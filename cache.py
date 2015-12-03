from datetime import datetime, timedelta
import logging


LOG_FILE = 'log_proxy'
logging.basicConfig(filename=LOG_FILE,
                    level=logging.DEBUG)


class TTLDict:

    """ Like a normal dictionary, but values have an expiration """

    def __init__(self):
        self.data = {}

    def contains(self, key):
        return key in self.data

    def add(self, key, value, TTL=timedelta(0, 10)):
        expire = datetime.utcnow() + TTL
        self.data[key] = (expire, self.data.setdefault(key, (None, ""))[1] + value)

    def get(self, key):
        self._clean()
        return self.data.get(key, (None, ""))[1]

    def _clean(self):

        """ Remove expired dictionary entries """

        data = {}
        for (key, (TTL, value)) in self.data.iteritems():
            if TTL > datetime.utcnow():
                data[key] = (TTL, value)
        self.data = data


class Cache(TTLDict):

    def get_cache(self):
        return self.data

    def search_cache(self, key):
        return self.get(key)

    def update_cache(self, key, value):
        try:
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
