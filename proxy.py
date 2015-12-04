"""
Seth Drew and Jacob Apkon
File: proxy.py

Contains the proxy class and helpers. The proxy intercepts http requests and
checks to see if any proxies connected with it have the data cached. Otherwise,
it forwards the request to the destination and caches the response for later use.

Each proxy contains the bloom filters of all it's peers, and advertises its
filter periodically. In this way, it can quickly check if it can to ask a peer
for the data or if it has to forward the request to the server.

Classes that overload asyncore.dispatcher override handle_ functions so that
requests and responses can be done asynchronously. This method is used instead
of select() calls.

"""

import socket
import asyncore
import logging
import pickle
from bloom import Counting_Bloom
from cache import Cache
from datetime import datetime


HOST = 'localhost'
WEB_SERVER_PORT = 80
BUFF_SIZE = 4096

BLOOM_FILTERS = {}
PROXY_SENTINEL = '@'
ERROR = '0'
BLOOM_ADVERT = '1'
CACHE_REQ = '2'
CACHE_RES = '3'

LOG_FILE = 'log_proxy'
logging.basicConfig(filename=LOG_FILE,
                    level=logging.DEBUG)

CACHE = Cache()

"""
Purpose: Forwards a request to the needed location on a cache miss
Constructor: Forwarding_Agent() takes no arguments
Public methods:
    handle_write() :::: Write to the destination
    handle_read()  :::: Reads response from destination
    handle_close() :::: Closes the connection
"""
class Forwarding_Agent(asyncore.dispatcher):

    def __init__(self, destination, request):
        asyncore.dispatcher.__init__(self)
        self.read_buffer = ""
        self.write_buffer = request

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
        while self.writable():
            self.handle_write()

        logging.debug("Proxy closing")
        self.close()


"""
Purpose: Main proxy class. Contains logic for parsing and responding to requests
on the socket.
Constructor: Proxy_Mixin is the intra-proxy requset request handler
Public methods:
    intra_proxy_write() :::: Write to other proxies.
    intra_proxy_read()  :::: Parse an incoming message from a proxy
    handle_read()       :::: Main reading from socket function. Parses request and
                             checks all bloom filters known by the proxy.

"""
class Proxy(asyncore.dispatcher):

    def __init__(self, socket, first_byte):
        asyncore.dispatcher.__init__(self, sock=socket)
        self.sock = socket
        self.forward = None
        self.intra_proxy = False

        self.write_client_buffer = ""
        self.read_client_buffer = first_byte

    def writable(self):
        return self.write_client_buffer or (self.forward and self.forward.read_buffer)

    def handle_read(self):
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
            logging.debug("GOT FROM CACHE")
            self.write_client_buffer += cache_contains
            return

        for (proxy, bloom_filter) in BLOOM_FILTERS.iteritems():
            logging.debug("Checking bloom filters for %s", self.host)
            if bloom_filter.query(self.host):
                logging.debug("A proxy had the request cached")
                logging.debug("bloom %s", bloom_filter.get_data())
                proxy.write_buffer += PROXY_SENTINEL + CACHE_REQ + self.host
                self.forward = proxy
                return

        # None of the proxies have the host cached
        self.forward = Forwarding_Agent((host[0], WEB_SERVER_PORT),
                                        self.read_client_buffer)
        self.read_client_buffer = ""

    def handle_write(self):
        #logging.debug("Writing to socket")
        if self.write_client_buffer:
            sent = self.send(self.write_client_buffer)
            self.write_client_buffer = self.write_client_buffer[sent:]
        if self.forward and self.forward.read_buffer:
            sent = self.send(self.forward.read_buffer)
            # TODO: Only cache if forwarding_agent
            CACHE.update_cache(self.host, self.forward.read_buffer[:sent])
            self.forward.read_buffer = self.forward.read_buffer[sent:]

    """closing the proxy"""
    def handle_close(self):
        while self.writable():
            self.handle_write()
        self.close()


class Proxy_Client(asyncore.dispatcher):

    def __init__(self, sock=None, port=None):
        logging.debug("Sock %s, port %s", sock, port)
        asyncore.dispatcher.__init__(self, sock=sock)
        if not sock:
            self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
            self.port = port
            if self.port:
                self.connect(('localhost', port))

        self.write_buffer = PROXY_SENTINEL + BLOOM_ADVERT + CACHE.get_bloom()
        self.read_buffer = ""

        self.last_transmit = datetime.utcnow()

    def writable(self):
        return self.write_buffer

    def readable(self):
        now = datetime.utcnow()
        if (now - self.last_transmit).total_seconds() > 10:
            self.write_buffer += PROXY_SENTINEL + BLOOM_ADVERT + CACHE.get_bloom()
        self.last_transmit = now
        return True

    def handle_write(self):
        try:
            if self.write_buffer:
                sent = self.send(self.write_buffer)
                self.write_buffer = self.write_buffer[sent:]
        except Exception:
            self.close()

    def handle_read(self):
        try:
            message = self.recv(BUFF_SIZE)

            if not message[0] == PROXY_SENTINEL:
                return

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


class Bloom_Advert:
    def __init__(self, bit_vector):
        self.bit_vector = bit_vector


class Cache_Req:
    def __init__(self, http_request):
        self.request = http_request


class Cache_Res:
    def __init__(self, http_response):
        self.response = http_response
