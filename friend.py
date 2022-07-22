import sys
from socket import socket
from common import IS_TXT, IS_FILE, HELP_MSG, communication_loop, read_protocol, send_protocol

talky = socket()
talky.connect((sys.argv[1], int(sys.argv[2])))

communication_loop(talky)