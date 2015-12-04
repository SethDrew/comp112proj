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
        sent = self.send(self.write_buffer)
        self.write_buffer = self.write_buffer[sent:]

    def writable(self):
        return len(self.write_buffer)

    def handle_read(self):
        self.read_buffer += self.recv(BUFF_SIZE)

    def handle_close(self):
        while self.writable():
            self.handle_write()

        logging.debug("Proxy closing")
        self.close()


"""
Purpose: Helper for the main proxy. Handles messages sent between proxy peers
Constructor: Proxy_Mixin() takes no arguments
Public methods:
    intra_proxy_write() :::: Write to other proxies.
    intra_proxy_read()  :::: Parse an incoming message from a proxy
                              Bloom filter: update records or add new filter to records
                              Data: give client the data from peer cache

"""
class Proxy_Mixin:

    def __init__(self):
        pass

    def intra_proxy_write(self):
        if self.write_buffer:
            #logging.debug("Writing %s", self.write_buffer)
            sent = self.send(self.write_buffer)
            self.write_buffer = self.write_buffer[sent:]

    def intra_proxy_read(self, message):
        if not message or message[0] != PROXY_SENTINEL:
            self.reading = False
            return

        global BLOOM_FILTERS
        self.intra_proxy = True

        message_type = message[2:]
        #logging.debug("Received message from proxy: %s", message_type)
        if message[1] == BLOOM_ADVERT:
            # Add our object (representing another proxy) to the BLOOM_FILTERS
            logging.debug("Updating the bloom filter")
            BLOOM_FILTERS[self] = Counting_Bloom(items=list(message_type))
        elif message[1] == CACHE_REQ:
            response_message = CACHE.get(message_type.request)
            if not response:
                response_message = ERROR
            response = Cache_Res(response_message)
            self.write_buffer = PROXY_SENTINEL + CACHE_RES + pickle.dumps(response)
        elif message[1] == CACHE_RES:
            # We got a response from a server's cache
            # TODO: what if the response comes in two different packets?
            if message_type.response == ERROR:
                # Spawn a Forwarding_Agent
                return
            else:
                self.read_buffer = message_type.response
                self.reading = True


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
class Proxy(asyncore.dispatcher, Proxy_Mixin):

    def __init__(self, socket):
        asyncore.dispatcher.__init__(self, sock=socket)
        self.sock = socket
        self.forward = None
        self.intra_proxy = False
        self.write_buffer = ""
        self.read_buffer = ""
        self.last_broadcast = datetime.utcnow()

    def writable(self):
        if self.intra_proxy:
            return self.write_buffer and len(self.write_buffer)
        else:
            return self.forward and len(self.forward.read_buffer)

    """
        This function contains the main
    """
    def handle_read(self):
        request = self.recv(BUFF_SIZE)
        if not request:
            return

        if self.intra_proxy:
            self.write_buffer += request
        elif request[0] != PROXY_SENTINEL:
            self.intra_proxy = False

            host = [
                x.split()[1] for x in request.splitlines() if x.startswith("Host:")
            ]

            if not host:
                self.forward.write_buffer += request
                return

            self.host = host[0]

            # TODO: hash host self.host and for each proxy key in BLOOM_FILTERS,
            # check against it's bloom filter value.
            # If it exists, use that proxy to get the data

            # TODO: Seth, is this what I'm supposed to do?

            for (proxy, bloom_filter) in BLOOM_FILTERS.iteritems():
                logging.debug("Checking bloom filters")
                if bloom_filter.query(self.host):
                    logging.debug("A proxy had the request cached")
                    proxy.write_buffer = PROXY_SENTINEL + CACHE_REQ + self.host
                    self.forward = proxy
                    return

            # None of the proxies have the host cached
            self.forward = Forwarding_Agent((host[0], WEB_SERVER_PORT),
                                            request)
        else:
            self.intra_proxy = True
            self.intra_proxy_read(request)

    """
    (1) Responding to the client with the data requested. The proxy's cache gets
    updated if the data came from the internet and not a peer.

    (2) Writes buffered data to a peer
    """
    def handle_write(self):
        logging.debug("Writing to socket")

        if not self.intra_proxy and self.forward:
            sent = self.send(self.forward.read_buffer)
            CACHE.update_cache(self.host, self.forward.read_buffer[:sent])
            logging.debug("Updated Bloom Filter: %s", CACHE.get_bloom())
            self.forward.read_buffer = self.forward.read_buffer[sent:]

        elif self.intra_proxy:
            logging.debug("From %s: %s", self.sock, self.write_buffer)
            self.intra_proxy_write()

    """closing the proxy"""
    def handle_close(self):
        while self.writable():
            self.handle_write()

        if not self.intra_proxy:
            logging.debug("FINAL CACHE %s", CACHE.get_cache())
            self.close()

"""
Purpose:???
Constructor:
Public methods:
            Wrappers for asyncore methods
"""
class Proxy_Client(asyncore.dispatcher, Proxy_Mixin):

    def __init__(self, port, source):
        asyncore.dispatcher.__init__(self)
        self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
        self.port = port
        self.source = source
        self.connect(('localhost', port))

        logging.debug("Sending initial bloom")
        self.write_buffer = PROXY_SENTINEL + BLOOM_ADVERT + str(CACHE.get_bloom())

    def writable(self):
        logging.debug("From %s To %s: %s", self.source, self.port, self.write_buffer)
        return self.write_buffer

    def handle_write(self):
        self.intra_proxy_write()

    def handle_read(self):
        request = self.recv(BUFF_SIZE)

        self.intra_proxy_read(request)

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
