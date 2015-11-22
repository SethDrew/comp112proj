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
        self.proxy = Proxy()

    def handle_accept(self):
        client = self.accept()
        self.proxy.forward(client)

    def handle_close(self):



def accept_connections(socket, proxy):

    while True:
        connection, address = socket.accept()
        # Loop the recv
        buf = connection.recv(BUFSIZE)

        # If it's an HTTP request, forward through the proxy
        # If it's a request to share chache do something else

        if buf:
            connection.send(str(proxy.forward(buf)))
        connection.close()


def start_server(port):
    data = {}
    with open("serverdata.txt", "r") as f:
        data = eval(f.read())

    address = (HOST, port)
    server = Server(address)

    asyncore.loop()

    #main_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    #main_socket.bind((HOST, port))
    #main_socket.listen(MAX_CONNECTIONS) # become a server socket

    #print "Proxy running on Port", port

    #proxy = Proxy()

    #accept_connections(sock, proxy)


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
