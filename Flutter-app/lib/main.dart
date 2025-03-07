import 'package:flutter/material.dart';
import 'package:flutter_blue_app/MainPage.dart';

void main() => runApp(ExampleApplication());

class ExampleApplication extends StatelessWidget {
  const ExampleApplication({Key? key}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return MaterialApp(home: MainPage());
  }
}
