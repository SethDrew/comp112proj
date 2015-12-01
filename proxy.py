import socket
import asyncore
import logging
from datetime import datetime, timedelta


BUFF_SIZE = 4096

LOG_FILE = 'log_proxy'
logging.basicConfig(filename=LOG_FILE,
                    level=logging.DEBUG)


CACHE = {}

def update_cache(key, value):
    global CACHE

    current_time = datetime.utcnow()

    expiration = ' '.join([
        x.split()[1:] for x in value.splitlines() if x.startswith("Expires:")
    ][0])

    ttl = datetime.strptime(expiration, "%a, %d %b %Y %H:%M:%S GMT")
    logging.debug("PARSED TTL = %s", ttl)

    time_diff = current_time - ttl

    if time_diff.total_seconds():
        CACHE[key] = (ttl, CACHE.setdefault(key, (ttl, ""))[1] + str(value))


def get_cache():
    return CACHE


def search_cache(key):
    return CACHE.setdefault(key, "")


def clear_expired_entires():
    return


class Proxy(asyncore.dispatcher):

    def __init__(self, address, destination, request):
        asyncore.dispatcher.__init__(self)
        self.read_buffer = ""
        self.write_buffer = request

        logging.debug("Connecting to %s", destination)

        self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
        self.connect(destination)

    """
    MOVE THESE TO SERVER.PY
    def add_peer(self, hostname, port): # should do some sort of pinging here
        self.peers.append((hostname, port))

    def del_peer(self, hotname, port):
        self.peers = [
            (h, p) for (h, p) in self.peers if h != hostname and p != port
        ]
    """

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
