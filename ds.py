import time
import socket


class TTLDict:

    """ Like a normal dictionary, but keeps TTL with value """

    def __init__(self):
        self.data = {}

    def contains(self, key):
        return key in self.data

    def add(self, key, value, TTL=10):
        self.data[key] = (time.time()+TTL, self.data.setdefault(key, (time.time()+TTL, ""))[1] + str(value))
    def get(self, key):
        self._clean()
        return self.data.get(key, (None, None))[1]

    def _clean(self):

        """ Remove expired dictionary entries """

        data = {}
        for (key, (TTL, value)) in self.data.iteritems():
            if TTL > time.time():
                data[key] = (TTL, value)
        self.data = data


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
            return {
                'type': 2,
                'data': 3
            }
