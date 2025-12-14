import 'dart:convert';
import 'package:http/http.dart' as http;
import '../models/attendance_record.dart';
import '../utils/constants.dart';

class ApiService {
  static final ApiService _instance = ApiService._internal();
  factory ApiService() => _instance;
  ApiService._internal();

  final Duration _timeout = const Duration(seconds: 30);

  /// Mark attendance with QR token
  /// Returns a map with 'success' boolean and 'message' string
  Future<Map<String, dynamic>> markAttendance({
    required String token,
    required String studentId,
    required String deviceId,
    required double livenessScore,
  }) async {
    try {
      // Extract session_id from token if needed
      // Token format: session_id:nonce:expiry:signature
      final url = Uri.parse('${AppConstants.markAttendanceUrl}/$token')
          .replace(queryParameters: {
        'student_id': studentId,
      });

      final response = await http.get(url).timeout(_timeout);

      if (response.statusCode == 200) {
        // Success - attendance marked
        return {
          'success': true,
          'message': 'Attendance marked successfully',
          'data': response.body,
        };
      } else if (response.statusCode == 400) {
        // Bad request - likely already marked or expired
        final body = response.body.toLowerCase();
        if (body.contains('already marked') || body.contains('duplicate')) {
          return {
            'success': false,
            'message': AppConstants.errorAlreadyMarked,
          };
        } else if (body.contains('expired')) {
          return {
            'success': false,
            'message': AppConstants.errorQrExpired,
          };
        } else {
          return {
            'success': false,
            'message': 'Invalid request: ${response.body}',
          };
        }
      } else if (response.statusCode == 404) {
        return {
          'success': false,
          'message': 'Session not found or inactive',
        };
      } else {
        return {
          'success': false,
          'message': 'Server error: ${response.statusCode}',
        };
      }
    } catch (e) {
      return {
        'success': false,
        'message': AppConstants.errorNetwork,
        'error': e.toString(),
      };
    }
  }

  /// Get attendance history for a student
  Future<List<AttendanceRecord>> getAttendanceHistory(String studentId) async {
    try {
      final url = Uri.parse('${AppConstants.attendanceHistoryUrl}/history/$studentId');
      final response = await http.get(url).timeout(_timeout);

      if (response.statusCode == 200) {
        final data = json.decode(response.body);
        final records = data['records'] as List<dynamic>? ?? [];
        
        return records
            .map((record) => AttendanceRecord.fromJson(record as Map<String, dynamic>))
            .toList();
      } else {
        throw Exception('Failed to load attendance history');
      }
    } catch (e) {
      throw Exception('Network error: $e');
    }
  }

  /// Health check to verify backend connectivity
  Future<bool> healthCheck() async {
    try {
      final url = Uri.parse(AppConstants.healthCheckUrl);
      final response = await http.get(url).timeout(const Duration(seconds: 10));
      
      if (response.statusCode == 200) {
        final data = json.decode(response.body);
        return data['status'] == 'ok';
      }
      return false;
    } catch (e) {
      return false;
    }
  }

  /// Parse QR code data to extract token
  /// QR contains URL like: https://example.com/mark_attendance_form/{token}
  String? extractTokenFromQr(String qrData) {
    try {
      final uri = Uri.parse(qrData);
      final pathSegments = uri.pathSegments;
      
      // Look for token in path segments
      if (pathSegments.isNotEmpty) {
        // Token should be the last segment after 'mark_attendance_form'
        final index = pathSegments.indexOf('mark_attendance_form');
        if (index != -1 && index < pathSegments.length - 1) {
          return pathSegments[index + 1];
        }
        // Fallback: return last segment
        return pathSegments.last;
      }
      
      return null;
    } catch (e) {
      return null;
    }
  }
}
