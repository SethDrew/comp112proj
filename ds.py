import time

class TTLDict:
	def __init__(self, TTL = 10):
		self.TTL = TTL
		self.data = {}
	def _clean(self):
		self.data = {key: (TTL, value) for (key, (TTL, value)) in self.data.iteritems() if TTL > time.time()}
	def add(self, key, value):
		self.data[key] = (time.time()+self.TTL, value)
	def get(self, key):
		if self.data.has_key(key) and self.data[key][0] > time.time():
			return self.data[key][1]
		self._clean()
		return None
	# removes dead keys 
	