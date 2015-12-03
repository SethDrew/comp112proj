""" CODE SOURCE:
https://gist.github.com/cwvh/1453729#file-countingbloom-py
"""

"""
Bloom filter applications paper:
    http://www.eecs.harvard.edu/~michaelm/NEWWORK/postscripts/BloomFilterSurvey.pdf
    - Choosing how many hash functions we need:
        k = ln(2) * (m/n) is the ideal number of hashes
            m --- bits in filter
            n --- number of things we need to store concurrently
            k --- number of hash functions we need
        (0.6185)^(m/n) is the error probability
            - given n = 30 about, we want m = 256 to garuntee 1/100 error rate

        Thus, we have k = 6 ideally.
"""

"""
Filter theory and use:
    - 4 bits per counter (not acheivable with python w/o wizardry? TODO?)
    - compressing bit vectors? BLoom filters are random and thus not compressable
    - Each proxy keeps a list of other proxies

"""

import hashlib # Contains md5(), sha1(), sha224(), sha256(), sha384(), and sha512()

m = 256

def hashfn(item): # some hashes end up being very similar across different words here.
    hashes = [hashlib.md5(), hashlib.sha224()]

    for h in hashes:
        h.update(item)

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
        (int(hashes[1].hexdigest(), 16))
    ]
    return (
        (1 << hash_values[0] % m) |
        (1 << hash_values[1] % m) |
        (1 << hash_values[2] % m) |
        (1 << hash_values[3] % m) |
        (1 << hash_values[4] % m) |
        (1 << hash_values[5] % m)
    )

def mask(val):
    return bin(hashfn(val))[2:]

class CountingBloom(object):
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
        return self.items


"""
TESTING FOR THE FILTER
"""
"""
bloom = CountingBloom()
args = ('fofdsao', 'bafdsar', 'bfdsafdsaafsdaz', "asdf", "vcxjznlk", "sxiuzbnjkq", "voczuyhjwq", "qo8uwehrjnm")
for arg in args:
    bloom.add(arg)
    print ', '.join(str(bloom.query(arg)) for arg in args)
for arg in args:
    bloom.remove(arg)
    print ', '.join(str(bloom.query(arg)) for arg in args)

"""
