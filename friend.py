import sys
from socket import socket
from common import communication_loop

talky = socket()
talky.connect((sys.argv[1], int(sys.argv[2]))) # ip and port addresses are expected 

communication_loop(talky)