class User {
  final String studentId;
  final String? password; // Optional as we might not fetch it always
  final String deviceId;
  final String? name;
  final bool isEnrolled;
  final String? faceEmbedding;
  final String? createdAt;

  User({
    required this.studentId,
    this.password,
    required this.deviceId,
    this.name,
    this.isEnrolled = false,
    this.faceEmbedding,
    this.createdAt,
  });

  // Convert User to Map for database
  Map<String, dynamic> toMap() => {
        'student_id': studentId,
        'password': password,
        'device_id': deviceId,
        'name': name,
        'is_enrolled': isEnrolled ? 1 : 0,
        'face_embedding': faceEmbedding,
        'created_at': createdAt,
      };

  // Create User from Map
  factory User.fromMap(Map<String, dynamic> map) => User(
        studentId: map['student_id'] as String,
        password: map['password'] as String?,
        deviceId: map['device_id'] as String,
        name: map['name'] as String?,
        isEnrolled: (map['is_enrolled'] as int?) == 1,
        faceEmbedding: map['face_embedding'] as String?,
        createdAt: map['created_at'] as String?,
      );

  @override
  String toString() => 'User(studentId: $studentId, isEnrolled: $isEnrolled)';
}
