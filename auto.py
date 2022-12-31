import sys
from socket import socket, AF_INET, SOCK_STREAM
from common import IS_FILE, read_protocol, send_protocol
from config import AUTO_PORT, translate

def sender_auto(me, send_to, filename):
    print(f'sending file on auto channel from {me} to {send_to}')
    other = socket()

    other.connect((send_to, AUTO_PORT))
    print(f"auto connection stablished on port:{AUTO_PORT}")
    
    send_protocol(other, IS_FILE, filename)

def receiver_auto(me, who='unkown'):
    print(f'I({me}) expecting a transfer from {who}')
    server = socket(AF_INET, SOCK_STREAM)
    server.bind(("0.0.0.0", AUTO_PORT))
    server.listen(1)

    print(f"auto connection waiting on port:{AUTO_PORT}")
    other, address = server.accept()
    print(f"auto connection stablished with address:{address}!")

    read_protocol(other)

if __name__ == '__main__':
    identify = sys.argv[1]
    if   sys.argv[2] in ['r', 'receive']:receiver_auto(identify)
    elif sys.argv[2] in ['s', 'sender'] :sender_auto(identify, sys.argv[3], sys.argv[4])