class AppConstants {
  // Liveness Detection Thresholds (relaxed for easier enrollment)
  static const double livenessPassThreshold = 0.5;
  static const int faceDetectionDurationMs = 1000;
  static const double blinkThreshold = 0.22;
  static const double eyeOpenThreshold = 0.5;
  static const double headRotationThreshold = 5.0; // Was 10.0 - less rotation needed

  // Storage Keys
  static const String keyStudentId = 'student_id';
  static const String keyDeviceId = 'device_id';
  static const String keyIsFirstLaunch = 'is_first_launch';

  // API Configuration - Update baseUrl to your backend server
  static const String apiBaseUrl = 'https://sialoid-louetta-semiprofessionally.ngrok-free.dev'; 
  static String get markAttendanceUrl => '$apiBaseUrl/mark';
  static String get attendanceHistoryUrl => '$apiBaseUrl/api/attendance';
  static String get healthCheckUrl => '$apiBaseUrl/api/health';

  // UI Constants
  static const double defaultPadding = 16.0;
  static const double defaultBorderRadius = 12.0;
  static const Duration defaultAnimationDuration = Duration(milliseconds: 300);

  // Error Messages
  static const String errorNetwork = 'Network error. Please check your connection.';
  static const String errorQrExpired = 'QR code has expired. Please scan a fresh code.';
  static const String errorAlreadyMarked = 'Attendance already marked for this session.';
  static const String errorInvalidQr = 'Invalid QR code. Please try again.';
  static const String errorLivenessFailed = 'Liveness check failed. Please try again.';
  static const String errorCameraPermission = 'Camera permission is required.';
}
