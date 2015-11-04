import socket
import sys

if len(sys.argv) < 2:
	print "Usage: "+ sys.argv[0]+" port"
	sys.exit();

PORT = int(sys.argv[1])
HOST = 'localhost'

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.connect((HOST, PORT))

msg = "hello"

sock.send(msg)



