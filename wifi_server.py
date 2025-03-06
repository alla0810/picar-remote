import socket
from time import sleep
from picarx import Picarx
import netifaces as ni


# Get Pi's IP address
def get_ip_address():
    interfaces = ni.interfaces()
    for interface in interfaces:
        if interface != "lo":
            try:
                ip = ni.ifaddresses(interface)[ni.AF_INET][0]["addr"]
                return ip
            except KeyError:
                continue
    return "127.0.0.1"


HOST = get_ip_address()
PORT = 65432  # Port to listen on (non-privileged ports are > 1023)

px = Picarx()
pan_angle = 0
tilt_angle = 0


with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.bind((HOST, PORT))
    s.listen()

    try:
        while 1:
            client, clientInfo = s.accept()
            print("server recv from: ", clientInfo)
            data = client.recv(1024)  # receive 1024 Bytes of message in binary format

            if data != b"":
                print(data)

                text = data.decode().strip().lower()
                print(f"Decoded data: {text}")

                if text == "headup":
                    print("tilt up pressed!")
                    tilt_angle += 5
                    if tilt_angle > 60:
                        tilt_angle = 60
                elif text == "headdown":
                    print("tilt down pressed!")
                    tilt_angle -= 5
                    if tilt_angle < -60:
                        tilt_angle = -60
                elif text == "headleft":
                    print("pan left pressed!")
                    pan_angle -= 5
                    if pan_angle < -60:
                        pan_angle = -60
                elif text == "headright":
                    print("pan right pressed!")
                    pan_angle += 5
                    if pan_angle > 60:
                        pan_angle = 60

                elif text == "driveup":
                    print("drive up pressed!")
                    px.set_dir_servo_angle(0)
                    px.forward(80)

                elif text == "drivedown":
                    print("drive down pressed!")
                    px.set_dir_servo_angle(0)
                    px.backward(80)

                elif text == "driveleft":
                    print("drive left pressed!")
                    px.set_dir_servo_angle(-30)
                    px.forward(80)

                elif text == "driveright":
                    print("drive right pressed!")
                    px.set_dir_servo_angle(30)
                    px.forward(80)

                px.set_cam_tilt_angle(tilt_angle)
                px.set_cam_pan_angle(pan_angle)
                sleep(0.5)
                px.forward(0)

                client.sendall(data)  # Echo back to client

    except:
        print("Closing socket")
        client.close()
        s.close()

    finally:
        px.set_cam_tilt_angle(0)
        px.set_cam_pan_angle(0)
        px.set_dir_servo_angle(0)
        px.stop()
        sleep(0.2)
