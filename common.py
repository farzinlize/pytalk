from socket import socket
from time import time as currentTime
from time import strftime, gmtime
import os

CHUNK_SIZE = 500_000 # in bytes (500KB)

BLACK = "█"
WHITE = "░"
PROGRESS_BAR_LEN = 25

NUM_SIZE = 4
ENCODING = 'utf8'
IS_TXT = b'\x00'
IS_FILE = b'\x01'
IS_DIR = b'\x02'

DEFAULT_DIRECTORY = 'temp/'

HELP_MSG = "Talky program is here to help you communicate fast inside network with all you devices\n" \
           "    list of commands:\n" \
           "    * `e` or `exit` to end communication\n" \
           "    * `sf` or `send file` to send a file providing a file name or address\n" \
           "    * `sx` or `send txt` to send any text\n" \
           "    * `r` or `receive` to wait for other end sending you something"

def bytes_to_int(b :bytes):return int.from_bytes(b, 'big', signed=False)
def int_to_bytes(i, int_size=NUM_SIZE, signed=False):return i.to_bytes(int_size, 'big', signed=False)

# turn bytes to human readable sizes (B,KB,MB,GB)
# maximum 8 character -> XXX.XX?B
def tell_size(b):
    if   b < 1000            :return f"{b}B"
    elif b < 1000_000        :return f"{round(b/1000, 2)}KB"
    elif b < 1000_000_000    :return f"{round(b/1000_000, 2)}MB"
    elif b < 1000_000_000_000:return f"{round(b/1000_000_000, 2)}GB"


class ProgressBar:
    def __init__(self, total_size, initial=0) -> None:
        self.size = total_size
        self.now = initial

        terminal = os.get_terminal_size()[0]
        if terminal >= 48:
            self.text = "[transmission: %s | %s | speed: %s/s]\r" # 31 character + 16 + X = terminal
            self.bar_len = terminal - 47
        else:
            self.text = "[t:%s|%s|s:%s/s]\r" # 10 character + 16 + X = terminal
            self.bar_len = terminal - 26
    
    def forward(self, how_many_byte, how_much_time):
        self.now += how_many_byte
        self.speed = how_many_byte / how_much_time

    def bar(self) -> str:
        B = self.bar_len * self.now // self.size
        return BLACK * B + WHITE * (self.bar_len - B)
    
    def __str__(self) -> str:
        return self.text%(tell_size(self.now), self.bar(), tell_size(self.speed))


def read_protocol(other:socket):

    def read_file():
        name_size = bytes_to_int(other.recv(NUM_SIZE))
        name = str(other.recv(name_size), encoding=ENCODING)
        file_size = bytes_to_int(other.recv(NUM_SIZE))
        bar = ProgressBar(file_size)
        print(f"--> downloading file {name} (size: {tell_size(file_size)})")
        starting_time = currentTime()
        with open(name, 'wb') as other_file:
            remaining = file_size
            while remaining:
                chunk_time = currentTime()
                chunk = other.recv(remaining)
                other_file.write(chunk)
                remaining -= len(chunk)
                bar.forward(len(chunk), currentTime()-chunk_time)
                print(bar)

        print( f"---- download done "
               f"| speed: {tell_size(file_size/(currentTime()-starting_time))}/s")
        return f"(successfully received file `{name}`)"

    def read_directory():
        for i in range(bytes_to_int(other.recv(NUM_SIZE))):read_file()

    def read_txt():
        txt_size = bytes_to_int(other.recv(NUM_SIZE))
        return f"[message]: {str(other.recv(txt_size), encoding=ENCODING)}"
        
    operation = {IS_FILE:read_file, IS_TXT:read_txt, IS_DIR:read_directory}

    try:print(operation[other.recv(1)]())
    except Exception as err:print(f"[READ_ERR] {err}")


def send_protocol(other:socket, what, content):

    def send_file(name):
        other.send(int_to_bytes(len(name)))
        other.send(bytes(name, encoding=ENCODING))
        
        # update: sending file loading bar
        with open(name, 'rb') as cargo:
            # determine length of file and tell other about it
            cargo_size = cargo.seek(0, 2)
            other.send(int_to_bytes(cargo_size)) 
            
            # start reading chunks and report progress
            print(f"<-- upstreaming file {name} (size: {tell_size(cargo_size)})")
            cargo.seek(0, 0)
            chunk = cargo.read(CHUNK_SIZE)
            bar = ProgressBar(cargo_size)
            starting_time = currentTime()
            while len(chunk) != 0:
                chunk_time = currentTime()
                other.sendall(chunk)
                bar.forward(len(chunk), currentTime()-chunk_time)
                chunk = cargo.read(CHUNK_SIZE)
                print(bar)

        print( f"---- upload done "
               f"| speed: {tell_size(cargo_size/(currentTime()-starting_time))}/s")
        return f"(successfully sent file `{name}`)"

    def send_directory(name):
        if not name:name = DEFAULT_DIRECTORY
        to_send = [f for f in os.listdir(name)]
        other.send(int_to_bytes(len(to_send)))
        for f in to_send:send_file(name + f)

    def send_txt(message):
        other.send(int_to_bytes(len(message)))
        other.send(bytes(message, encoding=ENCODING))
        return "(message sent)"

    operation = {IS_FILE:send_file, IS_TXT:send_txt, IS_DIR:send_directory}

    other.send(what)
    try:print(operation[what](content))
    except Exception as err:print(f"[SEND_ERR] {err}")


def communication_loop(other):
    while True:
        command = input("[here] enter a command (h for help): ")
        if   command in ['h', 'help']:print(HELP_MSG)
        elif command in ['r', 'receive']:read_protocol(other)
        elif command in ['sf', 'send file']:send_protocol(other, IS_FILE, input("(file name or address?)"))
        elif command in ['sd', 'send directory']:send_protocol(other, IS_DIR, input("(enter directory? or press enter for default temp)"))
        elif command in ['sx', 'send txt']:send_protocol(other, IS_TXT, input("(message?)"))
        elif command in ['e', 'exit']:break
    print("communication's over see you next time")
