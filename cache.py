from ds import TTLDict
from datetime import datetime, timedelta
import logging


LOG_FILE = 'log_proxy'
logging.basicConfig(filename=LOG_FILE,
                    level=logging.DEBUG)


CACHE = TTLDict()


def get_cache():
    return CACHE


def search_cache(key):
    return CACHE.get(key)


def update_cache(key, value):
    global CACHE

    print "PROXY:: got value"
    print value
    try:
        current_time = datetime.utcnow()

        expiration = ' '.join([
            x.split()[1:] for x in value.splitlines() if x.startswith("Expires:")][0])

        ttl = datetime.strptime(expiration, "%a, %d %b %Y %H:%M:%S GMT")
        logging.debug("PARSED TTL = %s", ttl)

        time_diff = ttl - current_time

        if time_diff.total_seconds() > 0:
            # Web Server gave us an expiration date
            CACHE.add(key, value, time_diff.total_seconds)
        else:
            # Choose to devault to 10 seconds
            CACHE.add(key, value)
    except IndexError:
        # Choose to default to 10 seconds
        CACHE.add(key, value)
