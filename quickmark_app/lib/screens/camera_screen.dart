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
import '../services/face_recognition_service.dart';
import 'package:google_mlkit_face_detection/google_mlkit_face_detection.dart';
import '../widgets/camera_overlay.dart';
import '../utils/constants.dart';
import '../utils/theme.dart';
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
  final FaceRecognitionService _faceRecognitionService = FaceRecognitionService();
  final FaceDetector _faceDetector = FaceDetector(
    options: FaceDetectorOptions(
      enableContours: false,
      enableClassification: true,
      enableLandmarks: true,
      enableTracking: true,
      performanceMode: FaceDetectorMode.fast,
    ),
  );
  bool _isVerifyingFace = false;
  
  CameraMode _mode = CameraMode.liveness;
  bool _isProcessing = false;
  String _message = 'Position your face in the frame';
  double _livenessProgress = 0.0;
  bool _faceDetected = false;
  bool _cameraInitialized = false;
  bool _isDisposed = false;

  LivenessTask? _currentTask;
  int _currentTaskNumber = 0;
  int _totalTasks = 3;

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addObserver(this);
    _initializeCamera();
  }

  @override
  void didChangeAppLifecycleState(AppLifecycleState state) {
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
          _livenessProgress = result.progress;
          _faceDetected = result.faceDetected;
          _currentTask = result.currentTask;
          _currentTaskNumber = result.currentTaskNumber;
          _totalTasks = result.totalTasks;
        });

        if (result.passed && !_isVerifyingFace) {
          // Liveness passed - now verify face identity
          _isVerifyingFace = true;
          setState(() {
            _message = 'Verifying your identity...';
          });
          
          await _verifyFaceAndProceed(image);
        }
      }
    } catch (e) {
      debugPrint('Image processing error: $e');
    } finally {
      _isProcessing = false;
    }
  }

  /// Verify face matches enrolled face before proceeding
  Future<void> _verifyFaceAndProceed(CameraImage image) async {
    try {
      // Get current user ID
      final authProvider = Provider.of<AuthProvider>(context, listen: false);
      final studentId = authProvider.currentUser?.studentId;

      if (studentId == null) {
         _handleVerificationError('User not authenticated');
         return;
      }

      // Check if face is enrolled using studentId
      final isEnrolled = await _faceRecognitionService.isFaceEnrolled(studentId);
      if (!isEnrolled) {
        // No face enrolled - proceed with just liveness (fallback)
        HapticFeedback.mediumImpact();
        await Future.delayed(const Duration(milliseconds: 300));
        await _switchToQrMode();
        return;
      }

      // Convert camera image to input image for face detection
      final inputImage = _convertToInputImage(image);
      if (inputImage == null) {
        _handleVerificationError('Failed to process image');
        return;
      }

      // Detect face
      final faces = await _faceDetector.processImage(inputImage);
      if (faces.isEmpty) {
        _handleVerificationError('No face detected. Please try again.');
        return;
      }

      // Verify face
      final face = faces.first;
      
      if (studentId == null) {
         _handleVerificationError('User not authenticated');
         return;
      }

      final result = await _faceRecognitionService.verifyFace(image, face, studentId);

      if (result.recognized) {
        // Face verified - switch to QR mode
        HapticFeedback.heavyImpact();
        setState(() {
          _message = 'Identity verified! Switching to QR scanner...';
        });
        await Future.delayed(const Duration(milliseconds: 500));
        await _switchToQrMode();
      } else {
        _showError('Face verification failed: ${result.message}', 'face_mismatch');
      }
    } catch (e) {
      debugPrint('Face verification error: $e');
      _handleVerificationError('Verification failed: $e');
    }
  }

  void _handleVerificationError(String message) {
    if (mounted) {
      setState(() {
        _isVerifyingFace = false;
        _message = message;
      });
      _livenessService.reset();
    }
  }

  InputImage? _convertToInputImage(CameraImage image) {
    try {
      final WriteBuffer allBytes = WriteBuffer();
      for (final Plane plane in image.planes) {
        allBytes.putUint8List(plane.bytes);
      }
      final bytes = allBytes.done().buffer.asUint8List();

      final inputImageData = InputImageMetadata(
        size: Size(image.width.toDouble(), image.height.toDouble()),
        rotation: InputImageRotation.rotation0deg,
        format: InputImageFormat.nv21,
        bytesPerRow: image.planes.first.bytesPerRow,
      );

      return InputImage.fromBytes(
        bytes: bytes,
        metadata: inputImageData,
      );
    } catch (e) {
      return null;
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
    _faceDetector.close();
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
              currentTask: _currentTask,
              isQrMode: _mode == CameraMode.qrScanning,
              onCancel: () => Navigator.of(context).pop(),
              currentTaskNumber: _currentTaskNumber,
              totalTasks: _totalTasks,
            ),

          // Mode Indicator
          Positioned(
            top: 50,
            right: 20,
            child: Container(
              padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 8),
              decoration: BoxDecoration(
                color: _mode == CameraMode.liveness
                    ? AppTheme.primaryColor
                    : AppTheme.successColor,
                borderRadius: BorderRadius.circular(8),
              ),
              child: Row(
                mainAxisSize: MainAxisSize.min,
                children: [
                  Icon(
                    _mode == CameraMode.liveness
                        ? Icons.face
                        : Icons.qr_code_scanner,
                    color: Colors.white,
                    size: 16,
                  ),
                  const SizedBox(width: 6),
                  Text(
                    _mode == CameraMode.liveness
                        ? 'Liveness Check'
                        : 'QR Scanning',
                    style: const TextStyle(
                      color: Colors.white,
                      fontSize: 13,
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

