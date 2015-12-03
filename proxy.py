import socket
import asyncore
import logging
import pickle
from bloom import hashfn
from cache import Cache


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


class Forwarding_Agent(asyncore.dispatcher):

    def __init__(self, address, destination, request):
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


class Proxy_Mixin:

    def __init__(self):
        pass

    def intra_proxy_write(self):
        if self.write_buffer:
            sent = self.send(self.write_buffer)
            self.write_buffer = self.write_buffer[sent:]

    def intra_proxy_read(self, message):
        if not message or message[0] != PROXY_SENTINEL:
            self.reading = False
            return

        global BLOOM_FILTERS
        self.intra_proxy = True

        message_type = pickle.loads(message[2:])
        logging.debug("Received message from proxy: %s", message)
        if message[1] == BLOOM_ADVERT:
            # Add our object (representing another proxy) to the BLOOM_FILTERS
            BLOOM_FILTERS[self] = message.bit_vector
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
                self.write_buffer = message_type.response
                self.reading = True


class Proxy(asyncore.dispatcher, Proxy_Mixin):

    def __init__(self, proxy_port, socket):
        asyncore.dispatcher.__init__(self, sock=socket)
        self.forward = None
        self.intra_proxy = False
        self.forward_port = proxy_port
        self.write_buffer = ""

    def writable(self):
        return self.forward and len(self.forward.read_buffer)

    def handle_read(self):
        logging.debug("Reading from socket")
        request = self.recv(BUFF_SIZE)
        if not request:
            return
        logging.debug(request)

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
            hashed = hashfn(self.host)

            for (proxy, bloom_filter) in BLOOM_FILTERS.iteritems():
                if bloom_filter.query(hashed):
                    # Do something with proxy
                    return

            # None of the proxies have the host cached
            self.forward = Forwarding_Agent((HOST, self.forward_port),
                                            (host[0], WEB_SERVER_PORT),
                                            request)
        else:
            self.intra_proxy_read(request)

    def handle_write(self):
        logging.debug("Writing to socket")

        if not self.intra_proxy and self.forward:
            logging.debug(self.forward.read_buffer)
            sent = self.send(self.forward.read_buffer)
            CACHE.update_cache(self.host, self.forward.read_buffer[:sent])
            self.forward.read_buffer = self.forward.read_buffer[sent:]

        elif self.intra_proxy:
            self.intra_proxy_write()

    def handle_close(self):
        while self.writable():
            self.handle_write()

        if not self.intra_proxy:
            logging.debug("FINAL CACHE %s", CACHE.get_cache())
            self.close()


class Proxy_Client(asyncore.dispatcher, Proxy_Mixin):

    def __init__(self, port):
        asyncore.dispatcher.__init__(self)
        self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
        self.connect(('localhost', port))

        bloom = Bloom_Advert(bin(0))
        self.write_buffer = PROXY_SENTINEL + BLOOM_ADVERT + pickle.dumps(bloom)

    def writable(self):
        return self.write_buffer

    def handle_write(self):
        self.intra_proxy_write()

    def handle_read(self):
        logging.debug("Reading from socket")
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
