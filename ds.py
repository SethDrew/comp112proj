import time
import socket


class TTLDict:

    """ Like a normal dictionary, but keeps TTL with value """

    def __init__(self, TTL=10):
		self.TTL = TTL
		self.data = {}

    def add(self, key, value):
		self.data[key] = (time.time() + self.TTL, value)

    def get(self, key):
        self._clean()

        return self.data.get(key, default=(None, None))[1]

    def _clean(self):

        """ Remove expired dictionary entries """

        data = {}
        for (key, (TTL, value)) in self.data.iteritems():
            if TTL > time.time():
                data[key] = (TTL, value)
        self.data = data


class Dict: # dictionary wrapper class for consistency.
    def __init__(self):
        self.data = {}

    def add(self, key, value):
        self.data[key] = value

    def get(self, key):
        return self.data.get(key)
