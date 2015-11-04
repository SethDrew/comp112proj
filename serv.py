import socket
import sys
import ds



if len(sys.argv) < 2:
	print "Usage: "+ sys.argv[0]+" port"
	sys.exit();

data = ds.Dict()
f = open("serverdata.txt", "r")
data.data = eval(f.read())
f.close()

PORT = int(sys.argv[1])
HOST = 'localhost'
BUFSIZE = 1024

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.bind((HOST, PORT))
sock.listen(5) # become a server socket, maximum 5 connections

while True:
    connection, address = sock.accept()
    buf = connection.recv(BUFSIZE)
    if len(buf) > 0:
        print buf

