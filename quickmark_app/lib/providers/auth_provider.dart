import 'package:flutter/foundation.dart';
import '../models/user_model.dart';
import '../services/database_service.dart';
import '../utils/device_utils.dart';

class AuthProvider with ChangeNotifier {
  final DatabaseService _dbService = DatabaseService();
  
  User? _currentUser;
  bool _isLoading = false;
  String? _error;

  User? get currentUser => _currentUser;
  bool get isLoading => _isLoading;
  String? get error => _error;
  bool get isLoggedIn => _currentUser != null;

  /// Initialize - try to recover session if we had one (optional)
  /// For high security, we might require login every time.
  Future<void> initialize() async {
    // For now, require fresh login
  }

  /// Login or Register with student ID and Password
  /// Returns 0: Success, 1: Invalid Credentials, 2: New User (Need Enrollment)
  Future<int> login(String studentId, String password) async {
    _isLoading = true;
    _error = null;
    notifyListeners();

    try {
      final user = await _dbService.getUser(studentId);

      if (user != null) {
        // User exists, check password
        // In a real app, hash this password!
        if (user.password == password) {
          _currentUser = user;
          _isLoading = false;
          notifyListeners();
          return 0; // Success
        } else {
          _error = 'Invalid password';
          _isLoading = false;
          notifyListeners();
          return 1; // Error
        }
      } else {
        // User does not exist - Register them?
        // Check requirement: "On first login it ask for face registration"
        // Implicitly registration.
        
        final deviceId = await DeviceUtils.getDeviceId();
        
        // Create new user record
        final newUser = User(
          studentId: studentId,
          password: password,
          deviceId: deviceId,
          isEnrolled: false,
          name: 'Student $studentId', // Default name
          createdAt: DateTime.now().toIso8601String(),
        );

        final success = await _dbService.saveUser(newUser);
        
        if (success) {
          _currentUser = newUser;
          _isLoading = false;
          notifyListeners();
          return 2; // New User Created -> Go to Enrollment
        } else {
          _error = 'Failed to create account';
          _isLoading = false;
          notifyListeners();
          return 1;
        }
      }
    } catch (e) {
      _error = 'Login failed: $e';
      _isLoading = false;
      notifyListeners();
      return 1;
    }
  }
  
  // Update local user data after enrollment
  Future<void> reloadUser() async {
    if (_currentUser != null) {
      final updated = await _dbService.getUser(_currentUser!.studentId);
      if (updated != null) {
        _currentUser = updated;
        notifyListeners();
      }
    }
  }

  /// Logout
  Future<void> logout() async {
    _currentUser = null;
    notifyListeners();
  }

  /// Clear error
  void clearError() {
    _error = null;
    notifyListeners();
  }
}

