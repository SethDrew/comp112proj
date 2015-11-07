from ds import TTLDict

class Proxy:
	peers = [] # array of [(hostname, port), (hostname, port)]

	def __init__(self, srvname, srvport):
		self.srvname = srvname
		self.srvport = srvport
		self.data = TTLDict()

	def add_peer(self, hostname, port): # should do some sort of pinging here
		peers.append((hostname,port))

	def del_peer(self, hotname, port):
		for i, (h, p) in enumerate(peers):
			if h == hostname and p == port:
				peers.remove(i)

	def ping_server(self):
		sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		tmp = sock.connect_ex((self.srvname, self.srvport))
		if tmp == 0:
			print "Connection available"
		else:
			print tmp

	def get(self, key):
		ret = self.data.get(key)
		if ret == None:
			print "Proxy does not contain key"
		else:
			# for proxy in the list, send a UDP question: do you contain something?
			print ret
			#step 1: ask peers
			#step 2: get the file from the server
			#do this asynchronously and provide the most recent?
