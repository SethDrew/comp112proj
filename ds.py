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


class MessageBuilder:
    """
    message type:
        0: get broadcast
        1: not found response
        2: found key response
        3: ERROR
    """
    @staticmethod
    def ProxyPeerReq(key):
        return {
        'type': 0,
        'key' : key
        }
    def ProxyPeerResp(data):
        if data == None: 
            return {
                'type': 3
            }
        if data == "":
            return {
                'type': 1
            }
        else:
            return{
                'type': 2,
                'data': 3
            }
        



