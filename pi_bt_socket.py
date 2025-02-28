import socket
import threading
from collections import deque
import signal
import time
import json
from picarx import Picarx

server_addr = 'D8:3A:DD:6D:E5:D4'
server_port = 1

px = Picarx()

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


def process_message(message):
    global pan_angle,tilt_angle    

    try:
        data = json.loads(message)
        content = data.get("content", "").lower()

        if content == "headup":
            print("tilt up pressed!")
            tilt_angle += 5
            if tilt_angle > 60:
                tilt_angle = 60
        elif content == "headdown":
            print("tilt down pressed!")
            tilt_angle -= 5
            if tilt_angle < -60:
                tilt_angle = -60
        elif content == "headleft":            
            print("pan left pressed!")
            pan_angle -= 5
            if pan_angle < -60:
                pan_angle = -60
        elif content == "headright":
            print("pan right pressed!")
            pan_angle += 5
            if pan_angle > 60:
                pan_angle = 60
        elif content == "driveup":
            print("drive up!")
            px.set_dir_servo_angle(0)
            px.forward(80)
        
        elif content == "drivedown":
            print("drive down")
            px.set_dir_servo_angle(0)
            px.backward(80)

        elif content == "driveleft":
            print("drive left")
            px.set_dir_servo_angle(-30)
            px.forward(80)

        elif content == "driveright":
            print("drive right")
            px.set_dir_servo_angle(30)
            px.forward(80)
        else:
            print("Unknown command:", content)

        px.set_cam_tilt_angle(tilt_angle)
        px.set_cam_pan_angle(pan_angle)
        time.sleep(0.5)
        px.forward(0)
        
    except json.JSONDecodeError:
        print("JSON Format Error:", message)



signal.signal(signal.SIGINT, handler)

def start_client():
    global server_addr
    global server_port
    global server_sock
    global sock
    global exit_event
    global message_queue
    global output
    global dq_lock
    global output_lock
    server_sock = socket.socket(socket.AF_BLUETOOTH, socket.SOCK_STREAM, socket.BTPROTO_RFCOMM)
    server_sock.bind((server_addr, server_port))
    server_sock.listen(1)
    server_sock.settimeout(60)
    sock, address = server_sock.accept()
    print("Connected")
    server_sock.settimeout(None)
    sock.setblocking(0)
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
                    data = sock.recv(1024).decode('utf-8')
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
                try:
                    process_message(output_split[i])
                except json.JSONDecodeError:
                    print("JSON Parsing Error:", output_split[i])


            output = output_split[-1]
            output_lock.release()
    server_sock.close()
    sock.close()
    print("client thread end")


cth = threading.Thread(target=start_client)

cth.start()

j = 0
while not exit_event.is_set():
    dq_lock.acquire()
    message_queue.append("RPi " + str(j) + " \r\n")
    dq_lock.release()
    j += 1
    time.sleep(1.5)
    

print("Disconnected.")


print("All done.")