# picar-remote

## Setup 

### Picar

Make sure you have [Picarx](https://github.com/sunfounder/picar-x) and [robot_hat](https://github.com/sunfounder/robot-hat) part of your python libraries
```
git clone https://github.com/alla0810/picar-remote.git
cd picar-remote/Picar-backend/
sudo apt install -y python3-picamera2 python3-opencv libopencv-dev
pip install -r requirements.txt
```

### Remote PC

```
git clone https://github.com/alla0810/picar-remote.git
cd picar-remote/remote-frontend/
npm init -y
npm install electron@35.0.0
```

### Bluetooth App
Make sure your Android phone (Recommend Android 11 or below) is connected to the Pi, and build the Flutter app on it.


## Usage over bluetooth app
Connect your android device (Recommend Android 11 or below) to your raspberry pi and run the app.  
Run the following command on your raspberry pi.
```
python Picar-backend/bt_app_server.py
```

## Usage over wifi

### On Raspberry Pi
```
python Picar-backend/wifi_server.py
```

### On Remote PC
Change the PI_IP address to your raspberrypi's address in [index.js](/remote-frontend/index.js)
```
npm start
```