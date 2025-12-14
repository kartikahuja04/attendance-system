class SessionModel {
  final String sessionId;
  final String className;
  final String subject;
  final String section;
  final DateTime startTime;
  final DateTime? endTime;
  final String status;

  SessionModel({
    required this.sessionId,
    required this.className,
    required this.subject,
    required this.section,
    required this.startTime,
    this.endTime,
    required this.status,
  });

  // Create SessionModel from JSON
  factory SessionModel.fromJson(Map<String, dynamic> json) {
    return SessionModel(
      sessionId: json['session_id'] as String,
      className: json['class_name'] as String,
      subject: json['subject'] as String,
      section: json['section'] as String,
      startTime: DateTime.parse(json['start_time'] as String),
      endTime: json['end_time'] != null
          ? DateTime.parse(json['end_time'] as String)
          : null,
      status: json['status'] as String,
    );
  }

  // Convert to JSON
  Map<String, dynamic> toJson() => {
        'session_id': sessionId,
        'class_name': className,
        'subject': subject,
        'section': section,
        'start_time': startTime.toIso8601String(),
        if (endTime != null) 'end_time': endTime!.toIso8601String(),
        'status': status,
      };

  @override
  String toString() =>
      'SessionModel(sessionId: $sessionId, class: $className, subject: $subject)';
}
