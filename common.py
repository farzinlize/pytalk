from socket import socket

NUM_SIZE = 4
ENCODING = 'utf8'
IS_TXT = b'\x00'
IS_FILE = b'\x01'

HELP_MSG = "Talky program is here to help you communicate fast inside network with all you devices\n" \
           "    list of commands:\n" \
           "    * `e` or `exit` to end communication\n" \
           "    * `sf` or `send file` to send a file providing a file name or address\n" \
           "    * `sx` or `send txt` to send any text\n" \
           "    * `r` or `receive` to wait for other end sending you something"

def bytes_to_int(b :bytes):return int.from_bytes(b, 'big', signed=False)
def int_to_bytes(i, int_size=NUM_SIZE, signed=False):return i.to_bytes(int_size, 'big', signed=False)

def read_protocol(other:socket):

    def read_file():
        name_size = bytes_to_int(other.recv(NUM_SIZE))
        name = str(other.recv(name_size), encoding=ENCODING)
        file_size = bytes_to_int(other.recv(NUM_SIZE))
        with open(name, 'wb') as other_file:
            while file_size:
                chunk = other.recv(file_size)
                other_file.write(chunk)
                file_size -= len(chunk)
        return f"(successfully received file `{name}`)"

    def read_txt():
        txt_size = bytes_to_int(other.recv(NUM_SIZE))
        return f"[message]: {str(other.recv(txt_size), encoding=ENCODING)}"
        
    operation = {IS_FILE:read_file, IS_TXT:read_txt}

    try:print(operation[other.recv(1)]())
    except Exception as err:print(f"[READ_ERR] {err}")


def send_protocol(other:socket, what, content):

    def send_file(name):
        other.send(int_to_bytes(len(name)))
        other.send(bytes(name, encoding=ENCODING))
        with open(name, 'rb') as other_file:data = other_file.read()
        other.send(int_to_bytes(len(data)))
        other.sendall(data)
        return f"(successfully sent file `{name}`)"

    def send_txt(message):
        other.send(int_to_bytes(len(message)))
        other.send(bytes(message, encoding=ENCODING))
        return "(message sent)"

    operation = {IS_FILE:send_file, IS_TXT:send_txt}

    other.send(what)
    try:print(operation[what](content))
    except Exception as err:print(f"[SEND_ERR] {err}")
