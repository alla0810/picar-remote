const net = require('net');

// Configuration - update with your Raspberry Pi's IP
const PI_IP = '192.168.1.233';
const PI_PORT = 65432;

// Variables
let client = null;
let connected = false;
let reconnectTimer = null;
let carSpeed = 25; // Default speed
const RECONNECT_INTERVAL = 5000; // 5 seconds
let activeMoveCommand = null; // Tracks the current movement command (forward, backward, stop)
let activeSteeringCommand = "center"; // Tracks steering (left, right, center)

// Setup camera stream function
function setupCameraStream() {
    const cameraStreamElement = document.getElementById('cameraStream');
    const streamUrl = `http://${PI_IP}:8000/video_feed`;
    
    console.log(`Attempting to load camera stream from: ${streamUrl}`);
    cameraStreamElement.src = streamUrl;
    
    cameraStreamElement.onload = () => {
        console.log('Camera stream loaded successfully');
    };
    
    cameraStreamElement.onerror = () => {
        console.error('Failed to load camera stream');
        cameraStreamElement.alt = 'Camera stream unavailable';
        
        const container = cameraStreamElement.parentElement;
        const placeholder = document.createElement('div');
        placeholder.style.textAlign = 'center';
        placeholder.style.padding = '20px';
        placeholder.style.color = '#666';
        placeholder.innerHTML = `
            <p>Camera stream unavailable</p>
            <p style="font-size: 0.8em; color: #999;">Make sure the camera server is running on ${PI_IP}:8000</p>
        `;
        container.appendChild(placeholder);
    };
}

// Update camera control UI
function updateCameraControls(camPan, camTilt) {
    // Reset all highlights
    ['camUpBtn', 'camDownBtn', 'camLeftBtn', 'camRightBtn', 'camCenterBtn'].forEach(id => {
        const btn = document.getElementById(id);
        if (btn) btn.classList.remove('active-button');
    });
    
    // Highlight active direction
    if (camPan < -10) {
        const btn = document.getElementById('camLeftBtn');
        if (btn) btn.classList.add('active-button');
    } else if (camPan > 10) {
        const btn = document.getElementById('camRightBtn');
        if (btn) btn.classList.add('active-button');
    }
    
    // Note: We're using the swapped logic per your comment
    if (camTilt > 13) {
        const btn = document.getElementById('camUpBtn');
        if (btn) btn.classList.add('active-button');
    } else if (camTilt < 3) {
        const btn = document.getElementById('camDownBtn');
        if (btn) btn.classList.add('active-button');
    }
}

// Connect to the Pi server
function connectToServer() {
    if (client) {
        client.destroy();
    }
    
    client = new net.Socket();
    
    client.connect(PI_PORT, PI_IP, () => {
        console.log('Connected to PiCar server');
        connected = true;
        updateConnectionStatus(true);
        clearTimeout(reconnectTimer);
    });
    
    client.on('data', (data) => {
        try {
            const response = JSON.parse(data.toString());
            console.log('Response from server:', response);
            updateCarStats(response);
            updateStatusMessage(response.response || 'Command received');
            
            // Update UI based on car's state
            updateUIFromCarState(response.direction, response.steering);
        } catch (error) {
            console.error('Error parsing response:', error);
        }
    });
    
    client.on('close', () => {
        console.log('Connection closed');
        connected = false;
        updateConnectionStatus(false);
        
        // Try to reconnect
        reconnectTimer = setTimeout(connectToServer, RECONNECT_INTERVAL);
    });
    
    client.on('error', (err) => {
        console.error('Connection error:', err);
        connected = false;
        updateConnectionStatus(false);
    });
}

// Send command to the Pi
function sendCommand(command, value = null) {
    if (!connected || !client) {
        updateStatusMessage('Not connected to PiCar. Trying to reconnect...');
        connectToServer();
        return;
    }
    
    try {
        let fullCommand = command;
        if (value !== null) {
            fullCommand = `${command}:${value}`;
        }
        
        client.write(fullCommand);
        updateStatusMessage(`Sending command: ${fullCommand}`);
        
        // Update active commands tracking
        if (command === 'forward' || command === 'backward' || command === 'stop') {
            activeMoveCommand = command;
        }
        
        if (command === 'left' || command === 'right' || command === 'center') {
            activeSteeringCommand = command;
        }
    } catch (error) {
        console.error('Error sending command:', error);
        updateStatusMessage(`Error sending command: ${error.message}`);
    }
}

// Update the car statistics displayed in the UI
function updateCarStats(data) {
    if (data.battery !== undefined) {
        document.getElementById('batteryLevel').innerText = `${data.battery.toFixed(2)}V`;
    }
    
    if (data.temperature !== undefined) {
        document.getElementById('temperature').innerText = `${data.temperature}°C`;
    }
    
    if (data.distance !== undefined) {
        document.getElementById('distance').innerText = `${data.distance.toFixed(1)} cm`;
    }
    
    if (data.timestamp !== undefined) {
        const date = new Date(data.timestamp * 1000);
        document.getElementById('lastUpdate').innerText = date.toLocaleTimeString();
    }

    // Update camera position if available
    if (data.cam_pan !== undefined && data.cam_tilt !== undefined) {
        updateCameraControls(data.cam_pan, data.cam_tilt);
    }
}

// Update the connection status display
function updateConnectionStatus(isConnected) {
    const statusElement = document.getElementById('connectionStatus');
    
    if (isConnected) {
        statusElement.innerText = 'Connected to PiCar-X';
        statusElement.className = 'connected';
    } else {
        statusElement.innerText = 'Disconnected from PiCar-X';
        statusElement.className = 'disconnected';
    }
}

// Update the status message
function updateStatusMessage(message) {
    document.getElementById('statusMessage').innerText = message;
}

// Update UI based on car's current state
function updateUIFromCarState(direction, steering) {
    // Update movement buttons
    resetMovementHighlights();
    let movementText = "Stopped";
    if (direction === "forward") {
        highlightButton('upBtn', true);
        movementText = "Forward";
    } else if (direction === "backward") {
        highlightButton('downBtn', true);
        movementText = "Backward";
    }
    document.getElementById('currentMovement').innerText = movementText;
    
    // Update steering buttons
    resetSteeringHighlights();
    let steeringText = "Centered";
    if (steering === -30) {
        highlightButton('leftBtn', true);
        steeringText = "Left";
    } else if (steering === 30) {
        highlightButton('rightBtn', true);
        steeringText = "Right";
    }
    document.getElementById('currentSteering').innerText = steeringText;
}

// Update the speed value and store it
function updateSpeed(value) {
    carSpeed = value;
    document.getElementById('speedValue').innerText = value;
    
    // If car is already moving, update the speed
    if (activeMoveCommand && activeMoveCommand !== 'stop' && connected) {
        sendCommand('speed', carSpeed);
    }
}

// Highlight the active button
function highlightButton(buttonId, active) {
    const button = document.getElementById(buttonId);
    if (!button) return;
    
    if (active) {
        button.style.transform = 'scale(0.95)';
        button.style.boxShadow = '0 2px 3px rgba(0, 0, 0, 0.1)';
        button.classList.add('active-button');
    } else {
        button.style.transform = '';
        button.style.boxShadow = '';
        button.classList.remove('active-button');
    }
}

// Reset movement button highlights
function resetMovementHighlights() {
    ['upBtn', 'downBtn'].forEach(id => {
        highlightButton(id, false);
    });
}

// Reset steering button highlights
function resetSteeringHighlights() {
    ['leftBtn', 'rightBtn'].forEach(id => {
        highlightButton(id, false);
    });
}

// Initialize the application when the page loads
document.addEventListener('DOMContentLoaded', () => {
    // Initialize connection to server
    connectToServer();
    
    // Set up camera stream
    setupCameraStream();
    
    // Set up movement button click handlers
    document.getElementById('upBtn').addEventListener('click', () => {
        sendCommand('forward', carSpeed);
        resetMovementHighlights();
        highlightButton('upBtn', true);
    });
    
    document.getElementById('downBtn').addEventListener('click', () => {
        sendCommand('backward', carSpeed);
        resetMovementHighlights();
        highlightButton('downBtn', true);
    });
    
    // Set up steering button click handlers
    document.getElementById('leftBtn').addEventListener('click', () => {
        sendCommand('left');
        resetSteeringHighlights();
        highlightButton('leftBtn', true);
    });
    
    document.getElementById('rightBtn').addEventListener('click', () => {
        sendCommand('right');
        resetSteeringHighlights();
        highlightButton('rightBtn', true);
    });
    
    // Set up camera control buttons
    document.getElementById('camLeftBtn').addEventListener('click', () => {
        sendCommand('cam_left');
    });
    
    document.getElementById('camRightBtn').addEventListener('click', () => {
        sendCommand('cam_right');
    });
    
    document.getElementById('camUpBtn').addEventListener('click', () => {
        sendCommand('cam_up');
    });
    
    document.getElementById('camDownBtn').addEventListener('click', () => {
        sendCommand('cam_down');
    });
    
    document.getElementById('camCenterBtn').addEventListener('click', () => {
        sendCommand('cam_center');
    });
    
    // Stop button resets everything
    document.getElementById('stopBtn').addEventListener('click', () => {
        sendCommand('stop');
        resetMovementHighlights();
        resetSteeringHighlights();
    });
    
    // Set up speed slider
    const speedSlider = document.getElementById('speedSlider');
    speedSlider.addEventListener('input', () => {
        updateSpeed(speedSlider.value);
    });
    
    // Set up keyboard controls
    document.addEventListener('keydown', (event) => {
        // Avoid repeating commands when key is held down
        if (event.repeat) return;
        
        switch(event.key) {
            case 'ArrowUp':
                sendCommand('forward', carSpeed);
                resetMovementHighlights();
                highlightButton('upBtn', true);
                break;
            case 'ArrowDown':
                sendCommand('backward', carSpeed);
                resetMovementHighlights();
                highlightButton('downBtn', true);
                break;
            case 'ArrowLeft':
                sendCommand('left');
                resetSteeringHighlights();
                highlightButton('leftBtn', true);
                break;
            case 'ArrowRight':
                sendCommand('right');
                resetSteeringHighlights();
                highlightButton('rightBtn', true);
                break;
            case ' ': // Space bar
                sendCommand('stop');
                resetMovementHighlights();
                resetSteeringHighlights();
                break;
            // Camera control keys (with fixed up/down logic per your comment)
            case 'w':
                sendCommand('cam_up');
                highlightButton('camUpBtn', true);
                break;
            case 'a':
                sendCommand('cam_left');
                highlightButton('camLeftBtn', true);
                break;
            case 's':
                sendCommand('cam_down');
                highlightButton('camDownBtn', true);
                break;
            case 'd':
                sendCommand('cam_right');
                highlightButton('camRightBtn', true);
                break;
            case 'c':
                sendCommand('cam_center');
                highlightButton('camCenterBtn', true);
                setTimeout(() => highlightButton('camCenterBtn', false), 300);
                break;
        }
    });
    
    // Reset buttons on key up
    document.addEventListener('keyup', (event) => {
        // Auto-center when arrows are released
        if (event.key === 'ArrowLeft' || event.key === 'ArrowRight') {
            sendCommand('center');
            resetSteeringHighlights();
        }
        
        // Reset camera button highlights
        switch(event.key.toLowerCase()) {
            case 'w':
                highlightButton('camUpBtn', false);
                break;
            case 'a':
                highlightButton('camLeftBtn', false);
                break;
            case 's':
                highlightButton('camDownBtn', false);
                break;
            case 'd':
                highlightButton('camRightBtn', false);
                break;
        }
    });
    
    // Set up regular polling for updated car stats
    setInterval(() => {
        if (connected) {
            // Send a stats command to get updated stats
            try {
                client.write('stats');
            } catch (e) {
                console.error('Error polling stats:', e);
            }
        }
    }, 1000); // Update stats every second
});
