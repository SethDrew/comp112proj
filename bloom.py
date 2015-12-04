"""
Seth Drew and Jacob Apkon
File: bloom.py

Resources used:
CODE SOURCE BASED ON:
https://gist.github.com/cwvh/1453729#file-countingbloom-py

http://www.eecs.harvard.edu/~michaelm/NEWWORK/postscripts/BloomFilterSurvey.pdf

Bloom filter applications:
    - How many hash functions to use.

        Assumptions:
            - around 30 items in each cache at a time
            - 1%-2% error rate is acceptable
        Calculations:
            k = ln(2) * (m/n) is the ideal number of hashes
                m --- bits in filter
                n --- number of things we need to store concurrently
                k --- number of hash functions we need
            (0.6185)^(m/n) is the error probability
                - given n = 30, we want m = 256 to garuntee 1/100 error rate

        Thus, we have k = 6 independent hash functions ideally.
"""


import hashlib # Contains md5(), sha1(), sha224(), sha256(), sha384(), and sha512()


m = 256
def hashfn(item):

    """ Returns a 256 bit vector containing result of 6 hashing functions """

    hashes = [hashlib.md5(), hashlib.sha224()]

    for h in hashes:
        h.update(item)

    """ Generating six hash indicies between 0 and 256 """
    hash_values = [
        (int(hashes[0].hexdigest(), 16)),
        (int(hashes[1].hexdigest(), 16))
    ]

    hashes[0].update(str(hash_values[0]))
    hashes[1].update(str(hash_values[1]))

    hash_values = hash_values + [
        (int(hashes[0].hexdigest(), 16)),
        (int(hashes[1].hexdigest(), 16))
    ]

    hashes[0].update(str(hash_values[2]))
    hashes[1].update(str(hash_values[3]))

    hash_values = hash_values + [
        (int(hashes[0].hexdigest(), 16)),
        (int(hashes[1].hexdigest(), 16)),
    ]
    hashes[0].update(str(hash_values[4]))
    hash_values = hash_values + [
        (int(hashes[0].hexdigest(), 16))]



    return (
        (1 << hash_values[0] % m) |
        (1 << hash_values[1] % m) |
        (1 << hash_values[2] % m) |
        (1 << hash_values[3] % m) |
        (1 << hash_values[4] % m) |
        (1 << hash_values[5] % m) |
        (1 << hash_values[6] % m)

    )


def mask(val):
    """ Creates a mask for val """
    return bin(hashfn(val))[3:]


class Counting_Bloom(object):

    """ Provides methods for adding to, removing from, and querying a bloom
    filter """

    def __init__(self, items=None):
        if items:
            self.items = items

        else:
            self.items = [0] * m

    def add(self, item):
        bits = mask(item)
        for index, bit in enumerate(bits):
            if bit == '1':
                self.items[index] += 1
    def query(self, item):
        bits = mask(item)
        for index, bit in enumerate(bits):
            if bit == '1' and self.items[index] == 0:
                return False
        return True

    def remove(self, item):
        bits = mask(item)
        for index, bit in enumerate(bits):
            if bit == '1' and self.items[index]:
                self.items[index] -= 1
    def get_data(self):
        chars = [ str(x) for x in self.items ]
        return ' '.join(chars)
