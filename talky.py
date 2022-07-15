from socket import socket, AF_INET, SOCK_STREAM
from common import HELP_MSG, IS_FILE, IS_TXT, read_protocol, send_protocol
import sys

server = socket(AF_INET, SOCK_STREAM)
server.bind(("0.0.0.0", int(sys.argv[1])))
server.listen(1)

print(f"I'm up! lets hear from anyone on port:{sys.argv[1]}")
friend, address = server.accept()
print(f"Friend just joined the Talky-Talky party on {address}!")

while True:
    command = input("[here] enter a command (h for help): ")
    if   command in ['h', 'help']:print(HELP_MSG)
    elif command in ['r', 'receive']:read_protocol(friend)
    elif command in ['sf', 'send file']:send_protocol(friend, IS_FILE, input("(file name or address?)"))
    elif command in ['sx', 'send txt']:send_protocol(friend, IS_TXT, input("(message?)"))
    elif command in ['e', 'exit']:break

print("communication's over see you next time")
