// Dart Test File
class User {
  final String name;
  final String email;
  final int age;
  
  User({required this.name, required this.email, required this.age});
  
  @override
  String toString() => 'User: \ (\), \ Jahre';
}

void main() {
  final users = [
    User(name: 'Anna', email: 'anna@example.com', age: 25),
    User(name: 'Ben', email: 'ben@example.com', age: 30),
  ];
  
  for (var user in users) {
    print(user);
  }
  
  print('Durchschnittsalter: \');
}
