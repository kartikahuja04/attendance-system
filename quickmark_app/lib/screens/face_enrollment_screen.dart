import 'package:flutter/material.dart';
import 'package:flutter/foundation.dart' show kIsWeb;
import 'package:flutter/services.dart';
import 'package:camera/camera.dart';
import 'package:google_mlkit_face_detection/google_mlkit_face_detection.dart';
import 'package:permission_handler/permission_handler.dart';
import 'package:provider/provider.dart';
import '../providers/auth_provider.dart';
import '../services/liveness_service.dart';
import '../services/face_recognition_service.dart';
import '../widgets/camera_overlay.dart';
import '../utils/theme.dart';
import 'home_screen.dart';

/// Screen for enrolling user's face for the first time
class FaceEnrollmentScreen extends StatefulWidget {
  const FaceEnrollmentScreen({super.key});

  @override
  State<FaceEnrollmentScreen> createState() => _FaceEnrollmentScreenState();
}

class _FaceEnrollmentScreenState extends State<FaceEnrollmentScreen> with WidgetsBindingObserver {
  CameraController? _cameraController;
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
  
  bool _isProcessing = false;
  String _message = 'Position your face in the frame';
  double _livenessProgress = 0.0;
  bool _cameraInitialized = false;
  bool _isDisposed = false;
  bool _isEnrolling = false;

  // Liveness check status
  bool _faceDetected = false;
  LivenessTask? _currentTask;

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addObserver(this);
    _initializeServices();
  }
  
  Future<void> _initializeServices() async {
    await _faceRecognitionService.initialize();
    await _initializeCamera();
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

    // On web, skip face enrollment
    if (kIsWeb) {
      if (mounted) {
        Navigator.of(context).pushReplacement(
          MaterialPageRoute(builder: (_) => const HomeScreen()),
        );
      }
      return;
    }
    
    // Request camera permission
    final status = await Permission.camera.request();
    if (status != PermissionStatus.granted) {
      if (mounted) {
        _showErrorDialog('Camera permission is required for face enrollment');
      }
      return;
    }

    try {
      final cameras = await availableCameras();
      if (cameras.isEmpty) {
        if (mounted) {
          _showErrorDialog('No camera found on this device');
        }
        return;
      }

      // Use front camera
      final frontCamera = cameras.firstWhere(
        (camera) => camera.lensDirection == CameraLensDirection.front,
        orElse: () => cameras.first,
      );

      _cameraController = CameraController(
        frontCamera,
        ResolutionPreset.medium,
        enableAudio: false,
        imageFormatGroup: ImageFormatGroup.nv21,
      );

      await _cameraController!.initialize();

      if (mounted && !_isDisposed) {
        _livenessService.setCameraMetadata(
          frontCamera.sensorOrientation,
          frontCamera.lensDirection,
        );

        setState(() {
          _cameraInitialized = true;
        });

        await _cameraController!.startImageStream(_processImage);
      }
    } catch (e) {
      if (mounted) {
        _showErrorDialog('Failed to initialize camera: $e');
      }
    }
  }

  Future<void> _processImage(CameraImage image) async {
    if (_isProcessing || _isDisposed || _isEnrolling) return;

    _isProcessing = true;

    try {
      final result = await _livenessService.processImage(image);

      if (mounted && !_isDisposed) {
        setState(() {
          _message = result.message;
          _livenessProgress = result.progress;
          _faceDetected = result.faceDetected;
          _currentTask = result.currentTask;
        });

        if (result.passed && result.faceDetected) {
          // Liveness passed - now do face enrollment
          await _performEnrollment(image);
        }
      }
    } catch (e) {
      debugPrint('Image processing error: $e');
    } finally {
      _isProcessing = false;
    }
  }

  Future<void> _performEnrollment(CameraImage image) async {
    if (_isEnrolling) return;
    
    setState(() {
      _isEnrolling = true;
      _message = 'Enrolling your face...';
    });

    HapticFeedback.mediumImpact();
    debugPrint('=== Starting face enrollment ===');

    try {
      // Stop camera stream for enrollment
      if (_cameraController?.value.isStreamingImages ?? false) {
        await _cameraController!.stopImageStream();
      }
      debugPrint('Camera stream stopped');

      // Detect face in the current image
      final inputImage = _convertCameraImage(image);
      if (inputImage == null) {
        debugPrint('ERROR: Failed to convert camera image');
        _handleEnrollmentError('Failed to process image');
        return;
      }
      debugPrint('Camera image converted successfully');

      final faces = await _faceDetector.processImage(inputImage);
      debugPrint('Faces detected: ${faces.length}');
      
      if (faces.isEmpty) {
        debugPrint('ERROR: No faces detected');
        _handleEnrollmentError('No face detected. Please try again.');
        return;
      }

      final face = faces.first;
      debugPrint('Face bounding box: ${face.boundingBox}');
      debugPrint('Face landmarks count: ${face.landmarks.length}');
      
      // Get current user ID
      final authProvider = Provider.of<AuthProvider>(context, listen: false);
      final studentId = authProvider.currentUser?.studentId;
      
      if (studentId == null) {
        _handleEnrollmentError('Validation error: No active user session');
        return;
      }

      final result = await _faceRecognitionService.enrollFace(image, face, studentId);
      debugPrint('Enrollment result - recognized: ${result.recognized}, similarity: ${result.similarity}');
      debugPrint('Enrollment message: ${result.message}');

      if (result.recognized) {
        // Reload user to get updated enrollment status
        await authProvider.reloadUser();
        
        HapticFeedback.heavyImpact();
        debugPrint('=== Face enrollment SUCCESS ===');
        
        if (mounted) {
          setState(() {
            _message = 'Face enrolled successfully!';
          });

          await Future.delayed(const Duration(milliseconds: 1000));

          if (mounted) {
            Navigator.of(context).pushReplacement(
              MaterialPageRoute(builder: (_) => const HomeScreen()),
            );
          }
        }
      } else {
        debugPrint('=== Face enrollment FAILED: ${result.message} ===');
        _handleEnrollmentError(result.message);
      }
    } catch (e) {
      debugPrint('=== Face enrollment ERROR: $e ===');
      _handleEnrollmentError('Enrollment failed: $e');
    }
  }

  void _handleEnrollmentError(String message) {
    if (mounted) {
      setState(() {
        _isEnrolling = false;
        _message = message;
      });
      
      _livenessService.reset();
      
      // Restart camera stream
      Future.delayed(const Duration(seconds: 2), () {
        if (mounted && !_isDisposed && _cameraController != null) {
          _cameraController!.startImageStream(_processImage);
        }
      });
    }
  }

  InputImage? _convertCameraImage(CameraImage image) {
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

  void _showErrorDialog(String message) {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Error'),
        content: Text(message),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text('OK'),
          ),
        ],
      ),
    );
  }

  @override
  void dispose() {
    _isDisposed = true;
    WidgetsBinding.instance.removeObserver(this);
    _cameraController?.dispose();
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
          if (_cameraInitialized && _cameraController != null)
            SizedBox.expand(
              child: CameraPreview(_cameraController!),
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
          if (_cameraInitialized)
            CameraOverlay(
              message: _message,
              progress: _livenessProgress,
              showProgress: true,
              faceDetected: _faceDetected,
              currentTask: _currentTask,
              isQrMode: false,
              onCancel: () => Navigator.of(context).pop(),
            ),

          // Loading indicator during enrollment
          if (_isEnrolling)
            Container(
              color: Colors.black54,
              child: const Center(
                child: Column(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    CircularProgressIndicator(
                      valueColor: AlwaysStoppedAnimation<Color>(Colors.white),
                    ),
                    SizedBox(height: 16),
                    Text(
                      'Enrolling your face...',
                      style: TextStyle(color: Colors.white, fontSize: 16),
                    ),
                  ],
                ),
              ),
            ),
        ],
      ),
    );
  }
}
