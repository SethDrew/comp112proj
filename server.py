import argparse
import socket
import asyncore
import logging
import pickle
from proxy import Forwarding_Agent, update_cache, get_cache, search_cache, Bloom_Advert


HOST = 'localhost'
WEB_SERVER_PORT = 80
BUFF_SIZE = 4096
MAX_CONNECTIONS = 5

BLOOM_FILTERS = {}
PROXY_SENTINEL = '@'
ERROR = '0'
BLOOM_ADVERT = '1'
CACHE_REQ = '2'
CACHE_RES = '3'

LOG_FILE = 'log_proxy'
logging.basicConfig(filename=LOG_FILE,
                    level=logging.DEBUG)


class Server(asyncore.dispatcher):

    def __init__(self, address):
        asyncore.dispatcher.__init__(self)
        self.host_with_port = address
        self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
        self.bind(address)
        self.address = self.socket.getsockname()
        self.listen(MAX_CONNECTIONS)

    def handle_accept(self):
        client = self.accept()
        Proxy(self.host_with_port[1] + 1, socket=client[0])
        logging.debug("Accepted Connection from %s", client[1])

    def handle_close(self):
        self.close()


class Proxy(asyncore.dispatcher):

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

        if request[0] != PROXY_SENTINEL:
            self.intra_proxy = False

            host = [
                x.split()[1] for x in request.splitlines() if x.startswith("Host:")
            ]

            if not host:
                self.forward.write_buffer += request
                return

            self.host = host[0]
            self.forward = Forwarding_Agent((HOST, self.forward_port),
                                            (host[0], WEB_SERVER_PORT),
                                            request)
        elif request[0] == PROXY_SENTINEL:
            global BLOOM_FILTERS
            self.intra_proxy = True

            message = pickle.loads(request[2:])
            logging.debug("Received request from proxy: %s", request)
            if request[1] == BLOOM_ADVERT:
                # Add our object (representing another proxy) to the BLOOM_FILTERS
                BLOOM_FILTERS[self] = message.bit_vector
            elif request[1] == CACHE_REQ:
                return
            elif request[1] == CACHE_RES:
                # We got a response from a server's cache
                # TODO: Right now we assume the proxy had the thing i.e. check
                # for false positives
                self.write_buffer = message.response
        elif self.intra_proxy:
            self.write_buffer += request

    def handle_write(self):
        logging.debug("Writing to socket")

        if not self.intra_proxy and self.forward:
            logging.debug(self.forward.read_buffer)
            sent = self.send(self.forward.read_buffer)
            update_cache(self.host, self.forward.read_buffer[:sent])
            self.forward.read_buffer = self.forward.read_buffer[sent:]

        elif self.intra_proxy:
            if self.write_buffer:
                sent = self.send(self.write_buffer)
                self.write_buffer = self.write_buffer[sent:]

    def handle_close(self):
        while self.writable():
            self.handle_write()

        if not self.intra_proxy:
            logging.debug("FINAL CACHE %s", get_cache())
            self.close()


class Proxy_Client(asyncore.dispatcher):

    def __init__(self, port):
        asyncore.dispatcher.__init__(self)
        self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
        self.connect(('localhost', port))

        test = Bloom_Advert(bin(0))
        self.write_buffer = "@1" + pickle.dumps(test)

    def writable(self):
        return self.write_buffer

    def handle_write(self):
        if self.write_buffer:
            sent = self.send(self.write_buffer)
            self.write_buffer = self.write_buffer[sent:]

    def handle_read(self):
        logging.debug("Reading from socket")
        request = self.recv(BUFF_SIZE)

        elif request[0] == PROXY_SENTINEL:
            global BLOOM_FILTERS
            self.intra_proxy = True

            message = pickle.loads(request[2:])
            logging.debug("Received request from proxy: %s", request)
            if request[1] == BLOOM_ADVERT:
                # Add our object (representing another proxy) to the BLOOM_FILTERS
                BLOOM_FILTERS[self] = message.bit_vector
            elif request[1] == CACHE_REQ:
                return
            elif request[1] == CACHE_RES:
                # We got a response from a server's cache
                # TODO: Right now we assume the proxy had the thing i.e. check
                # for false positives
                self.write_buffer = message.response

    def handle_close(self):
        return


def start_server(port, proxies):
    address = (HOST, port)
    server = Server(address)

    for proxy in proxies:
        Proxy_Client(proxy)

    asyncore.loop()


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('port',
                        help='Port number to run the server on',
                        type=int)
    parser.add_argument('proxies',
                        help='Other proxies to connect to',
                        type=int,
                        nargs='*')
    return parser.parse_args()


def main():
    args = parse_args()
    start_server(args.port, args.proxies)


if __name__ == "__main__":
    main()
