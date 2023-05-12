import signal
from socket import socket, AF_INET, SOCK_DGRAM
from subprocess import Popen, PIPE
from time import time as currentTime
from time import strftime, gmtime
import os

CHUNK_SIZE = 500_000 # in bytes (500KB)
UDP_CHUNK_SIZE = 10000
MAXIMUM_SIZE_WAITLIST = 10000

BLACK = "█"
WHITE = "░"
PROGRESS_BAR_LEN = 25

NUM_SIZE = 4
ENCODING = 'utf8'
IS_TXT = b'\x00'
IS_FILE = b'\x01'
IS_DIR = b'\x02'
SC_TXT = b'\x03'
SC_FILE = b'\x04'

RUN_C_PARTNER = "csecure"
CPC_KEYGEN = b"G"
CPC_SETKEY = b"S"
CPC_ENCRYPT = b"C"
CPC_DECRYPT = b"D"
CPR_OK = b"O"
CPR_REDO = b"R"
CPR_ER = b"E"

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
    if   b < 1000            :return f"{round(b,              2)}B"
    elif b < 1000_000        :return f"{round(b/1000,         2)}KB"
    elif b < 1000_000_000    :return f"{round(b/1000_000,     2)}MB"
    elif b < 1000_000_000_000:return f"{round(b/1000_000_000, 2)}GB"


class ProgressBar:
    def __init__(self, total_size, initial=0) -> None:
        self.size = total_size
        self.now = initial
        self.speed = 0
        self.line_check()

    def line_check(self):
        terminal = os.get_terminal_size()[0]
        if terminal >= 49:
            self.text = "[transmission: %s | %s | speed: %s/s]" # 31 character + 16 + X = terminal
            self.bar_len = terminal - 48
        else:
            self.text = "[t:%s|%s|s:%s/s]" # 10 character + 16 + X = terminal
            self.bar_len = terminal - 27


    def forward(self, how_many_byte, how_much_time):
        self.now += how_many_byte
        if self.now > self.size:self.now = self.size
        self.speed = how_many_byte / how_much_time

    def bar(self) -> str:
        B = self.bar_len * self.now // self.size
        return BLACK * B + WHITE * (self.bar_len - B)
    
    def __str__(self) -> str:
        s  = self.text%(tell_size(self.now), self.bar(), tell_size(self.speed))
        s += " " * (os.get_terminal_size()[0] - len(s) - 1)
        return s
    

def string_to_bytearray(arg:str) -> bytes:
    return int_to_bytes(len(arg)) + bytes(arg, encoding=ENCODING)


class CPartner:
    def __init__(self) -> None:
        self.process = Popen(RUN_C_PARTNER, stdin=PIPE, stdout=PIPE)
    
    def keygen(self, passphrase:str):
        self.process.stdin.write(CPC_KEYGEN+string_to_bytearray(passphrase))
        respond = self.process.stdout.read(1)
        if respond == CPR_REDO:print("WARNING - replacing older keys")
        key_len = bytes_to_int(self.process.stdout.read(NUM_SIZE))
        return self.process.stdout.read(key_len)
    
    def setkey(self, keydata:bytes, passphrase):
        self.process.stdin.write(CPC_SETKEY+string_to_bytearray(passphrase)+\
                                 int_to_bytes(len(keydata))+keydata)
        respond = self.process.stdout.read(1)
        if respond == CPR_REDO:print("WARNING - replacing public key")

    def encrypt(self, data:bytes):
        self.process.stdin.write(CPC_ENCRYPT+int_to_bytes(len(data))+data)
        respond = self.process.stdout.read(1)
        if respond == CPR_ER:print("ERROR - maybe no public key is set?");return
        encrypted_len = bytes_to_int(self.process.stdout.read(NUM_SIZE))
        return self.process.stdout.read(encrypted_len)
    
    def decrypt(self, data:bytes):
        self.process.stdin.write(CPC_DECRYPT+int_to_bytes(len(data))+data)
        respond = self.process.stdout.read(1)
        if respond == CPR_ER:print("ERROR - maybe no key is generated?");return
        decrypted_len = bytes_to_int(self.process.stdout.read(NUM_SIZE))
        return self.process.stdout.read(decrypted_len)


class ByteInterface:
    def __init__(self, security:CPartner=None) -> None:
        if security:
            self.security = security
            self.secure = True
        else:
            self.secure = False
    
    def secure_it(self, security):
        self.security = security
        self.secure = True

    def sending_string(self, data):
        if self.secure:return self.security.encrypt(bytes(data, encoding=ENCODING))
        return bytes(data, encoding=ENCODING)

    def sending_bytes(self, data):
        if self.secure:return self.security.encrypt(data)
        return data
    
    def received_string(self, data):
        if self.secure:return str(self.security.decrypt(data), encoding=ENCODING)
        return str(data, encoding=ENCODING)

    def received_bytes(self, data):
        if self.secure:return self.security.decrypt(data)
        return data


def read_protocol(other:socket, security:CPartner):

    def read_file():
        name_size = bytes_to_int(other.recv(NUM_SIZE))
        name = interface.received_string(other.recv(name_size))
        file_size = bytes_to_int(other.recv(NUM_SIZE))
        bar = ProgressBar(file_size)
        print(f"--> downloading file {name} (size: {tell_size(file_size)})")
        starting_time = currentTime()
        with open(name, 'wb') as other_file:
            remaining = file_size
            while remaining:
                chunk_time = currentTime()
                chunk = interface.received_bytes(other.recv(remaining))
                other_file.write(chunk)
                remaining -= len(chunk)
                bar.forward(len(chunk), currentTime()-chunk_time)
                print(bar, end='\r')

        print( f"\n---- download done "
               f"| speed: {tell_size(file_size/(currentTime()-starting_time))}/s")
        return f"(successfully received file `{name}`)"

    def read_directory():
        for i in range(bytes_to_int(other.recv(NUM_SIZE))):read_file()

    def read_txt():
        txt_size = bytes_to_int(other.recv(NUM_SIZE))
        return f"[message]: {interface.received_string(other.recv(txt_size))}"
        
    operation = {IS_FILE:read_file, IS_TXT:read_txt, IS_DIR:read_directory,
                 SC_FILE:read_file, SC_TXT:read_txt}

    interface = ByteInterface(security)
    first_byte = safe_start_read(other)
    if not first_byte:print("[NO_READ] ... back to console");return
    try:print(operation[first_byte]())
    except Exception as err:print("[READ_ERR]", {err})


def safe_start_read(connection:socket, many=1):
    try:
        signal.setitimer(signal.ITIMER_REAL, 1, 0)
        first_byte = connection.recv(many)
    except Exception as catch:
        if isinstance(catch, TimerException):print("[SAFE][TIMEOUT] nothing to read")
        else                                :print("[READ_ERR]", catch)
        return
    else:
        signal.setitimer(signal.ITIMER_REAL, 0, 0)
        return first_byte


def send_protocol(other:socket, what, content, security:CPartner=None):       

    def send_file(name):
        sending_name = interface.sending_string(name)
        other.sendall(int_to_bytes(len(sending_name)) + sending_name)
        
        # update: sending file loading bar
        with open(name, 'rb') as cargo:
            # determine length of file and tell other about it
            cargo_size = cargo.seek(0, 2)
            other.send(int_to_bytes(cargo_size)) 
            
            # start reading chunks and report progress
            print(f"<-- upstreaming file {name} (size: {tell_size(cargo_size)})")
            cargo.seek(0, 0)
            chunk = interface.sending_bytes(cargo.read(CHUNK_SIZE))
            bar = ProgressBar(cargo_size)
            starting_time = currentTime()
            while len(chunk) != 0:
                chunk_time = currentTime()
                other.sendall(chunk)
                bar.forward(CHUNK_SIZE, currentTime()-chunk_time)
                chunk = interface.sending_bytes(cargo.read(CHUNK_SIZE))
                print(bar, end='\r')

        print( f"\n---- upload done "
               f"| speed: {tell_size(cargo_size/(currentTime()-starting_time))}/s")
        return f"(successfully sent file `{name}`)"

    def send_directory(name):
        if not name:name = DEFAULT_DIRECTORY
        to_send = [f for f in os.listdir(name)]
        other.send(int_to_bytes(len(to_send)))
        for f in to_send:send_file(name + f)

    def send_txt(content):
        message = interface.sending_string(content)
        other.sendall(int_to_bytes(len(message)) + message)
        return "(message sent)"

    operation = {IS_FILE:send_file, IS_TXT:send_txt, IS_DIR:send_directory, 
                 SC_FILE:send_file, SC_TXT:send_txt}

    interface = ByteInterface(security)
    other.send(what)
    try:print(operation[what](content))
    except Exception as err:print(f"[SEND_ERR] {err}")

class TimerException(Exception):pass
def raise_function(input):raise TimerException(f"timer exception ({input})")

# # # # # # # # # # # UDP # # # # # # # # # # # 
#                                             #
#    handle file transfer using UDP socket    #
#                                             #
# # # # # # # # # # # UDP # # # # # # # # # # # 
def udp_sendfile(filename, main_channel:socket, udp_address:tuple[str, int]):

    def ack_flush():
        while True:
            signal.setitimer(signal.ITIMER_REAL, 0.5, 0)
            try:recived_ack = bytes_to_int(main_channel.recv(NUM_SIZE))
            except TimerException as _:return False
            signal.setitimer(signal.ITIMER_REAL, 0, 0)

            # report ending or remove waitlist item
            if recived_ack == chunk_count:return True

            # remove page from waitlist and calculate speed
            for w in waitlist:
                if w[0] == recived_ack:
                    bar.forward(UDP_CHUNK_SIZE, currentTime()-w[1])
                    waitlist.remove(w)
                    break
            else:print(f"[WARNING] didn't expect {recived_ack} chunk_id")

    def push_chunk(chunk_id, repeated=None):
        if not repeated:waitlist.append((chunk_id, currentTime())) # new entry
        else           :waitlist[i] = (chunk_id, currentTime())    # update time
        cargo.seek(chunk_id*UDP_CHUNK_SIZE, 0)
        udp_channel.sendto(int_to_bytes(chunk_id) + cargo.read(UDP_CHUNK_SIZE), udp_address)

    udp_channel = socket(AF_INET, SOCK_DGRAM)
    end = False

    with open(filename, 'rb') as cargo:
        
        starting_time = currentTime()
        cargo_size = cargo.seek(0, 2)
        bar = ProgressBar(cargo_size)
        chunk_count = (cargo_size+UDP_CHUNK_SIZE-1) // UDP_CHUNK_SIZE

        # send information through main channel
        main_channel.send(int_to_bytes(cargo_size))
        main_channel.send(int_to_bytes(len(filename)))
        main_channel.send(bytes(filename, encoding=ENCODING))
        main_channel.send(int_to_bytes(chunk_count))
        # # # # # # # # #

        waitlist = []
        lead_chunk = 0

        # while there is stll cargo
        while lead_chunk < chunk_count and not end:

            # just push cargo into channel
            if len(waitlist) < MAXIMUM_SIZE_WAITLIST/2:
                push_chunk(lead_chunk);lead_chunk+=1

            # push with ack-flush
            elif len(waitlist) < MAXIMUM_SIZE_WAITLIST:
                push_chunk(lead_chunk);lead_chunk+=1
                end = ack_flush()

            # repeat-all with ack-flush
            elif len(waitlist) == MAXIMUM_SIZE_WAITLIST:
                for i, stucked in enumerate(waitlist):push_chunk(stucked[0], repeated=i)
                end = ack_flush()

            print(bar, end='\r')

        # finishing cargo repeat waitlist until done 
        while len(waitlist) != 0 and not end:
            for i, stucked in enumerate(waitlist):push_chunk(stucked[0], repeated=i)
            end = ack_flush()
            print(bar, end='\r')

    print( f"\n---- upload done "
               f"| speed: {tell_size(cargo_size/(currentTime()-starting_time))}/s")


def udp_recivefile(main_channel:socket, port):

    # safe check from main channel
    # read 4 bytes for converting to number
    first_bytes = safe_start_read(main_channel, many=NUM_SIZE)
    if not first_bytes:print("[NO_READ] ... back to console");return

    starting_time = currentTime()

    udp_channel = socket(AF_INET, SOCK_DGRAM)
    udp_channel.bind(("0.0.0.0", port))

    # recive information through main channel
    cargo_size = bytes_to_int(first_bytes)
    filename_len = bytes_to_int(main_channel.recv(NUM_SIZE))
    filename = str(main_channel.recv(filename_len), encoding=ENCODING)
    chunk_count = bytes_to_int(main_channel.recv(NUM_SIZE))

    cargo = open(filename, 'wb')
    bar = ProgressBar(cargo_size)
    chunk_download = [False for _ in range(chunk_count)]
    recived_chunk_count = 0

    while recived_chunk_count < chunk_count:
        chunk_time = currentTime()
        data, _ = udp_channel.recvfrom(UDP_CHUNK_SIZE+NUM_SIZE)
        chunk_id = bytes_to_int(data[:NUM_SIZE])

        # check if not recived more than one time
        if not chunk_download[chunk_id]:
            main_channel.send(data[:NUM_SIZE])
            chunk_download[chunk_id] = True
            recived_chunk_count += 1            
            cargo.seek(chunk_id * UDP_CHUNK_SIZE, 0)
            cargo.write(data[NUM_SIZE:])
            bar.forward(len(data)-NUM_SIZE, currentTime() - chunk_time)

        print(bar, end='\r')
    
    print( f"\n---- download done "
               f"| speed: {tell_size(cargo_size/(currentTime()-starting_time))}/s")
    print(f"[UDP] all {chunk_count} chunks are downloaded")
    main_channel.send(int_to_bytes(chunk_count))
    udp_channel.close()
    cargo.close()

# # # # # # # # # # # END # # # # # # # # # # # 

def nothing():pass

def secure_channel(other:socket) -> CPartner:
    csecure = CPartner()
    public_key = csecure.keygen(input("secret passphrase: "))
    other.sendall(int_to_bytes(len(public_key)) + public_key)
    other_key_len = bytes_to_int(other.recv(NUM_SIZE))
    other_key = other.recv(other_key_len)
    csecure.setkey(other_key, input("other secret passphrase: "))
    return csecure


def communication_loop(other:socket):
    signal.signal(signal.SIGALRM, lambda signum,frame:raise_function((signum,frame)))
    security = None
    while True:
        command = input("[here] enter a command (h for help): ")
        if   command in ['h', 'help']:print(HELP_MSG)
        elif command in ['r', 'receive']:read_protocol(other, security)
        elif command in ['ru', 'recive udp']:udp_recivefile(other, int(input("(port?)")))
        elif command in ['su', 'send udp']:udp_sendfile(input("(file name?)"), other, (input("(ip?)"), int(input("(port?)"))))
        elif command in ['sf', 'send file']:send_protocol(other, IS_FILE, input("(file name or address?)"))
        elif command in ['sd', 'send directory']:send_protocol(other, IS_DIR, input("(enter directory? or press enter for default temp)"))
        elif command in ['sx', 'send txt']:send_protocol(other, IS_TXT, input("(message?)"))
        elif command in ['t', 'secure']:security = secure_channel(other)
        elif command in ['xx', 'secret txt']:send_protocol(other, SC_TXT, input("(secret message?)"), security)
        elif command in ['xf', 'secret file']:send_protocol(other, SC_FILE, input("(file name or address?)"), security)
        elif command in ['e', 'exit']:break
    print("communication's over see you next time")
    other.close()
