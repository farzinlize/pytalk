from socket import socket, AF_INET, SOCK_STREAM
import sys

NUM_SIZE = 4

def bytes_to_int(b :bytes):
    return int.from_bytes(b, 'big', signed=False)


def int_to_bytes(i, int_size=NUM_SIZE, signed=False):
    return i.to_bytes(int_size, 'big', signed=False)

server = socket(AF_INET, SOCK_STREAM)
server.bind(('127.0.0.1', int(sys.argv[1])))
server.listen(1)

print(f"I'm up! lets hear from anyone on port:{sys.argv[1]}")
friend, address = server.accept()
print("Talky-Talky started")

print("waiting for friend to talk first ...")
message_header = friend.recv(NUM_SIZE)
while message_header:
    print("[friend]: " ,friend.recv(bytes_to_int(message_header)) )
    prompt = input("do you wish to send something back?\n")
    if prompt.startswith('y'):
        back = input()
        friend.send(int_to_bytes(len(back)))
        friend.send(bytes(back, encoding='utf8'))

    print("waiting for friend to say anything ...")
    message_header = friend.recv(NUM_SIZE)

print("communication's over")
