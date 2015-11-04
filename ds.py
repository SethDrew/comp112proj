import time
import socket


class TTLDict:
	def __init__(self, TTL = 10):
		self.TTL = TTL
		self.data = {}
	def add(self, key, value):
		self.data[key] = (time.time()+self.TTL, value)
	def get(self, key):
		if self.data.has_key(key) and self.data[key][0] > time.time():
			return self.data[key][1]
		self._clean()
		return None
	def _clean(self):	# removes dead keys 
		self.data = {key: (TTL, value) for (key, (TTL, value)) in self.data.iteritems() if TTL > time.time()}

class Dict: # dictionary wrapper class for consistency.
	def __init__(self):
		self.data = {}
	def add(self, key, value):
		self.data[key] = value
	def get(self, key):
		if self.data.has_key(key):
			return self.data[key]
		return None
	


class Proxy:
	peers = [] # array of [(hostname, port), (hostname, port)]
	def __init__(self, srvname, srvport):
		self.srvname = srvname
		self.srvport = srvport
		self.data = TTLDict()
	def addpeer(self, hostname, port): # should do some sort of pinging here
		peers.append((hostname,port))
	def delpeer(self, hotname, port):
		for i, (h, p) in enumerate(peers):
			if h == hostname and p == port:
				peers.remove(i)
	def pingserver(self):
		sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		sock.connect((self.srvname, self.srvport))
		sock.send("hello")


