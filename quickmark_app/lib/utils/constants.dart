class AppConstants {
  // API Configuration - EASILY REPLACEABLE
  // Replace this with your ngrok URL when running
  static const String apiBaseUrl = 'https://sialoid-louetta-semiprofessionally.ngrok-free.dev';
  
  // Example: 'https://abc123.ngrok.io'
  // Or for local testing: 'http://10.0.2.2:8000' (Android emulator)
  // Or for local testing: 'http://localhost:8000' (iOS simulator)

  // Liveness Detection Thresholds (relaxed for easier enrollment)
  static const double livenessPassThreshold = 0.5; // Was 0.7
  static const int faceDetectionDurationMs = 1000; // Was 1500
  static const double blinkThreshold = 0.4; // Was 0.3 - more tolerant
  static const double eyeOpenThreshold = 0.5; // Was 0.7 - more tolerant
  static const double headRotationThreshold = 5.0; // Was 10.0 - less rotation needed

  // Storage Keys
  static const String keyStudentId = 'student_id';
  static const String keyDeviceId = 'device_id';
  static const String keyIsFirstLaunch = 'is_first_launch';

  // API Endpoints
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
