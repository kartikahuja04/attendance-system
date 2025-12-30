
import 'dart:math';
import 'package:google_mlkit_face_mesh_detection/google_mlkit_face_mesh_detection.dart';

class FaceMeshService {
  /// Calculate Eye Aspect Ratio (EAR)
  /// checks the ratio of vertical distance to horizontal distance of the eye
  static double calculateEAR(List<FaceMeshPoint> landmarks, int left, int right, int top, int bottom) {
    // 0-indexed in List, so we can access directly if the list is full 468 points.
    // However, google_mlkit_face_mesh_detection might not return a simple list.
    // Usually it returns a list of FaceMeshPoint. We assume they are ordered by index 0-467.

    if (landmarks.length < 468) return 0.0;

    final pLeft = landmarks[left];
    final pRight = landmarks[right];
    final pTop = landmarks[top];
    final pBottom = landmarks[bottom];

    final vertical = _distance(pTop, pBottom);
    final horizontal = _distance(pLeft, pRight);

    if (horizontal == 0) return 0.0;
    return vertical / horizontal;
  }

  /// Calculate Mouth Aspect Ratio (MAR)
  static double calculateMAR(List<FaceMeshPoint> landmarks) {
    if (landmarks.length < 468) return 0.0;

    // Lips: 13, 14 (inner vertical), 78, 308 (corners)
    final top = landmarks[13];
    final bottom = landmarks[14];
    final left = landmarks[78];
    final right = landmarks[308];

    final vertical = _distance(top, bottom);
    final horizontal = _distance(left, right);

    if (horizontal == 0) return 0.0;
    return vertical / horizontal;
  }

  /// Calculate Smile Ratio and other smile metrics
  static Map<String, double> calculateSmileMetrics(List<FaceMeshPoint> landmarks) {
    if (landmarks.length < 468) return {'ratio': 0.0, 'width': 0.0, 'lift': 0.0};

    final leftCorner = landmarks[78];
    final rightCorner = landmarks[308];
    final topLip = landmarks[13];
    final bottomLip = landmarks[14];

    final width = _distance(leftCorner, rightCorner);
    final height = _distance(topLip, bottomLip);
    
    // Corners Y average (normalized by face bounding box height approx, or just raw if we track relative change)
    // In Python code: corner_lift = neutral_corner_y - current_corner_y. 
    // Y increases downwards. So smaller Y means higher up.
    final cornerY = (leftCorner.y + rightCorner.y) / 2.0;

    double ratio = 0.0;
    if (height > 0) {
      ratio = width / height;
    }

    return {
      'ratio': ratio,
      'width': width,
      'corner_y': cornerY,
    };
  }

  /// Calculate Eyebrow raise (normalized)
  static double calculateEyebrowRaise(List<FaceMeshPoint> landmarks, double faceHeight) {
    if (landmarks.length < 468) return 0.0;

    // Left: 105 (eyebrow), 159 (eye top)
    // Right: 334 (eyebrow), 386 (eye top)
    
    final lEyebrow = landmarks[105];
    final lEye = landmarks[159];
    
    final rEyebrow = landmarks[334];
    final rEye = landmarks[386];

    final leftDist = (lEyebrow.y - lEye.y).abs();
    final rightDist = (rEyebrow.y - rEye.y).abs();

    final avgDist = (leftDist + rightDist) / 2.0;

    if (faceHeight == 0) return 0.0;
    return avgDist / faceHeight; // Normalized by face height
  }
  
  /// Calculate Head Rotation (Yaw/Turn) using nose offset
  static double calculateHeadTurnRatio(List<FaceMeshPoint> landmarks) {
    if (landmarks.length < 468) return 0.0;

    // Nose tip: 1
    // Left Eye Outer: 33 OR 263 (Right)
    // Actually 33 (Left Eye inner) vs 263 (Right Eye inner) is better for width?
    // Python code used: 33 (left), 263 (right) for face width. Nose: 1.
    
    final nose = landmarks[1];
    final leftEye = landmarks[33];
    final rightEye = landmarks[263];

    final faceWidth = (rightEye.x - leftEye.x).abs();
    final faceCenterX = (leftEye.x + rightEye.x) / 2.0;
    final noseX = nose.x;

    final offset = noseX - faceCenterX;
    
    if (faceWidth == 0) return 0.0;
    return offset / faceWidth;
  }

  static double _distance(FaceMeshPoint p1, FaceMeshPoint p2) {
    return sqrt(pow(p1.x - p2.x, 2) + pow(p1.y - p2.y, 2));
  }
}
