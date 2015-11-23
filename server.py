import argparse
import socket
import asyncore
import select
import sys
import ds
from proxy import Proxy


HOST = 'localhost'
BUFSIZE = 1024
MAX_CONNECTIONS = 5


class Server(asyncore.dispatcher):

    def __init__(self, address):
        asyncore.dispatcher.__init__(self)
        self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
        self.bind(address)
        self.address = self.socket.getsockname()
        self.listen(MAX_CONNECTIONS)

    def handle_accept(self):
        client = self.accept()
        proxy = Proxy(client[0])

    def handle_close(self):
        self.close() # TODO


def start_server(port):
    data = {}
    with open("serverdata.txt", "r") as f:
        data = eval(f.read())

    address = (HOST, port)
    server = Server(address)

    asyncore.loop()


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('port',
                        help='Port number to run the server on',
                        type=int)
    return parser.parse_args()


def main():
    args = parse_args()
    start_server(args.port)


if __name__ == "__main__":
    main()
