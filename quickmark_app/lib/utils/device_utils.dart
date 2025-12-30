import 'dart:io';
import 'package:device_info_plus/device_info_plus.dart';
import 'package:flutter/foundation.dart';

class DeviceUtils {
  static final DeviceInfoPlugin _deviceInfo = DeviceInfoPlugin();

  /// Generate a unique device ID based on device information
  static Future<String> generateDeviceId() async {
    try {
      if (kIsWeb) {
        // Web platform
        final webInfo = await _deviceInfo.webBrowserInfo;
        return 'web_${webInfo.userAgent.hashCode}';
      } else if (Platform.isAndroid) {
        // Android platform
        final androidInfo = await _deviceInfo.androidInfo;
        return 'android_${androidInfo.id}';
      } else if (Platform.isIOS) {
        // iOS platform
        final iosInfo = await _deviceInfo.iosInfo;
        return 'ios_${iosInfo.identifierForVendor ?? "unknown"}';
      } else {
        // Fallback for other platforms
        return 'device_${DateTime.now().millisecondsSinceEpoch}';
      }
    } catch (e) {
      // Fallback: generate timestamp-based ID
      return 'device_${DateTime.now().millisecondsSinceEpoch}';
    }
  }

  /// Get device model name
  static Future<String> getDeviceModel() async {
    try {
      if (Platform.isAndroid) {
        final androidInfo = await _deviceInfo.androidInfo;
        return '${androidInfo.manufacturer} ${androidInfo.model}';
      } else if (Platform.isIOS) {
        final iosInfo = await _deviceInfo.iosInfo;
        return iosInfo.model;
      }
      return 'Unknown Device';
    } catch (e) {
      return 'Unknown Device';
    }
  }

  /// Get OS version
  static Future<String> getOsVersion() async {
    try {
      if (Platform.isAndroid) {
        final androidInfo = await _deviceInfo.androidInfo;
        return 'Android ${androidInfo.version.release}';
      } else if (Platform.isIOS) {
        final iosInfo = await _deviceInfo.iosInfo;
        return 'iOS ${iosInfo.systemVersion}';
      }
      return 'Unknown OS';
    } catch (e) {
      return 'Unknown OS';
    }
  }
  // Alias for backward compatibility
  static Future<String> getDeviceId() => generateDeviceId();
}
