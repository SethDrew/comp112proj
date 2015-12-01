import argparse
import socket
import asyncore
import logging
from proxy import Proxy


HOST = 'localhost'
WEB_SERVER_PORT = 80
BUFF_SIZE = 4096
MAX_CONNECTIONS = 5

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
        Handler(self.host_with_port[1] + 1, socket=client[0])
        logging.debug("Accepted Connection from %s", client[1])

    def handle_close(self):
        self.close()


class Handler(asyncore.dispatcher):

    def __init__(self, proxy_port, socket):
        asyncore.dispatcher.__init__(self, sock=socket)
        self.proxy = None
        self.proxy_port = proxy_port

    def writable(self):
        return self.proxy and len(self.proxy.read_buffer)

    def handle_read(self):
        logging.debug("Reading from socket")
        request = self.recv(BUFF_SIZE)

        host = [
            x.split()[1] for x in request.splitlines() if x.startswith("Host:")
        ]

        if not host:
            self.proxy.write_buffer += request
            return

        self.proxy = Proxy((HOST, self.proxy_port), (host[0], WEB_SERVER_PORT), request)

    def handle_write(self):
        logging.debug("Writing to socket")
        if self.proxy:
            logging.debug(self.proxy.read_buffer)
            sent = self.send(self.proxy.read_buffer)
            self.proxy.read_buffer = self.proxy.read_buffer[sent:]

    def handle_close(self):
        while self.writable():
            self.handle_write()

        logging.debug("Connection closed")

        self.close()


def start_server(port):
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
