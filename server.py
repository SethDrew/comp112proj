"""
Seth Drew and Jacob Apkon
server.py

Contains startup logic for a single proxy.
"""


import argparse
import socket
import asyncore
import logging
from proxy import (
    Proxy,
    Proxy_Client,
    CACHE,
    BLOOM_FILTERS,
    PROXY_SENTINEL,
    BLOOM_ADVERT,
)


HOST = 'localhost'
BUFF_SIZE = 4096
MAX_CONNECTIONS = 10

LOG_FILE = 'log_proxy'
logging.basicConfig(filename=LOG_FILE,
                    level=logging.DEBUG)


def narrow_class(sock):

    """ Read the first byte of the transmission to determine if it's a new
    proxy or if it's an HTTP client """

    # Block until we can read the first byte
    sock.setblocking(1)
    value = sock.recv(1)

    # All proxy communications start with this
    if not value == PROXY_SENTINEL:
        logging.debug("Web Client Request")
        Proxy(socket=sock, first_byte=value)
    else:
        logging.debug("Proxy Client Connection")
        Proxy_Client(sock=sock)


class Server(asyncore.dispatcher):

    """ Class that just accepts incoming transmissions, and moves them off of
    the master socket """

    def __init__(self, address):
        asyncore.dispatcher.__init__(self)
        self.host_with_port = address
        self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
        self.bind(address)
        self.address = self.socket.getsockname()
        self.listen(MAX_CONNECTIONS)

    def handle_accept(self):
        client = self.accept()
        logging.debug("Accepted Connection from %s", client[1])
        narrow_class(client[0])

    def handle_close(self):
        logging.debug("SERVER CLOSING")
        self.close()


def advertise_bloom():

    """ Send our bloom filter to all known peers """

    message = PROXY_SENTINEL + BLOOM_ADVERT + str(CACHE.get_bloom())
    for proxy, _ in BLOOM_FILTERS.iteritems():
        if not proxy.write_buffer:
            proxy.write_buffer = message


def start_server(port, proxies):

    logging.debug(proxies)
    address = (HOST, port)
    server = Server(address)

    for proxy in proxies:
        logging.debug("Initializing clients")
        Proxy_Client(sock=None, address=proxy)

    while True:
        asyncore.loop(timeout=10, count=1)


def parse_args():

    """ Parse command line arguments """

    def address(x):
        host, port = x.split(',')
        return host, int(port)

    parser = argparse.ArgumentParser()
    parser.add_argument('port',
                        help='Port number to run the server on',
                        type=int)
    parser.add_argument('proxies',
                        help='Other proxies to connect to',
                        type=address,
                        nargs='*')
    return parser.parse_args()


def main():
    args = parse_args()
    start_server(args.port, args.proxies)


if __name__ == "__main__":
    main()
