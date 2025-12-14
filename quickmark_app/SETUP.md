# QuickMark Setup Guide

## Quick Start (5 Minutes)

### Step 1: Install Dependencies
```bash
cd c:\Users\karti\OneDrive\Documents\attendance-system\quickmark_app
flutter pub get
```

### Step 2: Start Backend Server
```bash
# In a new terminal
cd c:\Users\karti\OneDrive\Documents\attendance-system
python run.py
```

### Step 3: Expose Backend with ngrok
```bash
# In another terminal
ngrok http 8000
```

You'll see output like:
```
Forwarding   https://abc123.ngrok.io -> http://localhost:8000
```

### Step 4: Update API URL
Open `lib/utils/constants.dart` and replace:
```dart
static const String apiBaseUrl = 'https://your-ngrok-url.ngrok.io';
```

With your ngrok URL:
```dart
static const String apiBaseUrl = 'https://abc123.ngrok.io';
```

### Step 5: Run the App
```bash
# Connect your Android phone or start emulator
flutter run
```

## Testing the Complete Flow

### 1. Login
- Open the app
- Enter any Student ID (e.g., "STU001")
- Tap Login

### 2. Mark Attendance

#### On Teacher's Computer:
1. Go to `http://localhost:8000/login`
2. Login with `admin` / `admin123`
3. Create a new session
4. Display the QR code on screen

#### On Student's Phone:
1. Tap "Scan QR Code"
2. **Liveness Detection Phase:**
   - Position your face in the oval frame
   - Blink your eyes
   - Turn your head slightly left/right
   - Wait for progress to reach 100%
3. **QR Scanning Phase:**
   - Point camera at the QR code on teacher's screen
   - Attendance will be marked automatically
4. See success screen with timestamp

### 3. View History
- Go back to home screen
- Tap "Attendance History"
- See all your attendance records

## Troubleshooting

### "Camera permission denied"
**Solution:** Go to phone Settings → Apps → QuickMark → Permissions → Enable Camera

### "Network error"
**Solution:** 
- Make sure backend is running
- Check ngrok URL is correct in `constants.dart`
- Verify phone has internet connection

### "QR code expired"
**Solution:** 
- QR codes expire after 30 seconds
- Ask teacher to refresh the QR code
- Scan the new QR code

### Liveness detection stuck
**Solution:**
- Ensure good lighting
- Remove glasses if wearing
- Blink naturally (don't force it)
- Turn head slowly (not too fast)

### Android Emulator camera not working
**Solution:**
- Use a physical device for best results
- Or configure emulator camera in AVD settings

## Development Tips

### Hot Reload
While app is running, make code changes and press `r` in terminal for hot reload.

### Debug Mode
The app runs in debug mode by default. You'll see a debug banner.

### View Logs
```bash
flutter logs
```

### Clear App Data
```bash
flutter clean
flutter pub get
flutter run
```

## Backend API Endpoints Used

- `GET /api/health` - Health check
- `GET /mark/{token}?student_id={id}` - Mark attendance
- `GET /api/attendance/history/{student_id}` - Get history (if implemented)

## Next Steps

1. **Test with multiple students** - Login with different Student IDs
2. **Test error scenarios** - Try scanning expired QR, scanning twice
3. **Customize** - Change colors in `utils/theme.dart`
4. **Deploy** - Build release APK for distribution

## Building Release APK

```bash
flutter build apk --release
```

APK will be at: `build/app/outputs/flutter-apk/app-release.apk`

Transfer this to your phone and install!

---

**Need Help?** Check the main README.md for more details.
