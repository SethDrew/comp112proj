from ds import TTLDict
import socket


WEB_SERVER_PORT = 80


class Proxy:
    peers = [] # array of [(hostname, port), (hostname, port)]

    def __init__(self):
        self.data = TTLDict()

    def add_peer(self, hostname, port): # should do some sort of pinging here
        peers.append((hostname,port))

    def del_peer(self, hotname, port):
        for i, (h, p) in enumerate(peers):
            if h == hostname and p == port:
                peers.remove(i)


    """ Currently this function is broken, don't use it. """
    def get(self, key): 
        ret = self.data.get(key)
        if ret == None:
            print "Proxy does not contain key"
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) 
            for (hostname, port) in peers:
                print "Sending UDP message for file " + key+" to "+ " Proxy Peer: "+hostname ":"+ port
                sock.sendto(MessageBuilder.(ProxyPeerReq(key)), (hostname, port))
            ret, address = sock.recvfrom(4096)
            print "PROXY:: got from peer: " + ret 
            if ret:
                return ret
        return ret

            # for proxy in the list, send a UDP question: do you contain something?
            # implement multicasting
            #step 1: ask peers
            #step 2: get the file from the server
            #do this asynchronously and provide the most recent?

    def forward(self, msg):
        key = msg.split("\n")[0].split(" ")[1]
        if self.data.get(key) != None:
            return "PROXY:: found data:" + self.data.get(key)
            
        host = [x.split()[1] for x in msg.splitlines() if x.startswith("Host:")][0]
        forward_socket = socket.create_connection((host, WEB_SERVER_PORT))
        forward_socket.send(msg)
        self.data.add(key, forward_socket.recv(1024))
        return "FORWARDED THROUGH PROXY:\n" + self.data.get(key)
