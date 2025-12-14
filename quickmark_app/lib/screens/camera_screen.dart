import 'package:flutter/material.dart';
import 'package:flutter/foundation.dart' show kIsWeb;
import 'package:flutter/services.dart';
import 'package:camera/camera.dart';
import 'package:mobile_scanner/mobile_scanner.dart';
import 'package:provider/provider.dart';
import 'package:permission_handler/permission_handler.dart';
import '../providers/auth_provider.dart';
import '../providers/attendance_provider.dart';
import '../services/liveness_service.dart';
import '../widgets/camera_overlay.dart';
import '../utils/constants.dart';
import 'success_screen.dart';
import 'error_screen.dart';

enum CameraMode { liveness, qrScanning }

class CameraScreen extends StatefulWidget {
  const CameraScreen({super.key});

  @override
  State<CameraScreen> createState() => _CameraScreenState();
}

class _CameraScreenState extends State<CameraScreen> with WidgetsBindingObserver {
  CameraController? _cameraController;
  MobileScannerController? _qrController;
  final LivenessService _livenessService = LivenessService();
  
  CameraMode _mode = CameraMode.liveness;
  bool _isProcessing = false;
  String _message = 'Position your face in the frame';
  double _livenessProgress = 0.0;
  bool _cameraInitialized = false;
  bool _isDisposed = false;

  // Liveness check status
  bool _faceDetected = false;
  bool _blinkDetected = false;
  bool _headMoved = false;

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addObserver(this);
    _initializeCamera();
  }

  @override
  void didChangeAppLifecycleState(AppLifecycleState state) {
    // Handle app lifecycle changes
    if (_cameraController == null || !_cameraController!.value.isInitialized) {
      return;
    }

    if (state == AppLifecycleState.inactive) {
      _cameraController?.dispose();
    } else if (state == AppLifecycleState.resumed) {
      _initializeCamera();
    }
  }

  Future<void> _initializeCamera() async {
    if (_isDisposed) return;

    // On web, skip liveness detection and go straight to QR scanning
    if (kIsWeb) {
      await _switchToQrMode();
      return;
    }
    
    // Request camera permission
    final status = await Permission.camera.request();
    if (status != PermissionStatus.granted) {
      if (mounted) {
        _showError(AppConstants.errorCameraPermission, 'permission');
      }
      return;
    }

    try {
      // Get available cameras
      final cameras = await availableCameras();
      if (cameras.isEmpty) {
        if (mounted) {
          _showError('No camera found on this device', 'camera');
        }
        return;
      }

      // Use front camera for liveness detection
      final frontCamera = cameras.firstWhere(
        (camera) => camera.lensDirection == CameraLensDirection.front,
        orElse: () => cameras.first,
      );

      // Initialize camera controller
      _cameraController = CameraController(
        frontCamera,
        ResolutionPreset.medium,
        enableAudio: false,
        imageFormatGroup: ImageFormatGroup.nv21,
      );

      await _cameraController!.initialize();

      if (mounted && !_isDisposed) {
        // Set camera metadata for liveness service
        _livenessService.setCameraMetadata(
          frontCamera.sensorOrientation,
          frontCamera.lensDirection,
        );

        setState(() {
          _cameraInitialized = true;
        });

        // Start image stream for liveness detection
        await _cameraController!.startImageStream(_processImage);
      }
    } catch (e) {
      if (mounted) {
        _showError('Failed to initialize camera: $e', 'camera');
      }
    }
  }

  Future<void> _processImage(CameraImage image) async {
    if (_isProcessing || _mode != CameraMode.liveness || _isDisposed) return;

    _isProcessing = true;

    try {
      final result = await _livenessService.processImage(image);

      if (mounted && !_isDisposed) {
        setState(() {
          _message = result.message;
          _livenessProgress = result.score;
          _faceDetected = result.faceDetected;
          _blinkDetected = result.blinkDetected;
          _headMoved = result.headMovementDetected;
        });

        if (result.passed) {
          // Haptic feedback on liveness pass
          HapticFeedback.mediumImpact();
          
          // Small delay to show success message
          await Future.delayed(const Duration(milliseconds: 500));
          
          // Liveness check passed - switch to QR scanning mode
          await _switchToQrMode();
        }
      }
    } catch (e) {
      // Ignore processing errors
      debugPrint('Image processing error: $e');
    } finally {
      _isProcessing = false;
    }
  }

  Future<void> _switchToQrMode() async {
    if (_isDisposed) return;

    // Stop camera stream
    if (_cameraController != null) {
      try {
        if (_cameraController!.value.isStreamingImages) {
          await _cameraController!.stopImageStream();
        }
        await _cameraController!.dispose();
      } catch (e) {
        debugPrint('Error disposing camera: $e');
      }
      _cameraController = null;
    }

    // Initialize QR scanner
    _qrController = MobileScannerController(
      detectionSpeed: DetectionSpeed.normal,
      facing: CameraFacing.back,
    );

    if (mounted && !_isDisposed) {
      // Haptic feedback when switching modes
      HapticFeedback.lightImpact();
      
      setState(() {
        _mode = CameraMode.qrScanning;
        _message = 'Scan the QR code displayed by your teacher';
        _cameraInitialized = true;
      });
    }
  }

  Future<void> _handleQrDetection(BarcodeCapture capture) async {
    if (_isProcessing || _isDisposed) return;

    final barcodes = capture.barcodes;
    if (barcodes.isEmpty) return;

    final qrData = barcodes.first.rawValue;
    if (qrData == null || qrData.isEmpty) return;

    _isProcessing = true;

    // Haptic feedback on QR detection
    HapticFeedback.heavyImpact();

    // Extract token from QR code
    final attendanceProvider = Provider.of<AttendanceProvider>(context, listen: false);
    final token = attendanceProvider.extractToken(qrData);

    if (token == null) {
      _showError(AppConstants.errorInvalidQr, 'invalid_qr');
      return;
    }

    // Get user info
    final authProvider = Provider.of<AuthProvider>(context, listen: false);
    final user = authProvider.currentUser;

    if (user == null) {
      _showError('User not logged in', 'auth');
      return;
    }

    // Show loading
    if (mounted) {
      setState(() {
        _message = 'Submitting attendance...';
      });
    }

    // Submit attendance
    final success = await attendanceProvider.submitAttendance(
      token: token,
      studentId: user.studentId,
      deviceId: user.deviceId,
      livenessScore: _livenessProgress,
    );

    if (!mounted || _isDisposed) return;

    if (success) {
      // Success haptic
      HapticFeedback.heavyImpact();
      
      // Navigate to success screen
      Navigator.of(context).pushReplacement(
        MaterialPageRoute(
          builder: (_) => SuccessScreen(
            sessionId: token.split(':').first,
            studentId: user.studentId,
            timestamp: DateTime.now(),
          ),
        ),
      );
    } else {
      // Determine error type
      final error = attendanceProvider.error ?? 'Unknown error';
      String? errorType;
      
      if (error.contains('expired')) {
        errorType = 'expired';
      } else if (error.contains('already marked') || error.contains('duplicate')) {
        errorType = 'already_marked';
      } else if (error.contains('network') || error.contains('Network')) {
        errorType = 'network';
      }

      _showError(error, errorType);
    }
  }

  void _showError(String message, String? errorType) {
    Navigator.of(context).pushReplacement(
      MaterialPageRoute(
        builder: (_) => ErrorScreen(
          errorMessage: message,
          errorType: errorType,
        ),
      ),
    );
  }

  @override
  void dispose() {
    _isDisposed = true;
    WidgetsBinding.instance.removeObserver(this);
    _cameraController?.dispose();
    _qrController?.dispose();
    _livenessService.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.black,
      body: Stack(
        children: [
          // Camera Preview
          if (_mode == CameraMode.liveness && _cameraInitialized && _cameraController != null)
            SizedBox.expand(
              child: CameraPreview(_cameraController!),
            )
          else if (_mode == CameraMode.qrScanning && _qrController != null)
            SizedBox.expand(
              child: MobileScanner(
                controller: _qrController,
                onDetect: _handleQrDetection,
              ),
            )
          else
            const Center(
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  CircularProgressIndicator(
                    valueColor: AlwaysStoppedAnimation<Color>(Colors.white),
                  ),
                  SizedBox(height: 16),
                  Text(
                    'Initializing camera...',
                    style: TextStyle(color: Colors.white),
                  ),
                ],
              ),
            ),

          // Overlay
          if (_cameraInitialized || _mode == CameraMode.qrScanning)
            CameraOverlay(
              message: _message,
              progress: _livenessProgress,
              showProgress: _mode == CameraMode.liveness,
              faceDetected: _faceDetected,
              blinkDetected: _blinkDetected,
              headMoved: _headMoved,
              isQrMode: _mode == CameraMode.qrScanning,
              onCancel: () => Navigator.of(context).pop(),
            ),

          // Mode Indicator
          Positioned(
            top: 50,
            right: 20,
            child: Container(
              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
              decoration: BoxDecoration(
                color: _mode == CameraMode.liveness
                    ? Colors.blue.withOpacity(0.9)
                    : Colors.green.withOpacity(0.9),
                borderRadius: BorderRadius.circular(20),
                boxShadow: [
                  BoxShadow(
                    color: Colors.black.withOpacity(0.3),
                    blurRadius: 8,
                    offset: const Offset(0, 2),
                  ),
                ],
              ),
              child: Row(
                mainAxisSize: MainAxisSize.min,
                children: [
                  Icon(
                    _mode == CameraMode.liveness
                        ? Icons.face
                        : Icons.qr_code_scanner,
                    color: Colors.white,
                    size: 18,
                  ),
                  const SizedBox(width: 8),
                  Text(
                    _mode == CameraMode.liveness
                        ? 'Liveness Check'
                        : 'QR Scanning',
                    style: const TextStyle(
                      color: Colors.white,
                      fontSize: 14,
                      fontWeight: FontWeight.w600,
                    ),
                  ),
                ],
              ),
            ),
          ),

          // Back button
          Positioned(
            top: 50,
            left: 20,
            child: GestureDetector(
              onTap: () => Navigator.of(context).pop(),
              child: Container(
                padding: const EdgeInsets.all(12),
                decoration: BoxDecoration(
                  color: Colors.black.withOpacity(0.5),
                  shape: BoxShape.circle,
                ),
                child: const Icon(
                  Icons.arrow_back,
                  color: Colors.white,
                  size: 24,
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }
}

