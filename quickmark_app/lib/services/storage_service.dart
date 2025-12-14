import 'package:shared_preferences/shared_preferences.dart';
import '../models/user_model.dart';
import '../utils/constants.dart';
import '../utils/device_utils.dart';

class StorageService {
  static final StorageService _instance = StorageService._internal();
  factory StorageService() => _instance;
  StorageService._internal();

  SharedPreferences? _prefs;

  /// Initialize SharedPreferences
  Future<void> init() async {
    _prefs ??= await SharedPreferences.getInstance();
  }

  /// Save user data (student ID and device ID)
  Future<bool> saveUser(User user) async {
    await init();
    final studentIdSaved =
        await _prefs!.setString(AppConstants.keyStudentId, user.studentId);
    final deviceIdSaved =
        await _prefs!.setString(AppConstants.keyDeviceId, user.deviceId);
    return studentIdSaved && deviceIdSaved;
  }

  /// Get stored user data
  Future<User?> getUser() async {
    await init();
    final studentId = _prefs!.getString(AppConstants.keyStudentId);
    final deviceId = _prefs!.getString(AppConstants.keyDeviceId);

    if (studentId != null && deviceId != null) {
      return User(studentId: studentId, deviceId: deviceId);
    }
    return null;
  }

  /// Check if user is logged in
  Future<bool> isLoggedIn() async {
    final user = await getUser();
    return user != null;
  }

  /// Clear user data (logout)
  Future<bool> clearUser() async {
    await init();
    final studentIdRemoved =
        await _prefs!.remove(AppConstants.keyStudentId);
    final deviceIdRemoved =
        await _prefs!.remove(AppConstants.keyDeviceId);
    return studentIdRemoved && deviceIdRemoved;
  }

  /// Get or generate device ID
  Future<String> getOrGenerateDeviceId() async {
    await init();
    String? deviceId = _prefs!.getString(AppConstants.keyDeviceId);
    
    if (deviceId == null) {
      // Generate new device ID
      deviceId = await DeviceUtils.generateDeviceId();
      await _prefs!.setString(AppConstants.keyDeviceId, deviceId);
    }
    
    return deviceId;
  }

  /// Check if this is first launch
  Future<bool> isFirstLaunch() async {
    await init();
    final isFirst = _prefs!.getBool(AppConstants.keyIsFirstLaunch) ?? true;
    if (isFirst) {
      await _prefs!.setBool(AppConstants.keyIsFirstLaunch, false);
    }
    return isFirst;
  }

  /// Save arbitrary string value
  Future<bool> saveString(String key, String value) async {
    await init();
    return await _prefs!.setString(key, value);
  }

  /// Get arbitrary string value
  Future<String?> getString(String key) async {
    await init();
    return _prefs!.getString(key);
  }
}
