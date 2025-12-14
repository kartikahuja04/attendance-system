class AttendanceRecord {
  final String sessionId;
  final DateTime timestamp;
  final String status;
  final String? className;
  final String? subject;
  final String? section;

  AttendanceRecord({
    required this.sessionId,
    required this.timestamp,
    required this.status,
    this.className,
    this.subject,
    this.section,
  });

  // Create AttendanceRecord from JSON
  factory AttendanceRecord.fromJson(Map<String, dynamic> json) {
    return AttendanceRecord(
      sessionId: json['session_id'] as String,
      timestamp: DateTime.parse(json['timestamp'] as String),
      status: json['status'] as String? ?? 'Present',
      className: json['class_name'] as String?,
      subject: json['subject'] as String?,
      section: json['section'] as String?,
    );
  }

  // Convert to JSON
  Map<String, dynamic> toJson() => {
        'session_id': sessionId,
        'timestamp': timestamp.toIso8601String(),
        'status': status,
        if (className != null) 'class_name': className,
        if (subject != null) 'subject': subject,
        if (section != null) 'section': section,
      };

  @override
  String toString() =>
      'AttendanceRecord(sessionId: $sessionId, timestamp: $timestamp, status: $status)';
}
