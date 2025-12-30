import 'package:flutter/foundation.dart';
import '../models/attendance_record.dart';
import '../services/database_service.dart';
import '../services/api_service.dart';

enum AttendanceStatus { idle, loading, success, error }

class AttendanceProvider with ChangeNotifier {
  final DatabaseService _dbService = DatabaseService();
  final ApiService _apiService = ApiService();

  List<AttendanceRecord> _attendanceRecords = [];
  AttendanceStatus _status = AttendanceStatus.idle;
  String? _error;
  String? _successMessage;

  List<AttendanceRecord> get attendanceRecords => _attendanceRecords;
  AttendanceStatus get status => _status;
  String? get error => _error;
  String? get successMessage => _successMessage;
  bool get isLoading => _status == AttendanceStatus.loading;

  /// Submit attendance with QR token
  Future<bool> submitAttendance({
    required String token,
    required String studentId,
    required String deviceId,
    required double livenessScore,
  }) async {
    _status = AttendanceStatus.loading;
    _error = null;
    _successMessage = null;
    notifyListeners();

    try {
      // Submit to backend API so student ID appears on teacher portal
      final result = await _apiService.markAttendance(
        token: token,
        studentId: studentId,
        deviceId: deviceId,
        livenessScore: livenessScore,
      );

      if (result['success'] == true) {
        _status = AttendanceStatus.success;
        _successMessage = result['message'] ?? 'Attendance marked!';
        _error = null;
        
        // Also save locally for offline history
        final parts = token.split(':');
        final sessionId = parts.isNotEmpty ? parts[0] : 'unknown_session';
        
        final record = AttendanceRecord(
          studentId: studentId,
          sessionId: sessionId,
          timestamp: DateTime.now(),
          status: 'Present',
          subject: 'Session $sessionId',
        );
        await _dbService.markAttendance(record);
        
        // Refresh history
        await fetchAttendanceHistory(studentId);
        
        notifyListeners();
        return true;
      } else {
        _status = AttendanceStatus.error;
        _error = result['message'] ?? 'Failed to mark attendance';
        notifyListeners();
        return false;
      }
    } catch (e) {
      _status = AttendanceStatus.error;
      _error = 'Failed to submit attendance: $e';
      notifyListeners();
      return false;
    }
  }

  /// Fetch attendance history
  Future<void> fetchAttendanceHistory(String studentId) async {
    _status = AttendanceStatus.loading;
    _error = null;
    notifyListeners();

    try {
      _attendanceRecords = await _dbService.getAttendanceHistory(studentId);
      _status = AttendanceStatus.success;
      _error = null;
      notifyListeners();
    } catch (e) {
      _status = AttendanceStatus.error;
      _error = 'Failed to load attendance history: $e';
      _attendanceRecords = [];
      notifyListeners();
    }
  }

  /// Refresh attendance history
  Future<void> refreshHistory(String studentId) async {
    await fetchAttendanceHistory(studentId);
  }

  /// Clear error
  void clearError() {
    _error = null;
    notifyListeners();
  }

  /// Clear success message
  void clearSuccessMessage() {
    _successMessage = null;
    notifyListeners();
  }

  /// Reset state
  void reset() {
    _status = AttendanceStatus.idle;
    _error = null;
    _successMessage = null;
    notifyListeners();
  }

  /// Extract token from QR code
  /// Only accepts QR codes from teacher portal (URL with mark_attendance_form path)
  String? extractToken(String qrData) {
    if (qrData.isEmpty) return null;
    // Use ApiService to validate and extract token from teacher portal URL
    return _apiService.extractTokenFromQr(qrData);
  }
}
