const fs = require('fs');
const lockfile = require('proper-lockfile');

const MESSAGE_FILE = "message.json";
const RESPONSE_FILE = "response.json";

var server_port = 65432;
var server_addr = "192.168.1.86";   // the IP address of your Raspberry PI

var WIFI_BT_MODE = "WIFI";   // Default = WIFI

function client(input){
    
    const net = require('net');
//    const net = import('net');    
//    var input = document.getElementById("myName").value;

    const client = net.createConnection({ port: server_port, host: server_addr }, () => {
        // 'connect' listener.
        console.log('connected to server!');
        // send the message
        client.write(`${input}\r\n`);
    });
    
    // get the data from the server
    client.on('data', (data) => {
        document.getElementById("greet_from_server").innerHTML = data;
        console.log(data.toString());
        client.end();
        client.destroy();
    });

    client.on('end', () => {
        console.log('disconnected from server');
    });


}

function update_data(){

    // get the element from html
    var name = document.getElementById("myName").value;
    // update the content in html
    document.getElementById("greet").innerHTML = "Hello " + name + " !";
    // send the data to the server 
//    to_server(name);
    client(name);

}

function HeadupArrow(){
    if (WIFI_BT_MODE == "BT")
    {
        console.log("[BT] HeadUp");        
        sendCommand("HeadUp");
    }
    else
    {    
        console.log("[WIFI] HeadUp");

        client("HeadUp");
    }

}

function HeadleftArrow(){
    if (WIFI_BT_MODE == "BT")
    {
        console.log("[BT] HeadLeft");        
        sendCommand("HeadLeft");
    }
    else
    {    
        console.log("[WIFI] HeadLeft");

        client("HeadLeft");
    }
}

function HeadrightArrow(){

    if (WIFI_BT_MODE == "BT")
    {
        console.log("[BT] HeadRight");        
        sendCommand("HeadRight");
    }
    
    else
    {
        console.log("[WIFI] HeadRight");
    
        client("HeadRight");
    }
}

function HeaddownArrow(){
    if (WIFI_BT_MODE == "BT")
    {
        console.log("[BT] HeadDown");        
        sendCommand("HeadDown");
    }
    else
    {    
        console.log("[WIFI] HeadDown");

        client("HeadDown");
    }

}

function wifi_bt_toggleSwitch(){
    let toggle = document.getElementById("wifi_bt_toggle");
    let label = document.getElementById("toggleLabel");

    if(toggle.checked){        
        label.textContent = "Bluetooth";
        WIFI_BT_MODE = "BT"
        console.log("Bluetooth")
    }
    else {
        label.textContent = "WiFi";
        WIFI_BT_MODE = "WIFI"
        console.log("WiFi")        
    }
}


function DriveupArrow(){

    if (WIFI_BT_MODE == "BT")
    {
        console.log("[BT] DriveUp");        
        sendCommand("DriveUp");
    }
    else
    {
        console.log("[WIFI] DriveUp");                
        client("DriveUp");
    }

}

function DriveleftArrow(){
    if (WIFI_BT_MODE == "BT")
    {
        console.log("[BT] DriveLeft");        
        sendCommand("DriveLeft");
    }
    else
    {
        console.log("[WIFI] DriveLeft");                        
        client("DriveLeft");
    }

}

function DriverightArrow(){
    if (WIFI_BT_MODE == "BT")
    {
        console.log("[BT] DriveRight");        
        sendCommand("DriveRight");
    }
    else
    {
        console.log("[WIFI] DriveRight");                                
        client("DriveRight");
    }

}

function DrivedownArrow(){
    if (WIFI_BT_MODE == "BT")
    {    
        console.log("[BT] DriveDown");        
        sendCommand("DriveDown");
    }
    else
    {
        console.log("DriveDown");

        client("DriveDown");
    }

}



function sendCommand(message) {
    if (!fs.existsSync(MESSAGE_FILE)) {
        fs.writeFileSync(MESSAGE_FILE, "");
    }

    lockfile.lock(MESSAGE_FILE).then((release) => {
        const data = {sender: "JavaScript", content: message};
        fs.writeFileSync(MESSAGE_FILE, JSON.stringify(data));
        console.log("JavaScripte created message.json file");
        release();
    }).catch((err) => console.error("Fail to lockfile", err));

}

function fetchMessages() {
    if (fs.existsSync(RESPONSE_FILE) && fs.statSync(RESPONSE_FILE).size > 0) {
        try {
            const response = JSON.parse(fs.readFileSync(RESPONSE_FILE, "utf8"));
            console.log(`JavaScript received response from Python: ${response.reply}`);
            fs.unlinkSync(RESPONSE_FILE);
        } catch (error) {
            console.error("JSON Parsing Error:", error);
        }

    }
}

sendCommand("Hello from JavaScript!");

setInterval(fetchMessages, 1000);