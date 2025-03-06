from bluedot.btcomm import BluetoothServer
from signal import pause
from picarx import Picarx


def received_handler(data):
    print(data)
    s.send(data)
    try:
        direction, x_str, y_str = data.split(",")
        x = float(x_str)
        y = float(y_str)

        if direction == "L":
            px.set_cam_pan_angle(x * 60.0)
            px.set_cam_tilt_angle(-y * 60.0)
        elif direction == "R":
            px.set_dir_servo_angle(x * 60.0)
            px.forward(-y * 10.0)
    except:
        px.stop()


def disconnect_handler():
    print("Client disconnected. Waiting for reconnection...")


if __name__ == "__main__":
    px = Picarx()

    s = BluetoothServer(received_handler, when_client_disconnects=disconnect_handler)
    s.send("Bye from the pi")

    pause()
