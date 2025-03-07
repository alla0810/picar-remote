import 'dart:convert';
import 'dart:typed_data';
import 'package:flutter/material.dart';
import 'package:flutter_bluetooth_serial/flutter_bluetooth_serial.dart';
import 'package:flutter_joystick/flutter_joystick.dart';

class AppPage extends StatefulWidget {
  final BluetoothDevice server;

  const AppPage({Key? key, required this.server}) : super(key: key);

  @override
  _AppPage createState() => _AppPage();
}

class _AppPage extends State<AppPage> {
  BluetoothConnection? connection;

  bool isConnecting = true;
  bool get isConnected => connection != null && connection!.isConnected;
  bool isDisconnecting = false;

  double leftJoystickX = 0, leftJoystickY = 0;
  double rightJoystickX = 0, rightJoystickY = 0;

  @override
  void initState() {
    super.initState();
    BluetoothConnection.toAddress(widget.server.address).then((conn) {
      print('Connected to the device');
      connection = conn;
      setState(() {
        isConnecting = false;
        isDisconnecting = false;
      });

      connection!.input?.listen(_onDataReceived).onDone(() {
        if (isDisconnecting) {
          print('Disconnecting locally!');
        } else {
          print('Disconnected remotely!');
        }
        if (mounted) {
          setState(() {});
        }
      });
    }).catchError((error) {
      print('Cannot connect, exception occurred');
      print(error);
    });
  }

  @override
  void dispose() {
    if (isConnected) {
      isDisconnecting = true;
      connection!.dispose();
      connection = null;
    }
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: Text("Joystick Controller")),
      body: SafeArea(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: <Widget>[
            Row(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                // Left Joystick Column
                Column(
                  children: [
                    Text("Camera: X=${leftJoystickX.toStringAsFixed(2)}, Y=${leftJoystickY.toStringAsFixed(2)}"),
                    SizedBox(height: 10), // Space between text and joystick
                    Joystick(
                      mode: JoystickMode.all,
                      listener: (details) {
                        setState(() {
                          leftJoystickX = details.x;
                          leftJoystickY = details.y;
                        });
                        _sendMessage("L,${details.x},${details.y}");
                      },
                    ),
                  ],
                ),
                SizedBox(width: 50), // Space between the two joysticks
                // Right Joystick Column
                Column(
                  children: [
                    Text("Movement: X=${rightJoystickX.toStringAsFixed(2)}, Y=${rightJoystickY.toStringAsFixed(2)}"),
                    SizedBox(height: 10),
                    Joystick(
                      mode: JoystickMode.all,
                      listener: (details) {
                        setState(() {
                          rightJoystickX = details.x;
                          rightJoystickY = details.y;
                        });
                        _sendMessage("R,${details.x},${details.y}");
                      },
                    ),
                  ],
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }

  void _onDataReceived(Uint8List data) {
    String receivedData = utf8.decode(data);
    print("Received: $receivedData");
  }

  void _sendMessage(String text) async {
    text = text.trim();
    if (text.isNotEmpty) {
      try {
        connection!.output.add(Uint8List.fromList(utf8.encode(text + "\n")));
        await connection!.output.allSent;
      } catch (e) {
        setState(() {});
      }
    }
  }
}
