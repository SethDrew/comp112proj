"""
Seth Drew and Jacob Apkon
File: cache.py

This file contains:
    Cache class
        - Used by proxy to store cached web results
    TTLDict class
        - Wrapper for a python dictionary that implements time to live expiry of entires


"""


from datetime import datetime, timedelta
from bloom import Counting_Bloom
import logging


LOG_FILE = 'log_proxy'
logging.basicConfig(filename=LOG_FILE,
                    level=logging.DEBUG)


"""
Purpose: Wrapper for a python dictionary implementing time to live expiry for entires
Constructor: TTLDict() takes no arguments. Uses a default TTL value of 300 seconds
Public methods:
    add(key, val, TTL(optional)) :::: Same as dict, optional TTL third argument
    contains(key)                :::: Same as python dictionary
    remove(key)                  :::: Same as python dictionary
Private methods:
    _clean()                     :::: removes all expired entires
"""
class TTLDict:
    def __init__(self):
        self.data = {}
        self.bloom = Counting_Bloom()

    def contains(self, key):
        return key in self.data

    def add(self, key, value, TTL=timedelta(0, 300)):
        expire = datetime.utcnow() + TTL
        if key not in self.data:
            self.bloom.add(key)
        self.data[key] = (expire, value)

    def get(self, key):
        self._clean()
        return self.data.get(key, (None, ""))[1]

    def _clean(self):
        for (key, (TTL, value)) in self.data.iteritems():
            if TTL < datetime.utcnow():
                self.data.pop(key, None)
                self.bloom.remove(key)


"""
Purpose: Wrapper for a python dictionary implementing time to live expiry for entires
Constructor: Cache() takes no arguments.
Public methods:
    get_cache()              :::: Returns whole TTL dictionary
    search_cache(key)        :::: Gets a key from the cache, if avaliable
    update_cache(key, value) :::: Add a key/value pair to the cache
"""
class Cache(TTLDict):

    def get_cache(self):
        return self.data

    def search_cache(self, key):
        return self.get(key)

    def update_cache(self, key, value):
        try:
            """ Parse page (value) for TTL to use. Otherwise use TTL default"""
            current_time = datetime.utcnow()

            expiration = ' '.join([
                x.split()[1:] for x in value.splitlines() if x.startswith("Expires:")
            ][0])

            ttl = datetime.strptime(expiration, "%a, %d %b %Y %H:%M:%S GMT")
            logging.debug("PARSED TTL = %s", ttl)

            time_diff = ttl - current_time

            if time_diff.total_seconds() > 0:
                # Web Server gave us an expiration date
                self.add(key, str(value), time_diff)
            else:
                # Choose to devault to 10 seconds
                self.add(key, str(value))
        except Exception:
            # Choose to default to 10 seconds
            self.add(key, str(value))

    def get_bloom(self):
        return self.bloom.get_data()
