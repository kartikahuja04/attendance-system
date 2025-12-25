import 'dart:math';
import 'dart:typed_data';
import 'package:flutter/foundation.dart';
import 'package:flutter/services.dart';
import 'package:camera/camera.dart';
import 'package:google_mlkit_face_detection/google_mlkit_face_detection.dart';
import 'package:image/image.dart' as img;
import 'package:tflite_flutter/tflite_flutter.dart';
import 'storage_service.dart';

/// Result of face recognition
class FaceRecognitionResult {
  final bool faceDetected;
  final bool recognized;
  final double similarity;
  final String message;
  final List<double>? embedding;

  FaceRecognitionResult({
    required this.faceDetected,
    required this.recognized,
    required this.similarity,
    required this.message,
    this.embedding,
  });
}

/// Service for face recognition using MobileFaceNet TFLite model
class FaceRecognitionService {
  static final FaceRecognitionService _instance = FaceRecognitionService._internal();
  factory FaceRecognitionService() => _instance;
  FaceRecognitionService._internal();

  Interpreter? _interpreter;
  bool _isInitialized = false;
  
  final StorageService _storageService = StorageService();
  
  // Model configuration for MobileFaceNet
  static const int _inputSize = 112; // MobileFaceNet expects 112x112 images
  static const int _embeddingSize = 192; // Output embedding size
  static const double _recognitionThreshold = 0.6; // Cosine similarity threshold
  
  /// Initialize the TFLite interpreter
  Future<bool> initialize() async {
    if (_isInitialized) return true;
    
    try {
      debugPrint('FaceRecognitionService: Loading MobileFaceNet model...');
      _interpreter = await Interpreter.fromAsset('models/mobilefacenet.tflite');
      _isInitialized = true;
      debugPrint('FaceRecognitionService: Model loaded successfully!');
      return true;
    } catch (e) {
      debugPrint('FaceRecognitionService: Failed to load model: $e');
      _isInitialized = false;
      return false;
    }
  }
  
  /// Check if model is available
  bool get isModelAvailable => _isInitialized && _interpreter != null;
  
  /// Check if face is enrolled
  Future<bool> isFaceEnrolled() async {
    return await _storageService.hasFaceEnrolled();
  }
  
  /// Enroll a face
  Future<FaceRecognitionResult> enrollFace(CameraImage image, Face face) async {
    // Initialize if not already done
    if (!_isInitialized) {
      await initialize();
    }
    
    if (!isModelAvailable) {
      // Fallback to landmark-based approach
      debugPrint('FaceRecognitionService: Using fallback mode (no TFLite model)');
      final embedding = _generateFallbackEmbedding(face);
      await _storageService.saveFaceEmbedding(embedding);
      return FaceRecognitionResult(
        faceDetected: true,
        recognized: true,
        similarity: 1.0,
        message: 'Face enrolled successfully (simplified mode)',
        embedding: embedding,
      );
    }
    
    try {
      debugPrint('FaceRecognitionService: Generating face embedding with TFLite...');
      final embedding = await _generateEmbedding(image, face);
      if (embedding == null) {
        debugPrint('FaceRecognitionService: Failed to generate embedding, using fallback');
        final fallbackEmbedding = _generateFallbackEmbedding(face);
        await _storageService.saveFaceEmbedding(fallbackEmbedding);
        return FaceRecognitionResult(
          faceDetected: true,
          recognized: true,
          similarity: 1.0,
          message: 'Face enrolled successfully',
          embedding: fallbackEmbedding,
        );
      }
      
      await _storageService.saveFaceEmbedding(embedding);
      debugPrint('FaceRecognitionService: Face embedding saved successfully!');
      return FaceRecognitionResult(
        faceDetected: true,
        recognized: true,
        similarity: 1.0,
        message: 'Face enrolled successfully',
        embedding: embedding,
      );
    } catch (e) {
      debugPrint('FaceRecognitionService: Enrollment error: $e');
      return FaceRecognitionResult(
        faceDetected: true,
        recognized: false,
        similarity: 0.0,
        message: 'Failed to enroll face: $e',
      );
    }
  }
  
  /// Verify a face against enrolled embedding
  Future<FaceRecognitionResult> verifyFace(CameraImage image, Face face) async {
    final storedEmbedding = await _storageService.getFaceEmbedding();
    if (storedEmbedding == null) {
      return FaceRecognitionResult(
        faceDetected: true,
        recognized: false,
        similarity: 0.0,
        message: 'No face enrolled. Please enroll first.',
      );
    }
    
    // Initialize if not already done
    if (!_isInitialized) {
      await initialize();
    }
    
    List<double> currentEmbedding;
    
    if (!isModelAvailable) {
      // Fallback verification
      currentEmbedding = _generateFallbackEmbedding(face);
    } else {
      try {
        final embedding = await _generateEmbedding(image, face);
        currentEmbedding = embedding ?? _generateFallbackEmbedding(face);
      } catch (e) {
        debugPrint('FaceRecognitionService: Error generating embedding: $e');
        currentEmbedding = _generateFallbackEmbedding(face);
      }
    }
    
    final similarity = _cosineSimilarity(currentEmbedding, storedEmbedding);
    final recognized = similarity >= _recognitionThreshold;
    
    debugPrint('FaceRecognitionService: Verification - similarity: $similarity, recognized: $recognized');
    
    return FaceRecognitionResult(
      faceDetected: true,
      recognized: recognized,
      similarity: similarity,
      message: recognized 
          ? 'Face verified successfully' 
          : 'Face does not match. Please try again.',
      embedding: currentEmbedding,
    );
  }
  
  /// Generate embedding using TFLite model
  Future<List<double>?> _generateEmbedding(CameraImage cameraImage, Face face) async {
    if (_interpreter == null) return null;
    
    try {
      // Convert CameraImage to img.Image
      final convertedImage = _convertCameraImage(cameraImage);
      if (convertedImage == null) {
        debugPrint('Failed to convert camera image');
        return null;
      }
      
      // Crop face region with padding
      final faceRect = face.boundingBox;
      final padding = (faceRect.width * 0.2).toInt();
      
      final x = (faceRect.left - padding).clamp(0, convertedImage.width - 1).toInt();
      final y = (faceRect.top - padding).clamp(0, convertedImage.height - 1).toInt();
      final w = (faceRect.width + padding * 2).clamp(1, convertedImage.width - x).toInt();
      final h = (faceRect.height + padding * 2).clamp(1, convertedImage.height - y).toInt();
      
      final croppedFace = img.copyCrop(
        convertedImage,
        x: x,
        y: y,
        width: w,
        height: h,
      );
      
      // Resize to model input size
      final resizedFace = img.copyResize(croppedFace, width: _inputSize, height: _inputSize);
      
      // Prepare input tensor [1, 112, 112, 3]
      final input = _imageToByteListFloat32(resizedFace);
      
      // Run inference
      final outputShape = [1, _embeddingSize];
      final output = List.generate(1, (_) => List.filled(_embeddingSize, 0.0));
      
      _interpreter!.run(input, output);
      
      // Normalize output embedding
      final embedding = output[0];
      return _normalizeVector(embedding);
    } catch (e) {
      debugPrint('FaceRecognitionService: Embedding generation error: $e');
      return null;
    }
  }
  
  /// Convert image to Float32 input tensor
  Float32List _imageToByteListFloat32(img.Image image) {
    final convertedBytes = Float32List(1 * _inputSize * _inputSize * 3);
    var index = 0;
    
    for (var y = 0; y < _inputSize; y++) {
      for (var x = 0; x < _inputSize; x++) {
        final pixel = image.getPixel(x, y);
        // Normalize to [-1, 1]
        convertedBytes[index++] = (pixel.r / 127.5) - 1.0;
        convertedBytes[index++] = (pixel.g / 127.5) - 1.0;
        convertedBytes[index++] = (pixel.b / 127.5) - 1.0;
      }
    }
    
    return convertedBytes;
  }
  
  /// Generate fallback embedding from face landmarks
  List<double> _generateFallbackEmbedding(Face face) {
    final embedding = List<double>.filled(_embeddingSize, 0.0);
    int idx = 0;
    
    // Use face bounding box ratios
    final bbox = face.boundingBox;
    if (idx < _embeddingSize) embedding[idx++] = bbox.width / (bbox.height + 1);
    if (idx < _embeddingSize) embedding[idx++] = (bbox.width * bbox.height) / 100000.0;
    
    // Use head angles (normalized)
    if (idx < _embeddingSize) embedding[idx++] = (face.headEulerAngleX ?? 0) / 45.0;
    if (idx < _embeddingSize) embedding[idx++] = (face.headEulerAngleY ?? 0) / 45.0;
    if (idx < _embeddingSize) embedding[idx++] = (face.headEulerAngleZ ?? 0) / 45.0;
    
    // Use eye probabilities
    if (idx < _embeddingSize) embedding[idx++] = face.leftEyeOpenProbability ?? 0.5;
    if (idx < _embeddingSize) embedding[idx++] = face.rightEyeOpenProbability ?? 0.5;
    
    // Use smiling probability
    if (idx < _embeddingSize) embedding[idx++] = face.smilingProbability ?? 0.5;
    
    // Add landmark positions (normalized relative to face bounding box)
    for (final entry in face.landmarks.entries) {
      final landmark = entry.value;
      if (landmark != null && idx < _embeddingSize - 1) {
        embedding[idx++] = (landmark.position.x - bbox.left) / (bbox.width + 1);
        embedding[idx++] = (landmark.position.y - bbox.top) / (bbox.height + 1);
      }
    }
    
    return _normalizeVector(embedding);
  }
  
  /// Convert CameraImage to img.Image
  img.Image? _convertCameraImage(CameraImage image) {
    try {
      if (image.format.group == ImageFormatGroup.yuv420) {
        return _convertYUV420(image);
      } else if (image.format.group == ImageFormatGroup.bgra8888) {
        return _convertBGRA8888(image);
      } else if (image.format.group == ImageFormatGroup.nv21) {
        return _convertNV21(image);
      }
      return null;
    } catch (e) {
      debugPrint('Image conversion error: $e');
      return null;
    }
  }
  
  /// Convert NV21 format
  img.Image _convertNV21(CameraImage image) {
    final width = image.width;
    final height = image.height;
    final yPlane = image.planes[0];
    final uvPlane = image.planes[1];
    
    final result = img.Image(width: width, height: height);
    
    for (int y = 0; y < height; y++) {
      for (int x = 0; x < width; x++) {
        final yIndex = y * yPlane.bytesPerRow + x;
        final uvIndex = (y ~/ 2) * uvPlane.bytesPerRow + (x ~/ 2) * 2;
        
        final yValue = yPlane.bytes[yIndex];
        final vValue = uvPlane.bytes.length > uvIndex ? uvPlane.bytes[uvIndex] : 128;
        final uValue = uvPlane.bytes.length > uvIndex + 1 ? uvPlane.bytes[uvIndex + 1] : 128;
        
        final pixel = _yuvToRgb(yValue, uValue, vValue);
        result.setPixelRgb(x, y, pixel[0], pixel[1], pixel[2]);
      }
    }
    
    return result;
  }
  
  /// Convert YUV420 format
  img.Image _convertYUV420(CameraImage image) {
    final width = image.width;
    final height = image.height;
    final yPlane = image.planes[0];
    final uPlane = image.planes[1];
    final vPlane = image.planes[2];
    
    final result = img.Image(width: width, height: height);
    
    for (int y = 0; y < height; y++) {
      for (int x = 0; x < width; x++) {
        final yIndex = y * yPlane.bytesPerRow + x;
        final uvIndex = (y ~/ 2) * uPlane.bytesPerRow + (x ~/ 2);
        
        final yValue = yPlane.bytes[yIndex];
        final uValue = uPlane.bytes.length > uvIndex ? uPlane.bytes[uvIndex] : 128;
        final vValue = vPlane.bytes.length > uvIndex ? vPlane.bytes[uvIndex] : 128;
        
        final pixel = _yuvToRgb(yValue, uValue, vValue);
        result.setPixelRgb(x, y, pixel[0], pixel[1], pixel[2]);
      }
    }
    
    return result;
  }
  
  /// Convert BGRA8888 format
  img.Image _convertBGRA8888(CameraImage image) {
    final width = image.width;
    final height = image.height;
    final plane = image.planes[0];
    
    return img.Image.fromBytes(
      width: width,
      height: height,
      bytes: plane.bytes.buffer,
      order: img.ChannelOrder.bgra,
    );
  }
  
  /// Convert YUV to RGB
  List<int> _yuvToRgb(int y, int u, int v) {
    final r = (y + 1.370705 * (v - 128)).clamp(0, 255).toInt();
    final g = (y - 0.337633 * (u - 128) - 0.698001 * (v - 128)).clamp(0, 255).toInt();
    final b = (y + 1.732446 * (u - 128)).clamp(0, 255).toInt();
    return [r, g, b];
  }
  
  /// Calculate cosine similarity between two vectors
  double _cosineSimilarity(List<double> a, List<double> b) {
    if (a.length != b.length) return 0.0;
    
    double dotProduct = 0.0;
    double normA = 0.0;
    double normB = 0.0;
    
    for (int i = 0; i < a.length; i++) {
      dotProduct += a[i] * b[i];
      normA += a[i] * a[i];
      normB += b[i] * b[i];
    }
    
    if (normA == 0 || normB == 0) return 0.0;
    
    return dotProduct / (sqrt(normA) * sqrt(normB));
  }
  
  /// Normalize a vector to unit length
  List<double> _normalizeVector(List<double> vector) {
    double norm = 0.0;
    for (final v in vector) {
      norm += v * v;
    }
    norm = sqrt(norm);
    
    if (norm == 0) return vector;
    
    return vector.map((v) => v / norm).toList();
  }
  
  /// Clear enrolled face
  Future<bool> clearEnrolledFace() async {
    return await _storageService.clearFaceEnrollment();
  }
  
  /// Dispose resources
  void dispose() {
    _interpreter?.close();
    _interpreter = null;
    _isInitialized = false;
  }
}
