from socket import socket, AF_INET, SOCK_STREAM
from common import communication_loop
import sys

server = socket(AF_INET, SOCK_STREAM)
server.bind(("0.0.0.0", int(sys.argv[1]))) # arbitrary port is expected
server.listen(1)

print(f"I'm up! lets hear from anyone on port:{sys.argv[1]}")
friend, address = server.accept()
print(f"Friend just joined the Talky-Talky party on {address}!")

communication_loop(friend)