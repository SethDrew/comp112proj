import argparse
import socket
import sys


HOST = 'localhost'


def start_client(port):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((HOST, port))

    msg = "hello"
    sock.send(msg)


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('port',
                        help='Port number to run the server on',
                        type=int)
    return parser.parse_args()


def main():
    args = parse_args()
    start_client(args.port)


if __name__ == "__main__":
    main()

