class User {
  final String studentId;
  final String deviceId;

  User({
    required this.studentId,
    required this.deviceId,
  });

  // Convert User to JSON for storage
  Map<String, dynamic> toJson() => {
        'student_id': studentId,
        'device_id': deviceId,
      };

  // Create User from JSON
  factory User.fromJson(Map<String, dynamic> json) => User(
        studentId: json['student_id'] as String,
        deviceId: json['device_id'] as String,
      );

  @override
  String toString() => 'User(studentId: $studentId, deviceId: $deviceId)';
}
