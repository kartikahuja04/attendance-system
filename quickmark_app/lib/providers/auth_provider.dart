import 'package:flutter/foundation.dart';
import '../models/user_model.dart';
import '../services/storage_service.dart';
import '../utils/device_utils.dart';

class AuthProvider with ChangeNotifier {
  final StorageService _storageService = StorageService();
  
  User? _currentUser;
  bool _isLoading = false;
  String? _error;

  User? get currentUser => _currentUser;
  bool get isLoading => _isLoading;
  String? get error => _error;
  bool get isLoggedIn => _currentUser != null;

  /// Initialize - check if user is already logged in
  Future<void> initialize() async {
    _isLoading = true;
    notifyListeners();

    try {
      _currentUser = await _storageService.getUser();
      _error = null;
    } catch (e) {
      _error = 'Failed to load user data';
    } finally {
      _isLoading = false;
      notifyListeners();
    }
  }

  /// Login with student ID
  Future<bool> login(String studentId) async {
    if (studentId.trim().isEmpty) {
      _error = 'Student ID cannot be empty';
      notifyListeners();
      return false;
    }

    _isLoading = true;
    _error = null;
    notifyListeners();

    try {
      // Get or generate device ID
      final deviceId = await _storageService.getOrGenerateDeviceId();

      // Create user
      final user = User(
        studentId: studentId.trim(),
        deviceId: deviceId,
      );

      // Save user
      final success = await _storageService.saveUser(user);

      if (success) {
        _currentUser = user;
        _error = null;
        _isLoading = false;
        notifyListeners();
        return true;
      } else {
        _error = 'Failed to save user data';
        _isLoading = false;
        notifyListeners();
        return false;
      }
    } catch (e) {
      _error = 'Login failed: $e';
      _isLoading = false;
      notifyListeners();
      return false;
    }
  }

  /// Logout
  Future<void> logout() async {
    _isLoading = true;
    notifyListeners();

    try {
      await _storageService.clearUser();
      _currentUser = null;
      _error = null;
    } catch (e) {
      _error = 'Logout failed: $e';
    } finally {
      _isLoading = false;
      notifyListeners();
    }
  }

  /// Clear error
  void clearError() {
    _error = null;
    notifyListeners();
  }

  /// Get device info for display
  Future<Map<String, String>> getDeviceInfo() async {
    final model = await DeviceUtils.getDeviceModel();
    final os = await DeviceUtils.getOsVersion();
    return {
      'model': model,
      'os': os,
      'deviceId': _currentUser?.deviceId ?? 'Unknown',
    };
  }
}
