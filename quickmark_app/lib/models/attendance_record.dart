class AttendanceRecord {
  final String? studentId; // New field
  final String sessionId;
  final DateTime timestamp;
  final String status;
  final String? className;
  final String? subject;
  final String? section;

  AttendanceRecord({
    this.studentId,
    required this.sessionId,
    required this.timestamp,
    required this.status,
    this.className,
    this.subject,
    this.section,
  });

  // Create from DB Map
  factory AttendanceRecord.fromMap(Map<String, dynamic> map) {
    return AttendanceRecord(
      studentId: map['student_id'] as String?,
      sessionId: map['session_id'] as String,
      timestamp: DateTime.tryParse(map['timestamp'] as String) ?? DateTime.now(),
      status: map['status'] as String? ?? 'Present',
      className: map['class_name'] as String?,
      subject: map['subject'] as String?,
      section: map['section'] as String?,
    );
  }
  
  // Create from JSON
  factory AttendanceRecord.fromJson(Map<String, dynamic> json) => AttendanceRecord.fromMap(json);

  // Convert to Map for DB
  Map<String, dynamic> toMap() => {
        'student_id': studentId,
        'session_id': sessionId,
        'timestamp': timestamp.toIso8601String(),
        'status': status,
        'class_name': className,
        'subject': subject,
        'section': section,
      };

  @override
  String toString() =>
      'AttendanceRecord(sessionId: $sessionId, timestamp: $timestamp, status: $status)';
}
