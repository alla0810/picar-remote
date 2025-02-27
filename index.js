var server_port = 65432;
var server_addr = "192.168.1.86";   // the IP address of your Raspberry PI

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
    console.log("HeadUp");

    client("HeadUp");

}

function HeadleftArrow(){
    console.log("HeadLeft");

    client("HeadLeft");
}

function HeadrightArrow(){
    console.log("HeadRight");
    
    client("HeadRight");
}

function HeaddownArrow(){
    console.log("HeadDown");

    client("HeadDown");

}

function wifi_bt_toggleSwitch(){
    let toggle = document.getElementById("wifi_bt_toggle");
    let label = document.getElementById("toggleLabel");

    if(toggle.checked){        
        label.textContent = "Bluetooth";
        console.log("Bluetooth")
    }
    else {
        label.textContent = "WiFi";
        console.log("WiFi")        
    }
}


function DriveupArrow(){
    console.log("DriveUp");

    client("DriveUp");

}

function DriveleftArrow(){
    console.log("DriveLeft");

    client("DriveLeft");

}

function DriverightArrow(){
    console.log("DriveRight");

    client("DriveRight");

}

function DrivedownArrow(){
    console.log("DriveDown");

    client("DriveDown");

}