import socket
import threading
from collections import deque
import signal
import time
import json
import os
import portalocker

MESSAGE_FILE = "message.json"
RESPONSE_FILE = "response.json"

server_addr = 'D8:3A:DD:6D:E5:D4'
server_port = 1

buf_size = 1024

client_sock = None
server_sock = None
sock = None

exit_event = threading.Event()

message_queue = deque([])
output = ""

dq_lock = threading.Lock()
output_lock = threading.Lock()

def handler(signum, frame):
    exit_event.set()

signal.signal(signal.SIGINT, handler)

def start_client():
    global sock
    global dq_lock
    global output_lock
    global exit_event
    global message_queue
    global output
    global server_addr
    global server_port
    sock = socket.socket(socket.AF_BLUETOOTH, socket.SOCK_STREAM, socket.BTPROTO_RFCOMM)
    sock.settimeout(60)
    sock.connect((server_addr,server_port))
    sock.settimeout(None)
    print("after connect")
    sock.setblocking(False)
    while not exit_event.is_set():
        if dq_lock.acquire(blocking=False):
            if(len(message_queue) > 0):
                try:
                    sent = sock.send(bytes(message_queue[0], 'utf-8'))
                except Exception as e:
                    exit_event.set()
                    continue
                if sent < len(message_queue[0]):
                    message_queue[0] = message_queue[0][sent:]
                else:
                    message_queue.popleft()
            dq_lock.release()
        
        if output_lock.acquire(blocking=False):
            data = ""
            try:
                try:
                    data = sock.recv(1024).decode("utf-8")
                except socket.error as e:
                    assert(1==1)
                    #no data
            except Exception as e:
                exit_event.set()
                continue
            output += data
            output_split = output.split("\r\n")
            for i in range(len(output_split) - 1):
                print(output_split[i])
            output = output_split[-1]
            output_lock.release()
    sock.close()
    print("client thread end")


"""
            with open(RESPONSE_FILE, "w") as file:
                portalocker.lock(file, portalocker.LOCK_EX)
                json.dump({"reply": output_split}, file)
                portalocker.unlock(file)
            print("Python created response.json")
"""            
            


cth = threading.Thread(target=start_client)

cth.start()


print("finish join")
j = 0
while not exit_event.is_set():
    dq_lock.acquire()

    message_queue.append("PC " + str(j) + " \r\n")                 

    if os.path.exists(MESSAGE_FILE) and os.path.getsize(MESSAGE_FILE) > 0:
        with open(MESSAGE_FILE, "r+") as file:
            try:
                portalocker.lock(file, portalocker.LOCK_EX)
                data = json.load(file)
                message_queue.append(json.dumps(data) + " \r\n")
                file.truncate(0)
                portalocker.unlock(file)
            except json.decoder.JSONDecodeError:
                print("JSONDecodeError: File Empty or Damaged")

    dq_lock.release()
    j += 1
    time.sleep(2)

print("Disconnected.")



print("All done.")