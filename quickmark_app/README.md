# QuickMark - College Attendance System

A Flutter mobile application for marking college attendance using QR codes with liveness detection.

## Features

✅ **User Authentication** - Simple login with Student ID  
✅ **Liveness Detection** - Face detection with blink and head movement verification  
✅ **QR Code Scanning** - Scan teacher-displayed QR codes  
✅ **Attendance Marking** - Automatic submission with device ID tracking  
✅ **Attendance History** - View all past attendance records  
✅ **Material 3 Design** - Modern, clean UI  
✅ **Offline Storage** - SharedPreferences for user data  

## Prerequisites

- Flutter SDK (3.x or higher)
- Android Studio / Xcode
- Android device/emulator or iOS device/simulator
- Backend server running (see backend setup)

## Installation

### 1. Install Dependencies

```bash
cd quickmark_app
flutter pub get
```

### 2. Configure Backend URL

Open `lib/utils/constants.dart` and update the API base URL:

```dart
static const String apiBaseUrl = 'https://your-ngrok-url.ngrok.io';
```

**For local testing:**
- Android Emulator: Use `http://10.0.2.2:8000`
- iOS Simulator: Use `http://localhost:8000`
- Physical Device: Use your computer's IP address or ngrok URL

### 3. Run the App

```bash
# For Android
flutter run

# For iOS
flutter run -d ios

# For specific device
flutter devices
flutter run -d <device-id>
```

## Backend Setup

Make sure your backend server is running:

```bash
cd ../
python run.py
```

Then expose it via ngrok (for physical devices):

```bash
ngrok http 8000
```

Copy the ngrok URL and update `constants.dart`.

## Project Structure

```
lib/
├── main.dart                 # App entry point
├── models/                   # Data models
│   ├── user_model.dart
│   ├── attendance_record.dart
│   └── session_model.dart
├── providers/                # State management
│   ├── auth_provider.dart
│   └── attendance_provider.dart
├── screens/                  # UI screens
│   ├── splash_screen.dart
│   ├── login_screen.dart
│   ├── home_screen.dart
│   ├── camera_screen.dart
│   ├── success_screen.dart
│   ├── error_screen.dart
│   └── history_screen.dart
├── services/                 # Business logic
│   ├── api_service.dart
│   ├── storage_service.dart
│   └── liveness_service.dart
├── utils/                    # Utilities
│   ├── constants.dart
│   ├── device_utils.dart
│   └── theme.dart
└── widgets/                  # Reusable widgets
    ├── custom_button.dart
    ├── loading_indicator.dart
    └── camera_overlay.dart
```

## Usage Flow

1. **Login** - Enter your Student ID
2. **Home Screen** - Choose "Scan QR Code" or "View History"
3. **Liveness Detection** - Position face in frame, blink, and turn head slightly
4. **QR Scanning** - Once liveness passes, scan the QR code from teacher's screen
5. **Success** - Attendance marked automatically
6. **History** - View all your attendance records

## Liveness Detection

The app uses Google MLKit Face Detection to verify:
- ✅ Face detected continuously for 1.5 seconds
- ✅ Blink detected (eyes close and open)
- ✅ Head movement (rotation left/right)

**Liveness Score Calculation:**
- Face Detection: 40%
- Blink Detection: 30%
- Head Movement: 30%
- **Pass Threshold: 70%**

## Permissions

### Android
- Camera
- Internet

### iOS
- Camera (NSCameraUsageDescription)

Permissions are requested at runtime when needed.

## Dependencies

```yaml
dependencies:
  provider: ^6.1.1                    # State management
  shared_preferences: ^2.2.2          # Local storage
  http: ^1.1.2                        # Networking
  mobile_scanner: ^3.5.5              # QR scanning
  google_mlkit_face_detection: ^0.9.0 # Face detection
  camera: ^0.10.5+5                   # Camera access
  intl: ^0.18.1                       # Date formatting
  device_info_plus: ^9.1.1            # Device ID
  permission_handler: ^11.1.0         # Permissions
```

## Troubleshooting

### Camera not working
- Check permissions in device settings
- Ensure camera hardware is available
- Try restarting the app

### QR code not scanning
- Ensure good lighting
- Hold phone steady
- Make sure QR code is fully visible

### Network errors
- Check backend URL in `constants.dart`
- Verify backend server is running
- Check internet connection
- For Android emulator, use `10.0.2.2` instead of `localhost`

### Liveness detection failing
- Ensure good lighting
- Position face clearly in frame
- Blink naturally
- Turn head slowly left/right

## Building for Release

### Android APK
```bash
flutter build apk --release
```

### Android App Bundle
```bash
flutter build appbundle --release
```

### iOS
```bash
flutter build ios --release
```

## Configuration

### Change App Name
- Android: `android/app/src/main/AndroidManifest.xml`
- iOS: `ios/Runner/Info.plist`

### Change App Icon
Replace icons in:
- Android: `android/app/src/main/res/`
- iOS: `ios/Runner/Assets.xcassets/AppIcon.appiconset/`

Or use `flutter_launcher_icons` package.

## Security Notes

- Device ID is generated once and stored locally
- Student ID is stored in SharedPreferences
- All API calls use HTTPS (in production)
- Liveness detection prevents photo/video spoofing

## Future Enhancements

- [ ] Biometric authentication
- [ ] Offline attendance marking with sync
- [ ] Push notifications for new sessions
- [ ] Dark mode support
- [ ] Multi-language support
- [ ] Advanced liveness detection (3D depth)

## Support

For issues or questions:
1. Check the troubleshooting section
2. Review backend logs
3. Check Flutter doctor: `flutter doctor`

## License

This project is for educational purposes.

---

**Built with Flutter 💙**
