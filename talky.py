from socket import socket, AF_INET, SOCK_STREAM
from common import HELP_MSG, IS_FILE, IS_TXT, communication_loop, read_protocol, send_protocol
import sys

server = socket(AF_INET, SOCK_STREAM)
server.bind(("0.0.0.0", int(sys.argv[1])))
server.listen(1)

print(f"I'm up! lets hear from anyone on port:{sys.argv[1]}")
friend, address = server.accept()
print(f"Friend just joined the Talky-Talky party on {address}!")

communication_loop(friend)