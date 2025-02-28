import bluetooth

def start_client():
    global sock
    global dq_lock
    global output_lock
    global exit_event
    global message_queue
    global output
    global server_addr
    global server_port

    sock = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
    sock.settimeout(10)
    try:
        sock.connect((server_addr, server_port))
        sock.settimeout(None)
        sock.setblocking(False)
        print("Connected to Bluetooth server")
    except bluetooth.BluetoothError as e:
        print(f"Bluetooth connection failed: {e}")
        exit_event.set()
        return