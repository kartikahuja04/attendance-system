import 'package:flutter/foundation.dart';
import '../models/attendance_record.dart';
import '../services/api_service.dart';

enum AttendanceStatus { idle, loading, success, error }

class AttendanceProvider with ChangeNotifier {
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
      final result = await _apiService.markAttendance(
        token: token,
        studentId: studentId,
        deviceId: deviceId,
        livenessScore: livenessScore,
      );

      if (result['success'] == true) {
        _status = AttendanceStatus.success;
        _successMessage = result['message'] as String;
        _error = null;
        notifyListeners();
        return true;
      } else {
        _status = AttendanceStatus.error;
        _error = result['message'] as String;
        _successMessage = null;
        notifyListeners();
        return false;
      }
    } catch (e) {
      _status = AttendanceStatus.error;
      _error = 'Failed to submit attendance: $e';
      _successMessage = null;
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
      _attendanceRecords = await _apiService.getAttendanceHistory(studentId);
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
  String? extractToken(String qrData) {
    return _apiService.extractTokenFromQr(qrData);
  }
}
