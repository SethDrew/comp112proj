import socket
import asyncore
import logging


BUFF_SIZE = 4096

LOG_FILE = 'log_proxy'
logging.basicConfig(filename=LOG_FILE,
                    level=logging.DEBUG)


class Proxy(asyncore.dispatcher):

    def __init__(self, address, destination, request):
        asyncore.dispatcher.__init__(self)
        self.read_buffer = ""
        self.write_buffer = request

        logging.debug("Connecting to %s", destination)

        self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
        self.connect(destination)

    def add_peer(self, hostname, port): # should do some sort of pinging here
        self.peers.append((hostname, port))

    def del_peer(self, hotname, port):
        self.peers = [
            (h, p) for (h, p) in self.peers if h != hostname and p != port
        ]

    def handle_write(self):
        logging.debug(self.write_buffer)
        sent = self.send(self.write_buffer)
        self.write_buffer = self.write_buffer[sent:]
        logging.debug("Length after write: %s", len(self.write_buffer))

    def writable(self):
        logging.debug("Length? %s", len(self.write_buffer))
        return len(self.write_buffer)

    def handle_read(self):
        self.read_buffer += self.recv(BUFF_SIZE)

    def handle_close(self):
        while self.writable():
            self.handle_write()

        logging.debug("Proxy closing")
        self.close()
