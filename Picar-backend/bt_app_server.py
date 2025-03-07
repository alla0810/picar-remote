from bluedot.btcomm import BluetoothServer
from signal import pause
from picarx import Picarx
import os
import time


def received_handler(data, px: Picarx):

    if os.getenv("DEBUG") == "1":
        print(f"Received data: {data}")
        s.send(data)

    def get_car_data(px):
        try:
            # Get battery voltage (approximate)
            battery = 7.4  # Default for PiCar-X if not available

            # Get CPU temperature
            temp = os.popen("vcgencmd measure_temp").readline()
            temp = temp.replace("temp=", "").replace("'C\n", "")

            # Get ultrasonic sensor reading
            distance = px.ultrasonic.read()
            if distance is None or distance < 0:
                distance = 100  # Default value if reading fails

            # Return data as dictionary
            return f"battery={battery},temperature={temp},distance={distance}}"
        except Exception as e:
            print(f"Error getting car data: {e}")
            return f"battery={battery},temperature={temp},distance={distance}}"

    print(get_car_data(px))
    s.send(get_car_data(px))

    try:
        direction, x_str, y_str = data.split(",")
        x = float(x_str)
        y = -float(y_str)

        if direction == "L":
            px.set_cam_pan_angle(x * 40.0)
            px.set_cam_tilt_angle(y * 40.0)
            current_cam_pan = x * 60
            current_cam_tilt = y * 60
        elif direction == "R":
            px.set_dir_servo_angle(x * 60.0)
            px.forward(y * 10.0)
            current_direction = y * 10
            current_steering = x * 60
    except:
        px.stop()


def disconnect_handler(px: Picarx):
    print("Bluetooth app lient disconnected. Waiting for reconnection...")
    px.stop()


def connect_handler():
    print("Bluetooth app client connected")


def create_bluetooth_server(
    px: Picarx,
    received_handler=received_handler,
    connect_handler=connect_handler,
    disconnect_handler=disconnect_handler,
):
    return BluetoothServer(
        lambda data: received_handler(data, px),
        when_client_connects=connect_handler,
        when_client_disconnects=lambda: disconnect_handler(px),
    )


if __name__ == "__main__":
    px = Picarx()
    try:
        s = create_bluetooth_server(px)
        pause()
    finally:
        px.stop()
        s.stop()
