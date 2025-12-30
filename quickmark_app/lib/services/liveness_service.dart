import 'dart:io';
import 'dart:math';
import 'package:camera/camera.dart';
import 'package:flutter/foundation.dart';
import 'package:google_mlkit_face_mesh_detection/google_mlkit_face_mesh_detection.dart';
import 'package:flutter/services.dart';
import 'face_mesh_service.dart';

enum LivenessTask {
  BLINK,
  SMILE,
  HEAD_LEFT,
  HEAD_RIGHT,
  MOUTH_OPEN,
  EYEBROW_RAISE,
}

class LivenessResult {
  final bool passed;
  final double score;
  final String message;
  final LivenessTask? currentTask;
  final bool faceDetected;
  final double progress; // 0.0 to 1.0
  final int currentTaskNumber; // 1-based
  final int totalTasks;

  LivenessResult({
    required this.passed,
    required this.score,
    required this.message,
    this.currentTask,
    this.faceDetected = false,
    this.progress = 0.0,
    this.currentTaskNumber = 0,
    this.totalTasks = 3,
  });
}

class LivenessService {
  final FaceMeshDetector _meshDetector = FaceMeshDetector(
    option: FaceMeshDetectorOptions.faceMesh,
  );

  // Camera metadata
  int _sensorOrientation = 0;
  CameraLensDirection _lensDirection = CameraLensDirection.front;

  // Task Management
  List<LivenessTask> _tasks = [];
  int _currentTaskIndex = 0;
  bool _tasksInitialized = false;
  
  // Smoothing State
  double _prevEAR = 0.0;
  double _prevMAR = 0.0;
  double _prevHeadTurn = 0.0;
  bool _hasPrevData = false;
  
  // Baseline / Calibration
  double _neutralEAR = 0.0;
  double _neutralMAR = 0.0;
  double _neutralMouthWidth = 0.0;
  double _neutralCornerY = 0.0;
  int _calibrationFrames = 0;
  static const int CALIBRATION_FRAMES_REQUIRED = 15;
  bool _isCalibrated = false;

  // Task State Logic
  bool _eyesClosed = false; // For blink tracking
  int _blinkCount = 0;
  int _consecutiveFrames = 0; // For stability
  DateTime? _lastTaskPassTime; // For cooldown
  
  // Constants / Thresholds
  static const int STABILITY_FRAMES = 7;  // Require 7 consecutive frames (stricter)
  static const int BLINKS_REQUIRED = 2;
  static const Duration TASK_COOLDOWN = Duration(milliseconds: 500);

  void setCameraMetadata(int sensorOrientation, CameraLensDirection lensDirection) {
    _sensorOrientation = sensorOrientation;
    _lensDirection = lensDirection;
  }

  void _initTasks() {
    if (_tasksInitialized) return;
    
    final allTasks = [
      LivenessTask.BLINK,
      LivenessTask.SMILE,
      LivenessTask.HEAD_LEFT,
      LivenessTask.HEAD_RIGHT,
      LivenessTask.MOUTH_OPEN,
      LivenessTask.EYEBROW_RAISE,
    ];
    
    // Randomly select 3 discrete tasks
    allTasks.shuffle();
    _tasks = allTasks.take(3).toList();
    _currentTaskIndex = 0;
    _tasksInitialized = true;
    _resetTaskState();
  }

  void _resetTaskState() {
    _consecutiveFrames = 0;
    _eyesClosed = false;
    _blinkCount = 0;
    _hasPrevData = false; // Reset smoothing on new task
    _prevEAR = 0.0;
    _prevMAR = 0.0;
    _prevHeadTurn = 0.0;
    // Keeping smoothing is better for continuity.
  }
  
  void reset() {
    _tasksInitialized = false;
    _tasks = [];
    _currentTaskIndex = 0;
    _isCalibrated = false;
    _calibrationFrames = 0;
    _lastTaskPassTime = null;
    _resetTaskState();
  }

  /// Calculate Eye Aspect Ratio using 6-point formula
  /// EAR = (||p2-p6|| + ||p3-p5||) / (2 * ||p1-p4||)
  /// This is more accurate than simple 4-point method
  double _calculateEAR6Point(List<FaceMeshPoint> landmarks, int p1, int p2, int p3, int p4, int p5, int p6) {
    if (landmarks.length < 468) return 0.0;
    
    final point1 = landmarks[p1];
    final point2 = landmarks[p2];
    final point3 = landmarks[p3];
    final point4 = landmarks[p4];
    final point5 = landmarks[p5];
    final point6 = landmarks[p6];
    
    // Vertical distances
    final vertical1 = sqrt(pow(point2.x - point6.x, 2) + pow(point2.y - point6.y, 2));
    final vertical2 = sqrt(pow(point3.x - point5.x, 2) + pow(point3.y - point5.y, 2));
    
    // Horizontal distance
    final horizontal = sqrt(pow(point1.x - point4.x, 2) + pow(point1.y - point4.y, 2));
    
    if (horizontal == 0) return 0.0;
    
    // EAR formula
    return (vertical1 + vertical2) / (2.0 * horizontal);
  }

  Future<LivenessResult> processImage(CameraImage image) async {
    if (kIsWeb) return LivenessResult(passed: true, score: 1.0, message: "Web Skipped");

    final inputImage = _convertCameraImage(image);
    if (inputImage == null) {
      return LivenessResult(passed: false, score: 0.0, message: "Camera Error");
    }

    final meshes = await _meshDetector.processImage(inputImage);
    if (meshes.isEmpty) {
      // DON'T reset task progress - just pause and wait for face
      return LivenessResult(
        passed: false,
        score: _currentTaskIndex / (_tasks.isNotEmpty ? _tasks.length : 1),
        message: "Position face in frame",
        faceDetected: false,
        currentTaskNumber: _currentTaskIndex + 1,
        totalTasks: _tasks.isNotEmpty ? _tasks.length : 3,
      );
    }

    final face = meshes.first;
    final landmarks = face.points;
    
    // Face Stability Check - DON'T reset completed tasks
    if (landmarks.length < 468) {
       // Only reset current task state, not task index
       _consecutiveFrames = 0;
       return LivenessResult(
         passed: false, 
         score: _currentTaskIndex / _tasks.length, 
         message: "Hold your face steady", 
         faceDetected: true,
         currentTaskNumber: _currentTaskIndex + 1,
         totalTasks: _tasks.length,
       );
    }

    // Initialize tasks
    if (!_tasksInitialized) _initTasks();

    if (_currentTaskIndex >= _tasks.length) {
      return LivenessResult(
        passed: true, 
        score: 1.0, 
        message: "Liveness Verified!", 
        faceDetected: true,
        currentTaskNumber: _tasks.length,
        totalTasks: _tasks.length,
      );
    }

    // 8. Cooldown check
    if (_lastTaskPassTime != null) {
      if (DateTime.now().difference(_lastTaskPassTime!) < TASK_COOLDOWN) {
         return LivenessResult(
           passed: false,
           score: (_currentTaskIndex + 1) / _tasks.length, // Show progress
           message: "Success!",
           currentTask: _tasks[_currentTaskIndex > 0 ? _currentTaskIndex - 1 : 0], // Show prev task icon maybe?
           faceDetected: true,
           progress: 1.0,
         );
      } else {
        _lastTaskPassTime = null; // Cooldown over
      }
    }

    // --- raw Metrics ---
    // Calculate EAR using 6-point formula for better accuracy
    // Left eye: P1=33, P2=160, P3=158, P4=133, P5=153, P6=144
    // Right eye: P1=362, P2=385, P3=387, P4=263, P5=373, P6=380
    final leftEAR = _calculateEAR6Point(landmarks, 33, 160, 158, 133, 153, 144);
    final rightEAR = _calculateEAR6Point(landmarks, 362, 385, 387, 263, 373, 380);
    final rawEAR = (leftEAR + rightEAR) / 2.0;
    final rawMAR = FaceMeshService.calculateMAR(landmarks);
    
    // Debug raw EAR
    debugPrint('RAW EAR: $rawEAR (L:$leftEAR R:$rightEAR)');
    
    // Head Turn Logic (Fixed)
    final nose = landmarks[1];
    final leftCheek = landmarks[234];
    final rightCheek = landmarks[454];
    final faceCenterX = (leftCheek.x + rightCheek.x) / 2.0;
    final rawTurn = nose.x - faceCenterX;
    final faceWidth = (rightCheek.x - leftCheek.x).abs();
    double normalizedTurnRaw = rawTurn / (faceWidth > 0 ? faceWidth : 1.0);
    
    // Mirror inversion for front camera
    if (_lensDirection == CameraLensDirection.front) {
       normalizedTurnRaw = -normalizedTurnRaw;
    }
    
    // Jitter protection
    if (normalizedTurnRaw.abs() < 0.12) {
       normalizedTurnRaw = 0.0;
    }

    // 1. Temporal Smoothing
    double smoothEAR = rawEAR;
    double smoothMAR = rawMAR;
    double smoothHeadTurn = normalizedTurnRaw;

    if (_hasPrevData) {
      // Reduced smoothing for faster blink response (was 0.7/0.3, now 0.5/0.5)
      smoothEAR = _prevEAR * 0.5 + rawEAR * 0.5;
      smoothMAR = _prevMAR * 0.7 + rawMAR * 0.3;
      smoothHeadTurn = _prevHeadTurn * 0.7 + normalizedTurnRaw * 0.3;
    }
    
    _prevEAR = smoothEAR;
    _prevMAR = smoothMAR;
    _prevHeadTurn = smoothHeadTurn;
    _hasPrevData = true;

    // 3. Adaptive Baselines (Calibration)
    if (!_isCalibrated) {
      _calibrationFrames++;
      // Accumulate logic could be better, but let's just use the last frame of calibration for simplicity 
      // or simple running average during calibration
      if (_calibrationFrames == 1) {
         _neutralEAR = smoothEAR;
         _neutralMAR = smoothMAR;
         final smileMetrics = FaceMeshService.calculateSmileMetrics(landmarks);
         _neutralMouthWidth = smileMetrics['width'] ?? 0;
         _neutralCornerY = smileMetrics['corner_y'] ?? 0;
      } else {
         _neutralEAR = (_neutralEAR * 0.8) + (smoothEAR * 0.2);
         _neutralMAR = (_neutralMAR * 0.8) + (smoothMAR * 0.2);
         final smileMetrics = FaceMeshService.calculateSmileMetrics(landmarks);
         _neutralMouthWidth = (_neutralMouthWidth * 0.8) + ((smileMetrics['width'] ?? 0) * 0.2);
         _neutralCornerY = (_neutralCornerY * 0.8) + ((smileMetrics['corner_y'] ?? 0) * 0.2);
      }

      if (_calibrationFrames >= CALIBRATION_FRAMES_REQUIRED) {
        _isCalibrated = true;
        // Safety checks for bad calibration
        if (_neutralEAR < 0.15) _neutralEAR = 0.25; // Default fallback
        if (_neutralMAR > 0.1) _neutralMAR = 0.05; // Default fallback
      }

      return LivenessResult(
        passed: false,
        score: 0.0,
        message: "Hold still, calibrating...",
        faceDetected: true,
        progress: _calibrationFrames / CALIBRATION_FRAMES_REQUIRED,
      );
    }

    // --- Task Logic ---
    final currentTask = _tasks[_currentTaskIndex];
    bool taskPassed = false;
    double taskProgress = 0.0;
    String dynamicMessage = "";

    switch (currentTask) {
      case LivenessTask.BLINK:
        // Improved Blink Detection with fixed thresholds
        // Standard EAR: open eyes ~0.25-0.35, closed ~0.15 or less
        const double fixedClosedThreshold = 0.20;  // Below this = closed
        const double fixedOpenThreshold = 0.25;    // Above this = open
        
        // Debug EAR values
        debugPrint('BLINK: smoothEAR=$smoothEAR (closed<$fixedClosedThreshold, open>$fixedOpenThreshold) eyesClosed=$_eyesClosed count=$_blinkCount');

        if (smoothEAR < fixedClosedThreshold) {
          // Eyes are closed
          if (!_eyesClosed) {
            _eyesClosed = true;
            debugPrint('>>> Eyes CLOSED detected <<<');
          }
        } else if (smoothEAR > fixedOpenThreshold) {
          // Eyes are open
          if (_eyesClosed) {
            // Just opened after being closed = blink complete
            _blinkCount++;
            _eyesClosed = false;
            debugPrint('>>> BLINK #$_blinkCount counted! <<<');
          }
        }
        
        dynamicMessage = "Blink your eyes ($_blinkCount/$BLINKS_REQUIRED)";
        taskProgress = _blinkCount / BLINKS_REQUIRED;
        if (_blinkCount >= BLINKS_REQUIRED) taskPassed = true;
        break;

      case LivenessTask.MOUTH_OPEN:
        // 3. Adaptive Thresholds
        // MAR > neutralMAR * 1.4 + fixed buffer
        final threshold = max(_neutralMAR * 1.4, 0.15); // ensure absolute minimum
        
        if (smoothMAR > threshold) {
          _consecutiveFrames++;
        } else {
          _consecutiveFrames = 0;
        }
        
        dynamicMessage = "Open your mouth";
        taskProgress = min(_consecutiveFrames / STABILITY_FRAMES, 1.0);
        if (_consecutiveFrames >= STABILITY_FRAMES) taskPassed = true;
        break;

      case LivenessTask.SMILE:
        // Improved Smile Detection - STRICTER
        final smileMetrics = FaceMeshService.calculateSmileMetrics(landmarks);
        final smileRatio = smileMetrics['ratio'] ?? 0.0;  // width/height ratio
        final mouthWidth = smileMetrics['width'] ?? 0.0;
        final cornerY = smileMetrics['corner_y'] ?? 0.0;
        
        // Calculate mouth width ratio compared to neutral
        final widthRatio = mouthWidth / (_neutralMouthWidth > 0 ? _neutralMouthWidth : 1.0);
        
        // Lip corner lift (positive = lifted up = smiling)
        final lift = _neutralCornerY - cornerY;
        
        // Debug smile metrics
        debugPrint('SMILE: ratio=$smileRatio widthRatio=$widthRatio lift=$lift');
        
        // STRICTER detection: 
        // - Smile ratio > 6.0 (was 5.0) OR
        // - Width increases by 20% (was 15%) AND corners lift significantly (was 0.02)
        bool isSmiling = smileRatio > 6.0 || (widthRatio > 1.20 && lift > 0.03);
        
        if (isSmiling) {
           _consecutiveFrames++;
           debugPrint('>>> SMILE detected! Frame $_consecutiveFrames/$STABILITY_FRAMES <<<');
        } else {
           _consecutiveFrames = 0;
        }

        dynamicMessage = "Smile";
        taskProgress = min(_consecutiveFrames / STABILITY_FRAMES, 1.0);
        if (_consecutiveFrames >= STABILITY_FRAMES) taskPassed = true;
        break;

      case LivenessTask.HEAD_LEFT:
      case LivenessTask.HEAD_RIGHT:
        // 4. Normalized Head Turn
        // Use smoothed value directly as it is already normalized
        final threshold = 0.25;
        
        // Debug print
        debugPrint('Head Turn: $smoothHeadTurn (Task: $currentTask)');

        bool isTurned = false;
        if (currentTask == LivenessTask.HEAD_LEFT) {
           // Positive = turning left (from user's perspective)
           isTurned = smoothHeadTurn > threshold;
           dynamicMessage = "Turn head LEFT";
        } else {
           // Negative = turning right (from user's perspective)
           isTurned = smoothHeadTurn < -threshold;
           dynamicMessage = "Turn head RIGHT";
        }

        if (isTurned) {
          _consecutiveFrames++;
        } else {
          _consecutiveFrames = 0;
        }
        
        taskProgress = min(_consecutiveFrames / STABILITY_FRAMES, 1.0);
        if (_consecutiveFrames >= STABILITY_FRAMES) taskPassed = true;
        break;

      case LivenessTask.EYEBROW_RAISE:
         // Using simpler normalized eyebrow height - STRICTER
         final faceH = sqrt(pow(landmarks[10].x - landmarks[152].x, 2) + pow(landmarks[10].y - landmarks[152].y, 2));
         final raise = FaceMeshService.calculateEyebrowRaise(landmarks, faceH);

         // Debug eyebrow raise
         debugPrint('EYEBROW: raise=$raise (threshold=0.07)');

         // STRICTER threshold (was 0.055, now 0.07)
         if (raise > 0.07) {
            _consecutiveFrames++;
            debugPrint('>>> EYEBROW RAISE detected! Frame $_consecutiveFrames/$STABILITY_FRAMES <<<');
         } else {
            _consecutiveFrames = 0;
         }
         
         dynamicMessage = "Raise eyebrows";
         taskProgress = min(_consecutiveFrames / STABILITY_FRAMES, 1.0);
         if (_consecutiveFrames >= STABILITY_FRAMES) taskPassed = true;
         break;
    }

    if (taskPassed) {
       _lastTaskPassTime = DateTime.now();
       _currentTaskIndex++;
       _resetTaskState();
    }

    return LivenessResult(
      passed: false,
      score: _currentTaskIndex / _tasks.length,
      message: dynamicMessage,
      currentTask: currentTask,
      faceDetected: true,
      progress: taskProgress,
      currentTaskNumber: _currentTaskIndex + 1,
      totalTasks: _tasks.length,
    );
  }

  void dispose() {
    _meshDetector.close();
  }

  // --- Image Conversion boilerplate ---
  InputImage? _convertCameraImage(CameraImage image) {
    try {
      final imageRotation = _getImageRotation();
      if (imageRotation == null) return null;
      final format = _getInputImageFormat(image.format.group);
      if (format == null) return null;
      if (image.planes.isEmpty) return null;
      final bytes = _concatenatePlanes(image.planes);
      if (bytes == null) return null;

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
      return null;
    }
  }

  InputImageRotation? _getImageRotation() {
    int rotationCompensation = _sensorOrientation;
    if (_lensDirection == CameraLensDirection.front) {
      rotationCompensation = (360 - _sensorOrientation) % 360;
    }
    switch (rotationCompensation) {
      case 0: return InputImageRotation.rotation0deg;
      case 90: return InputImageRotation.rotation90deg;
      case 180: return InputImageRotation.rotation180deg;
      case 270: return InputImageRotation.rotation270deg;
      default: return InputImageRotation.rotation0deg;
    }
  }

  InputImageFormat? _getInputImageFormat(ImageFormatGroup formatGroup) {
    switch (formatGroup) {
      case ImageFormatGroup.nv21: return InputImageFormat.nv21;
      case ImageFormatGroup.yuv420: return InputImageFormat.yuv420;
      case ImageFormatGroup.bgra8888: return InputImageFormat.bgra8888;
      default:
        if (!kIsWeb && Platform.isAndroid) return InputImageFormat.nv21;
        return null;
    }
  }

  Uint8List? _concatenatePlanes(List<Plane> planes) {
    try {
      final WriteBuffer allBytes = WriteBuffer();
      for (final Plane plane in planes) {
        allBytes.putUint8List(plane.bytes);
      }
      return allBytes.done().buffer.asUint8List();
    } catch (e) {
      return null;
    }
  }
}
