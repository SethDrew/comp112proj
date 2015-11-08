import argparse
import socket
import sys
import ds
from proxy import Proxy


HOST = 'localhost'
BUFSIZE = 1024
MAX_CONNECTIONS = 5


def accept_connections(socket, proxy):

    while True:
        connection, address = socket.accept()
        buf = connection.recv(BUFSIZE)

        # If it's an HTTP request, forward through the proxy
        # If it's a request to share chache do something else

        if buf:
            print buf


def start_server(port):
    data = ds.Dict()
    with open("serverdata.txt", "r") as f:
        data.data = eval(f.read())

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind((HOST, port))
    sock.listen(MAX_CONNECTIONS) # become a server socket

    proxy = Proxy("Server Name", port)

    accept_connections(sock, proxy)


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
