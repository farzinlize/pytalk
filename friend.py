import sys
from socket import socket
from common import IS_TXT, IS_FILE, HELP_MSG, read_protocol, send_protocol

talky = socket()
talky.connect((sys.argv[1], int(sys.argv[2])))

while True:
    command = input("[here] enter a command (h for help): ")
    if   command in ['h', 'help']:print(HELP_MSG)
    elif command in ['r', 'receive']:read_protocol(talky)
    elif command in ['sf', 'send file']:send_protocol(talky, IS_FILE, input("(file name or address?)"))
    elif command in ['sx', 'send txt']:send_protocol(talky, IS_TXT, input("(message?)"))
    elif command in ['e', 'exit']:break

print("communication's over see you next time")
