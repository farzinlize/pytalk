import sys
from socket import socket

NUM_SIZE = 4

def bytes_to_int(b :bytes):
    return int.from_bytes(b, 'big', signed=False)


def int_to_bytes(i, int_size=NUM_SIZE, signed=False):
    return i.to_bytes(int_size, 'big', signed=False)

talky = socket()
talky.connect((sys.argv[1], int(sys.argv[2])))

talky.send(int_to_bytes(2))
talky.send(b"hi")

i = bytes_to_int(talky.recv(4))
print(talky.recv(i))

