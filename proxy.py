"""
Seth Drew and Jacob Apkon
proxy.py

Contains the Proxy class and helpers. The proxy intercepts http requests. If it
does not have the response for a given request, it checks to see if any proxies
connected with it have the data cached. If not, it forwards the request to the
destination and caches the response for later use.

Each proxy contains the bloom filters of all its peers, and advertises its
filter periodically. In this way, it can quickly check if it should ask a peer
for the data or if it has to forward the request to the server.

Classes that overload asyncore.dispatcher override functions so that requests
and responses can be done asynchronously. This is used instead of select() calls.
"""

import socket
import asyncore
import logging
from bloom import Counting_Bloom
from cache import Cache
from datetime import datetime


HOST = 'localhost'
WEB_SERVER_PORT = 80
BUFF_SIZE = 4096

BLOOM_FILTERS = {}
BLOOM_FILTER_FREQ = 10

PROXY_SENTINEL = '@'
ERROR = '0'
BLOOM_ADVERT = '1'
CACHE_REQ = '2'
CACHE_RES = '3'

LOG_FILE = 'log_proxy'
logging.basicConfig(filename=LOG_FILE,
                    level=logging.DEBUG)

# Cache for this entire server.py instance
CACHE = Cache()

class Forwarding_Agent(asyncore.dispatcher):

    """ Forwards an HTTP Request to the destination server on a cache miss.
    Puts the response in self.read_buffer """

    def __init__(self, destination, request):
        asyncore.dispatcher.__init__(self)
        self.read_buffer = ""
        self.write_buffer = request
        self.cachable = True

        logging.debug("Connecting to %s", destination)

        self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
        self.connect(destination)

    def handle_write(self):
        logging.debug("Forwarding Agent Writing")
        sent = self.send(self.write_buffer)
        self.write_buffer = self.write_buffer[sent:]

    def writable(self):
        return len(self.write_buffer)

    def handle_read(self):
        logging.debug("Forwarding Agent Reading")
        self.read_buffer += self.recv(BUFF_SIZE)

    def handle_close(self):

        """ Finish writing before closing """

        while self.writable():
            self.handle_write()

        logging.debug("Proxy closing")
        self.close()


class Proxy(asyncore.dispatcher):

    """ Proxy intercepts HTTP requests and determines if the response is
    already cached, a peer has it cached, or if the request needs to be
    forwarded to the server """

    def __init__(self, socket, first_byte):
        asyncore.dispatcher.__init__(self, sock=socket)
        self.sock = socket
        self.forward = None
        self.intra_proxy = False

        self.write_client_buffer = ""
        self.read_client_buffer = first_byte

    def writable(self):

        """ The proxy is writable if it has something in its write buffer or if
        the object it uses to forward the request has read something """

        return self.write_client_buffer or (self.forward and self.forward.read_buffer)

    def handle_read(self):

        """ Read from the socket, and parse the message for the host """

        self.read_client_buffer += self.recv(BUFF_SIZE)
        if not self.read_client_buffer:
            return

        request_lines = self.read_client_buffer.splitlines()
        host = [
            x.split()[1] for x in request_lines if x.startswith("Host:")
        ]

        if not host:
            self.forward.write_buffer += self.read_client_buffer
            return

        self.host = host[0]

        cache_contains = CACHE.search_cache(self.host)
        if cache_contains:
            logging.debug("Cache Hit")
            self.write_client_buffer += cache_contains
            return

        # Check all known bloom filters for a cache hit
        for (proxy, bloom_filter) in BLOOM_FILTERS.iteritems():
            if bloom_filter.query(self.host):
                logging.debug("A proxy had the request cached")
                proxy.write_buffer += PROXY_SENTINEL + CACHE_REQ + self.host
                self.forward = proxy
                return

        # None of the proxies have the host cached
        self.forward = Forwarding_Agent((host[0], WEB_SERVER_PORT),
                                        self.read_client_buffer)
        self.read_client_buffer = ""

    def handle_write(self):

        """ Write what's in the proxy's client buffer, and what's the
        forwarding object has read """

        if self.write_client_buffer:
            sent = self.send(self.write_client_buffer)
            self.write_client_buffer = self.write_client_buffer[sent:]
        if self.forward and self.forward.read_buffer:
            sent = self.send(self.forward.read_buffer)
            if self.forward.cachable:
                CACHE.update_cache(self.host, self.forward.read_buffer[:sent])
            self.forward.read_buffer = self.forward.read_buffer[sent:]

    def handle_close(self):

        """ Close the socket associated with this specific instance. This
        instance will no longer be usable """

        while self.writable():
            self.handle_write()
        self.close()


class Proxy_Client(asyncore.dispatcher):

    """ Each instance is associated with one active Proxy """

    def __init__(self, sock=None, address=None):
        logging.debug(address)
        asyncore.dispatcher.__init__(self, sock=sock)
        if not sock:
            self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
            self.address = address
            if self.address:
                self.connect(address)

        # Send an initial Bloom Filter
        self.write_buffer = PROXY_SENTINEL + BLOOM_ADVERT + CACHE.get_bloom()
        self.read_buffer = ""

        # We shouldn't cache data we get from other proxies
        self.cachable = False

        self.last_transmit = datetime.utcnow()

    def writable(self):

        """ Writabel if there is anything in the write buffer """

        return self.write_buffer

    def readable(self):

        """ Use readable to determine if we need to send a new Bloom Filter """

        now = datetime.utcnow()
        if (now - self.last_transmit).total_seconds() > BLOOM_FILTER_FREQ:
            self.write_buffer += PROXY_SENTINEL + BLOOM_ADVERT + CACHE.get_bloom()
        self.last_transmit = now
        return True

    def handle_write(self):

        """ Write to the socket, if anything goes wrong, assume the other proxy
        left and close the socket """

        try:
            if self.write_buffer:
                sent = self.send(self.write_buffer)
                self.write_buffer = self.write_buffer[sent:]
        except Exception:
            self.close()

    def handle_read(self):

        """ Read from the buffer, if anything goes wrong, assume the other
        proxy left and close the socket """

        try:
            message = self.recv(BUFF_SIZE)

            # Message not meant for the proxy, discard it
            if not message[0] == PROXY_SENTINEL:
                return

            # Parse the message to figure out which kind it was
            if message[1] == BLOOM_ADVERT:
                logging.debug("Received Bloom")
                new_bloom = [ int(x) for x in message[2:].split() ]
                logging.debug("New bloom: %s", new_bloom)
                BLOOM_FILTERS[self] = Counting_Bloom(items=new_bloom)
            elif message[1] == CACHE_REQ:
                logging.debug("Got Cache Request for %s", message)
                response = PROXY_SENTINEL + CACHE_RES
                cached = CACHE.get(message[2:])
                if not cached:
                    response += ERROR
                else:
                    response += cached
                self.write_buffer = response
            elif message[1] == CACHE_RES:
                logging.debug("Got Cache Response")
                self.read_buffer = message[2:]
        except Exception:
            self.close()

    def handle_close(self):
        return
