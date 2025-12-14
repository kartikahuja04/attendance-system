import 'dart:io';
import 'dart:ui';
import 'package:camera/camera.dart';
import 'package:google_mlkit_face_detection/google_mlkit_face_detection.dart';
import 'package:flutter/foundation.dart';
import 'package:flutter/services.dart';
import '../utils/constants.dart';

class LivenessResult {
  final bool passed;
  final double score;
  final String message;
  final bool faceDetected;
  final bool blinkDetected;
  final bool headMovementDetected;

  LivenessResult({
    required this.passed,
    required this.score,
    required this.message,
    this.faceDetected = false,
    this.blinkDetected = false,
    this.headMovementDetected = false,
  });
}

class LivenessService {
  final FaceDetector _faceDetector = FaceDetector(
    options: FaceDetectorOptions(
      enableContours: false,
      enableClassification: true, // Enable eye open probability
      enableLandmarks: true,
      enableTracking: true,
      performanceMode: FaceDetectorMode.fast,
    ),
  );

  // Camera metadata for image conversion
  int _sensorOrientation = 0;
  CameraLensDirection _lensDirection = CameraLensDirection.front;

  // Tracking variables
  bool _faceDetectedContinuously = false;
  DateTime? _faceDetectionStartTime;
  bool _blinkDetected = false;
  bool _headMovementDetected = false;
  
  // Eye state tracking for blink detection
  bool _eyesWereOpen = false;
  bool _eyesWereClosed = false;
  
  // Head position tracking
  double? _initialHeadRotation;
  double? _maxHeadRotation;

  /// Set camera metadata for proper image orientation
  void setCameraMetadata(int sensorOrientation, CameraLensDirection lensDirection) {
    _sensorOrientation = sensorOrientation;
    _lensDirection = lensDirection;
  }

  /// Process camera image for face detection and liveness checks
  Future<LivenessResult> processImage(CameraImage image) async {
    try {
      // Skip processing on web
      if (kIsWeb) {
        return LivenessResult(
          passed: true,
          score: 1.0,
          message: 'Liveness check skipped on web',
        );
      }

      // Convert CameraImage to InputImage
      final inputImage = _convertCameraImage(image);
      if (inputImage == null) {
        return LivenessResult(
          passed: false,
          score: 0.0,
          message: 'Position your face in the frame',
        );
      }

      // Detect faces
      final faces = await _faceDetector.processImage(inputImage);

      if (faces.isEmpty) {
        // No face detected - reset tracking
        _resetTracking();
        return LivenessResult(
          passed: false,
          score: 0.0,
          message: 'No face detected. Please position your face in the frame.',
          faceDetected: false,
        );
      }

      // Get the first detected face
      final face = faces.first;

      // Check if face is detected continuously
      if (!_faceDetectedContinuously) {
        _faceDetectionStartTime = DateTime.now();
        _faceDetectedContinuously = true;
      }

      final detectionDuration = DateTime.now().difference(_faceDetectionStartTime!);

      // Perform liveness checks
      _checkBlink(face);
      _checkHeadMovement(face);

      // Calculate liveness score
      final score = _calculateLivenessScore(detectionDuration);

      // Check if all conditions are met
      final passed = score >= AppConstants.livenessPassThreshold;

      String message = _generateMessage();

      return LivenessResult(
        passed: passed,
        score: score,
        message: message,
        faceDetected: true,
        blinkDetected: _blinkDetected,
        headMovementDetected: _headMovementDetected,
      );
    } catch (e) {
      debugPrint('Liveness processing error: $e');
      return LivenessResult(
        passed: false,
        score: 0.0,
        message: 'Processing... Keep your face visible',
      );
    }
  }

  /// Check for blink detection
  void _checkBlink(Face face) {
    if (_blinkDetected) return; // Already detected

    final leftEyeOpen = face.leftEyeOpenProbability ?? 1.0;
    final rightEyeOpen = face.rightEyeOpenProbability ?? 1.0;

    // Both eyes open
    if (leftEyeOpen > AppConstants.eyeOpenThreshold &&
        rightEyeOpen > AppConstants.eyeOpenThreshold) {
      _eyesWereOpen = true;
    }

    // Both eyes closed
    if (leftEyeOpen < AppConstants.blinkThreshold &&
        rightEyeOpen < AppConstants.blinkThreshold) {
      if (_eyesWereOpen) {
        _eyesWereClosed = true;
      }
    }

    // Blink complete: eyes were open, then closed, then open again
    if (_eyesWereOpen && _eyesWereClosed &&
        leftEyeOpen > AppConstants.eyeOpenThreshold &&
        rightEyeOpen > AppConstants.eyeOpenThreshold) {
      _blinkDetected = true;
    }
  }

  /// Check for head movement (rotation)
  void _checkHeadMovement(Face face) {
    if (_headMovementDetected) return; // Already detected

    final headRotationY = face.headEulerAngleY ?? 0.0;

    if (_initialHeadRotation == null) {
      _initialHeadRotation = headRotationY;
      _maxHeadRotation = headRotationY;
    } else {
      // Track maximum rotation
      if ((headRotationY - _initialHeadRotation!).abs() >
          (_maxHeadRotation! - _initialHeadRotation!).abs()) {
        _maxHeadRotation = headRotationY;
      }

      // Check if head moved beyond threshold
      if ((_maxHeadRotation! - _initialHeadRotation!).abs() >
          AppConstants.headRotationThreshold) {
        _headMovementDetected = true;
      }
    }
  }

  /// Calculate liveness score based on checks
  double _calculateLivenessScore(Duration detectionDuration) {
    double score = 0.0;

    // Face detected continuously (40% weight)
    if (detectionDuration.inMilliseconds >= AppConstants.faceDetectionDurationMs) {
      score += 0.4;
    } else {
      score += 0.4 * (detectionDuration.inMilliseconds / AppConstants.faceDetectionDurationMs);
    }

    // Blink detected (30% weight)
    if (_blinkDetected) {
      score += 0.3;
    }

    // Head movement detected (30% weight)
    if (_headMovementDetected) {
      score += 0.3;
    }

    return score;
  }

  /// Generate user-friendly message
  String _generateMessage() {
    if (!_blinkDetected && !_headMovementDetected) {
      return 'Please blink and turn your head slightly';
    } else if (!_blinkDetected) {
      return 'Good! Now please blink your eyes';
    } else if (!_headMovementDetected) {
      return 'Great! Now turn your head slightly';
    } else {
      return 'Liveness verified! Switching to QR scanner...';
    }
  }

  /// Reset tracking variables
  void _resetTracking() {
    _faceDetectedContinuously = false;
    _faceDetectionStartTime = null;
    _blinkDetected = false;
    _headMovementDetected = false;
    _eyesWereOpen = false;
    _eyesWereClosed = false;
    _initialHeadRotation = null;
    _maxHeadRotation = null;
  }

  /// Reset for new session
  void reset() {
    _resetTracking();
  }

  /// Convert CameraImage to InputImage for MLKit
  /// This is the critical method that was missing - properly converts camera frames
  InputImage? _convertCameraImage(CameraImage image) {
    try {
      // Get image rotation based on sensor orientation and lens direction
      final imageRotation = _getImageRotation();
      if (imageRotation == null) return null;

      // Get the image format
      final format = _getInputImageFormat(image.format.group);
      if (format == null) return null;

      // For NV21 format (Android), we need to handle planes correctly
      if (image.planes.isEmpty) return null;

      // Concatenate all planes into a single byte array
      final bytes = _concatenatePlanes(image.planes);
      if (bytes == null) return null;

      // Create InputImage from bytes
      final inputImageData = InputImageMetadata(
        size: Size(image.width.toDouble(), image.height.toDouble()),
        rotation: imageRotation,
        format: format,
        bytesPerRow: image.planes.first.bytesPerRow,
      );

      return InputImage.fromBytes(
        bytes: bytes,
        metadata: inputImageData,
      );
    } catch (e) {
      debugPrint('Error converting camera image: $e');
      return null;
    }
  }

  /// Get InputImageRotation based on camera sensor orientation
  InputImageRotation? _getImageRotation() {
    // Calculate rotation based on sensor orientation and device orientation
    // For front camera, we need to flip the rotation
    int rotationCompensation = _sensorOrientation;
    
    if (_lensDirection == CameraLensDirection.front) {
      // Front camera requires different rotation handling
      rotationCompensation = (360 - _sensorOrientation) % 360;
    }

    switch (rotationCompensation) {
      case 0:
        return InputImageRotation.rotation0deg;
      case 90:
        return InputImageRotation.rotation90deg;
      case 180:
        return InputImageRotation.rotation180deg;
      case 270:
        return InputImageRotation.rotation270deg;
      default:
        return InputImageRotation.rotation0deg;
    }
  }

  /// Get InputImageFormat from camera image format
  InputImageFormat? _getInputImageFormat(ImageFormatGroup formatGroup) {
    switch (formatGroup) {
      case ImageFormatGroup.nv21:
        return InputImageFormat.nv21;
      case ImageFormatGroup.yuv420:
        return InputImageFormat.yuv420;
      case ImageFormatGroup.bgra8888:
        return InputImageFormat.bgra8888;
      default:
        // Try to use nv21 as default for Android
        if (!kIsWeb && Platform.isAndroid) {
          return InputImageFormat.nv21;
        }
        return null;
    }
  }

  /// Concatenate image planes into a single byte array
  Uint8List? _concatenatePlanes(List<Plane> planes) {
    try {
      final WriteBuffer allBytes = WriteBuffer();
      for (final Plane plane in planes) {
        allBytes.putUint8List(plane.bytes);
      }
      return allBytes.done().buffer.asUint8List();
    } catch (e) {
      debugPrint('Error concatenating planes: $e');
      return null;
    }
  }

  /// Dispose resources
  void dispose() {
    _faceDetector.close();
  }
}
