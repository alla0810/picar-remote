import socket
import json
import time
import os
import signal
import sys
from threading import Thread, Event
from picarx import Picarx

# Flask for camera streaming
from flask import Flask, Response, render_template_string
import cv2
from picamera2 import Picamera2
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
    raise Exception("Unable to get local IP address")


HOST = get_ip_address()
WIFI_PORT = 65432  # Port for WiFi control
CAMERA_PORT = 8000  # Port for camera stream

# Initialize the car
px = Picarx()
servo_offset = 0  # Front wheel offset

# Default speeds
FORWARD_SPEED = 25
BACKWARD_SPEED = 25
TURN_SPEED = 15

# Track current car state
current_direction = "stop"  # "forward", "backward", or "stop"
current_steering = 0  # -30 (left) to 30 (right)
current_cam_pan = 0  # -80 to 80 degrees
current_cam_tilt = 8  # Default tilt from your smart_navigation.py

# Camera variables
camera = None
global_frame = None
last_frame_time = 0
FRAME_INTERVAL = 0.1  # Limit to 10 FPS to reduce CPU usage
camera_running = True
shutdown_event = Event()


# Initialize camera
def init_camera():
    global camera
    try:
        camera = Picamera2()
        camera_config = camera.create_still_configuration(main={"size": (640, 480)})
        camera.configure(camera_config)
        camera.start()
        print("Camera initialized successfully")
        return True
    except Exception as e:
        print(f"Error initializing camera: {e}")
        return False


# Capture frames
def capture_frames():
    global global_frame, last_frame_time, camera_running

    if camera is None:
        print("Camera not available, cannot capture frames")
        return

    print("Starting frame capture thread")

    # Set initial camera position
    px.set_cam_pan_angle(current_cam_pan)
    px.set_cam_tilt_angle(current_cam_tilt)

    retry_count = 0
    max_retries = 5

    while camera_running and not shutdown_event.is_set():
        try:
            current_time = time.time()
            if current_time - last_frame_time >= FRAME_INTERVAL:
                # Capture frame
                image = camera.capture_array()

                # Optional: Add text overlay with car status
                status_text = f"Dir: {current_direction} | Steer: {current_steering} | Cam: {current_cam_pan},{current_cam_tilt}"
                cv2.putText(
                    image,
                    status_text,
                    (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.7,
                    (0, 255, 0),
                    2,
                )

                # Convert to JPEG
                _, buffer = cv2.imencode(".jpg", image, [cv2.IMWRITE_JPEG_QUALITY, 70])
                global_frame = buffer.tobytes()
                last_frame_time = current_time
                retry_count = 0  # Reset retry counter on success

            # Brief sleep to reduce CPU usage
            time.sleep(0.01)
        except Exception as e:
            retry_count += 1
            print(f"Error capturing frame ({retry_count}/{max_retries}): {e}")

            if retry_count >= max_retries:
                print("Too many camera errors, restarting camera...")
                try:
                    if camera:
                        camera.close()
                    init_camera()
                    retry_count = 0
                except Exception as restart_error:
                    print(f"Failed to restart camera: {restart_error}")

            time.sleep(1)

    print("Camera frame capture stopped")
    if camera:
        try:
            camera.close()
            print("Camera closed successfully")
        except:
            pass


# Function to get car data
def get_car_data():
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
        return {
            "battery": battery,
            "temperature": temp,
            "distance": distance,
            "direction": current_direction,
            "steering": current_steering,
            "cam_pan": current_cam_pan,
            "cam_tilt": current_cam_tilt,
            "timestamp": time.time(),
        }
    except Exception as e:
        print(f"Error getting car data: {e}")
        return {
            "battery": 7.4,
            "temperature": "25.0",
            "distance": 100,
            "direction": current_direction,
            "steering": current_steering,
            "cam_pan": current_cam_pan,
            "cam_tilt": current_cam_tilt,
            "timestamp": time.time(),
            "error": str(e),
        }


# Function to handle client connection
def handle_client(conn, addr):
    print(f"Connected by {addr}")
    with conn:
        while not shutdown_event.is_set():
            try:
                data = conn.recv(1024)
                if not data:
                    break

                # Decode the received command
                command_data = data.decode()
                print(f"Received command: {command_data}")

                # Check if the command has a speed parameter
                if ":" in command_data:
                    command, value = command_data.split(":", 1)
                    response = process_command(command, value)
                else:
                    response = process_command(command_data)

                # Send car data back to client
                car_data = get_car_data()
                car_data["response"] = response
                conn.sendall(json.dumps(car_data).encode())

            except Exception as e:
                print(f"Error: {e}")
                break
    print(f"Connection with {addr} closed")
    # For safety, stop the car when the connection is lost
    px.stop()


# Function to update car movement based on current state
def update_car_movement(speed=None):
    global current_direction

    if current_direction == "forward":
        if speed is not None:
            px.forward(int(speed))
        else:
            px.forward(FORWARD_SPEED)
    elif current_direction == "backward":
        if speed is not None:
            px.backward(int(speed))
        else:
            px.backward(BACKWARD_SPEED)
    else:  # stop
        px.stop()


# Function to process commands
def process_command(command, value=None):
    global current_direction, current_steering, current_cam_pan, current_cam_tilt

    # Handle different commands
    try:
        if command == "forward":
            current_direction = "forward"
            if value:
                update_car_movement(value)
            else:
                update_car_movement()
            return "Moving forward"

        elif command == "backward":
            current_direction = "backward"
            if value:
                update_car_movement(value)
            else:
                update_car_movement()
            return "Moving backward"

        elif command == "left":
            # Just change steering angle, maintain current movement
            current_steering = -30
            px.set_dir_servo_angle(-30 + servo_offset)
            return "Steering left"

        elif command == "right":
            # Just change steering angle, maintain current movement
            current_steering = 30
            px.set_dir_servo_angle(30 + servo_offset)
            return "Steering right"

        elif command == "center":
            # Center the steering
            current_steering = 0
            px.set_dir_servo_angle(servo_offset)
            return "Steering centered"

        elif command == "stop":
            # Stop the car and center the wheels
            current_direction = "stop"
            px.stop()
            px.set_dir_servo_angle(servo_offset)
            current_steering = 0
            return "Stopped"

        elif command == "speed":
            # Update speed with current direction
            if value and value.isdigit():
                update_car_movement(value)
                return f"Speed set to {value}"
            return "Invalid speed value"

        elif command == "cam_left":
            # Pan camera left
            current_cam_pan = max(-80, current_cam_pan - 10)
            px.set_cam_pan_angle(current_cam_pan)
            return f"Camera panning left: {current_cam_pan}°"

        elif command == "cam_right":
            # Pan camera right
            current_cam_pan = min(80, current_cam_pan + 10)
            px.set_cam_pan_angle(current_cam_pan)
            return f"Camera panning right: {current_cam_pan}°"

        elif command == "cam_center":
            # Center camera
            current_cam_pan = 0
            px.set_cam_tilt_angle(current_cam_tilt)  # Maintain tilt
            px.set_cam_pan_angle(current_cam_pan)
            return "Camera centered"

        elif command == "cam_up":
            # Tilt camera up (fixed - per your note about swapped directions)
            current_cam_tilt = min(35, current_cam_tilt + 5)
            px.set_cam_tilt_angle(current_cam_tilt)
            return f"Camera tilting up: {current_cam_tilt}°"

        elif command == "cam_down":
            # Tilt camera down (fixed - per your note about swapped directions)
            current_cam_tilt = max(-35, current_cam_tilt - 5)
            px.set_cam_tilt_angle(current_cam_tilt)
            return f"Camera tilting down: {current_cam_tilt}°"

        elif command == "stats":
            # Just return current stats
            return "Stats updated"

        else:
            return f"Unknown command: {command}"

    except Exception as e:
        return f"Error executing command: {e}"


# Flask app for camera streaming
app = Flask(__name__)


def generate_frames():
    while not shutdown_event.is_set():
        if global_frame is not None:
            yield (
                b"--frame\r\n"
                b"Content-Type: image/jpeg\r\n\r\n" + global_frame + b"\r\n"
            )
        else:
            # If no frame is available, yield an empty response
            yield (b"--frame\r\n" b"Content-Type: image/jpeg\r\n\r\n\r\n")

        # Control the frame rate
        time.sleep(0.1)


@app.route("/video_feed")
def video_feed():
    return Response(
        generate_frames(), mimetype="multipart/x-mixed-replace; boundary=frame"
    )


@app.route("/")
def index():
    camera_status = "Active" if camera else "Not Available"
    html_template = """
    <!DOCTYPE html>
    <html>
      <head>
        <title>PiCar Camera</title>
        <style>
          body { 
            font-family: Arial, sans-serif; 
            text-align: center; 
            margin-top: 50px;
            background-color: #f5f5f5;
          }
          h1 {
            color: #2196F3;
          }
          .container {
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
            background-color: white;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
          }
          .status {
            background-color: #e8f5e9;
            padding: 10px;
            border-radius: 5px;
            margin: 20px 0;
            display: inline-block;
          }
          img {
            max-width: 100%;
            border-radius: 5px;
            margin-top: 20px;
          }
        </style>
      </head>
      <body>
        <div class="container">
          <h1>PiCar Camera Stream</h1>
          <div class="status">Camera Status: {{ camera_status }}</div>
          <img src="/video_feed" alt="Camera Stream" />
        </div>
      </body>
    </html>
    """
    return render_template_string(html_template, camera_status=camera_status)


# Threaded WiFi control server
def start_wifi_server():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind((HOST, WIFI_PORT))
        s.listen()
        print(f"WiFi server listening on {HOST}:{WIFI_PORT}")

        while not shutdown_event.is_set():
            try:
                s.settimeout(1.0)  # Add timeout to check shutdown event
                try:
                    conn, addr = s.accept()
                    # Start a new thread to handle the client
                    client_thread = Thread(target=handle_client, args=(conn, addr))
                    client_thread.daemon = True
                    client_thread.start()
                except socket.timeout:
                    continue
            except Exception as e:
                if not shutdown_event.is_set():
                    print(f"Error accepting connection: {e}")
                    # For safety, stop the car if there's a server error
                    px.stop()


# Handle shutdown signals
def signal_handler(sig, frame):
    print("\nShutdown signal received, cleaning up...")
    shutdown_event.set()

    # Stop the car
    px.stop()

    # Reset camera position
    px.set_cam_pan_angle(0)
    px.set_cam_tilt_angle(8)

    # Exit the program
    print("Shutdown complete")
    sys.exit(0)


# Main function to start both servers
def main():
    # Set up signal handling for clean shutdown
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Initialize camera
    camera_initialized = init_camera()

    if camera_initialized:
        # Start frame capture thread
        capture_thread = Thread(target=capture_frames)
        capture_thread.daemon = True
        capture_thread.start()

    # Start WiFi control server in a separate thread
    wifi_thread = Thread(target=start_wifi_server)
    wifi_thread.daemon = True
    wifi_thread.start()

    # Start Flask camera server
    print("Starting Flask camera server...")
    app.run(host="0.0.0.0", port=CAMERA_PORT, threaded=True)


if __name__ == "__main__":
    print("Starting PiCar-X Combined Server...")
    main()
