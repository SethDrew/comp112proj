""" 
Seth Drew and Jacob Apkon
File: server.py


Contains startup logic for a single proxy.
"""



import argparse
import socket
import asyncore
import logging
from proxy import Proxy, Proxy_Client


HOST = 'localhost'
BUFF_SIZE = 4096
MAX_CONNECTIONS = 5

LOG_FILE = 'log_proxy'
logging.basicConfig(filename=LOG_FILE,
                    level=logging.DEBUG)


"""
Purpose: ????
Constructor: Hostname/port tuple to run server on
Public methods:
    handle_accept() :::: Assigns a proxy to new incoming socket activity
    handle_close() :::: Closes a TCP connection

"""
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

""" 
Called when running "source start portno" to instantiate Server class and
create Proxy_Client for each network proxy supplied at startup.

"""
def start_server(port, proxies):
    address = (HOST, port)
    server = Server(address)

    for proxy in proxies:
        Proxy_Client(proxy)

    asyncore.loop()


""" command line arguments for proxies in the network we need to connect to """
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
