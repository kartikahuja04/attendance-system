import 'package:flutter/material.dart';
import '../services/liveness_service.dart';
import '../utils/theme.dart';

class CameraOverlay extends StatelessWidget {
  final String message;
  final double progress;
  final bool showProgress;
  final bool faceDetected;
  final LivenessTask? currentTask;
  final bool isQrMode;
  final VoidCallback? onCancel;
  final int currentTaskNumber;
  final int totalTasks;

  const CameraOverlay({
    super.key,
    required this.message,
    this.progress = 0.0,
    this.showProgress = false,
    this.faceDetected = false,
    this.currentTask,
    this.isQrMode = false,
    this.onCancel,
    this.currentTaskNumber = 0,
    this.totalTasks = 3,
  });

  @override
  Widget build(BuildContext context) {
    return Stack(
      children: [
        // Semi-transparent overlay with cutout
        _buildOverlayWithCutout(context),

        // Instructions at top
        Positioned(
          top: 100,
          left: 0,
          right: 0,
          child: Container(
            padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 16),
            margin: const EdgeInsets.symmetric(horizontal: 24),
            decoration: BoxDecoration(
              color: Colors.black.withOpacity(0.85),
              borderRadius: BorderRadius.circular(12),
              border: Border.all(
                color: AppTheme.primaryColor.withOpacity(0.4),
                width: 1.5,
              ),
            ),
            child: Column(
              children: [
                // Task Counter (1/3, 2/3, etc.)
                if (showProgress && !isQrMode && totalTasks > 0)
                  Container(
                    margin: const EdgeInsets.only(bottom: 10),
                    padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 4),
                    decoration: BoxDecoration(
                      color: AppTheme.primaryColor,
                      borderRadius: BorderRadius.circular(12),
                    ),
                    child: Text(
                      'Task $currentTaskNumber/$totalTasks',
                      style: const TextStyle(
                        color: Colors.white,
                        fontSize: 12,
                        fontWeight: FontWeight.w600,
                      ),
                    ),
                  ),
                Text(
                  message,
                  style: const TextStyle(
                    color: Colors.white,
                    fontSize: 18,
                    fontWeight: FontWeight.w600,
                  ),
                  textAlign: TextAlign.center,
                ),
                if (showProgress) ...[
                  const SizedBox(height: 16),
                  
                  // Icon for current task
                  if (currentTask != null)
                    Icon(
                      _getTaskIcon(currentTask!),
                      color: Colors.white,
                      size: 48,
                    ),
                    
                  const SizedBox(height: 16),
                  
                  // Progress bar
                  ClipRRect(
                    borderRadius: BorderRadius.circular(6),
                    child: LinearProgressIndicator(
                      value: progress,
                      backgroundColor: Colors.white.withOpacity(0.2),
                      valueColor: AlwaysStoppedAnimation<Color>(
                        progress >= 1.0 ? AppTheme.successColor : AppTheme.primaryColor,
                      ),
                      minHeight: 10,
                    ),
                  ),
                ],
              ],
            ),
          ),
        ),

        // Cancel button at bottom
        if (onCancel != null)
          Positioned(
            bottom: 50,
            left: 0,
            right: 0,
            child: Center(
              child: ElevatedButton.icon(
                onPressed: onCancel,
                icon: const Icon(Icons.close, size: 18),
                label: const Text('Cancel'),
                style: ElevatedButton.styleFrom(
                  backgroundColor: AppTheme.errorColor,
                  foregroundColor: Colors.white,
                  elevation: 0,
                  padding: const EdgeInsets.symmetric(horizontal: 28, vertical: 12),
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(8),
                  ),
                ),
              ),
            ),
          ),
      ],
    );
  }

  IconData _getTaskIcon(LivenessTask task) {
    switch (task) {
      case LivenessTask.BLINK: return Icons.visibility_off;
      case LivenessTask.SMILE: return Icons.sentiment_very_satisfied;
      case LivenessTask.HEAD_LEFT: return Icons.arrow_back; // Points Left
      case LivenessTask.HEAD_RIGHT: return Icons.arrow_forward; // Points Right
      case LivenessTask.MOUTH_OPEN: return Icons.mood; // Approximation
      case LivenessTask.EYEBROW_RAISE: return Icons.arrow_upward;
    }
  }

  Widget _buildOverlayWithCutout(BuildContext context) {
    final size = MediaQuery.of(context).size;
    final centerX = size.width / 2;
    final centerY = size.height / 2;

    if (isQrMode) {
      // QR scanning mode - square cutout
      const cutoutSize = 280.0;
      return CustomPaint(
        size: size,
        painter: _QrOverlayPainter(
          centerX: centerX,
          centerY: centerY,
          cutoutSize: cutoutSize,
        ),
      );
    } else {
      // Liveness mode - oval face guide
      const ovalWidth = 280.0;
      const ovalHeight = 360.0;
      return CustomPaint(
        size: size,
        painter: _FaceOverlayPainter(
          centerX: centerX,
          centerY: centerY,
          ovalWidth: ovalWidth,
          ovalHeight: ovalHeight,
          faceDetected: faceDetected,
          progress: progress,
        ),
      );
    }
  }

  // Removed old _buildLivenessIndicators
}

// Custom painter for face overlay with oval cutout
class _FaceOverlayPainter extends CustomPainter {
  final double centerX;
  final double centerY;
  final double ovalWidth;
  final double ovalHeight;
  final bool faceDetected;
  final double progress;

  _FaceOverlayPainter({
    required this.centerX,
    required this.centerY,
    required this.ovalWidth,
    required this.ovalHeight,
    required this.faceDetected,
    required this.progress,
  });

  @override
  void paint(Canvas canvas, Size size) {
    // Dark overlay
    final overlayPaint = Paint()
      ..color = Colors.black.withOpacity(0.6)
      ..style = PaintingStyle.fill;

    // Create path with oval cutout
    final path = Path()
      ..addRect(Rect.fromLTWH(0, 0, size.width, size.height))
      ..addOval(Rect.fromCenter(
        center: Offset(centerX, centerY),
        width: ovalWidth,
        height: ovalHeight,
      ))
      ..fillType = PathFillType.evenOdd;

    canvas.drawPath(path, overlayPaint);

    // Draw oval border
    final borderColor = faceDetected
        ? (progress >= 0.7 ? AppTheme.successColor : AppTheme.primaryColor)
        : Colors.white;
    
    final borderPaint = Paint()
      ..color = borderColor
      ..style = PaintingStyle.stroke
      ..strokeWidth = 4;

    canvas.drawOval(
      Rect.fromCenter(
        center: Offset(centerX, centerY),
        width: ovalWidth,
        height: ovalHeight,
      ),
      borderPaint,
    );

    // Draw animated glow if face detected
    if (faceDetected) {
      final glowPaint = Paint()
        ..color = borderColor.withOpacity(0.3)
        ..style = PaintingStyle.stroke
        ..strokeWidth = 8
        ..maskFilter = const MaskFilter.blur(BlurStyle.normal, 8);

      canvas.drawOval(
        Rect.fromCenter(
          center: Offset(centerX, centerY),
          width: ovalWidth,
          height: ovalHeight,
        ),
        glowPaint,
      );
    }
  }

  @override
  bool shouldRepaint(covariant _FaceOverlayPainter oldDelegate) {
    return oldDelegate.faceDetected != faceDetected ||
        oldDelegate.progress != progress;
  }
}

// Custom painter for QR scanning overlay
class _QrOverlayPainter extends CustomPainter {
  final double centerX;
  final double centerY;
  final double cutoutSize;

  _QrOverlayPainter({
    required this.centerX,
    required this.centerY,
    required this.cutoutSize,
  });

  @override
  void paint(Canvas canvas, Size size) {
    // Dark overlay
    final overlayPaint = Paint()
      ..color = Colors.black.withOpacity(0.6)
      ..style = PaintingStyle.fill;

    // Create path with square cutout
    final cutoutRect = Rect.fromCenter(
      center: Offset(centerX, centerY),
      width: cutoutSize,
      height: cutoutSize,
    );

    final path = Path()
      ..addRect(Rect.fromLTWH(0, 0, size.width, size.height))
      ..addRRect(RRect.fromRectAndRadius(cutoutRect, const Radius.circular(20)))
      ..fillType = PathFillType.evenOdd;

    canvas.drawPath(path, overlayPaint);

    // Draw border
    final borderPaint = Paint()
      ..color = AppTheme.primaryColor
      ..style = PaintingStyle.stroke
      ..strokeWidth = 3;

    canvas.drawRRect(
      RRect.fromRectAndRadius(cutoutRect, const Radius.circular(16)),
      borderPaint,
    );

    // Draw corner markers
    final cornerPaint = Paint()
      ..color = AppTheme.primaryColor
      ..style = PaintingStyle.stroke
      ..strokeWidth = 5
      ..strokeCap = StrokeCap.round;

    const cornerLength = 40.0;
    const offset = 2.0;

    // Top-left corner
    canvas.drawLine(
      Offset(cutoutRect.left - offset, cutoutRect.top + cornerLength),
      Offset(cutoutRect.left - offset, cutoutRect.top - offset),
      cornerPaint,
    );
    canvas.drawLine(
      Offset(cutoutRect.left - offset, cutoutRect.top - offset),
      Offset(cutoutRect.left + cornerLength, cutoutRect.top - offset),
      cornerPaint,
    );

    // Top-right corner
    canvas.drawLine(
      Offset(cutoutRect.right - cornerLength, cutoutRect.top - offset),
      Offset(cutoutRect.right + offset, cutoutRect.top - offset),
      cornerPaint,
    );
    canvas.drawLine(
      Offset(cutoutRect.right + offset, cutoutRect.top - offset),
      Offset(cutoutRect.right + offset, cutoutRect.top + cornerLength),
      cornerPaint,
    );

    // Bottom-left corner
    canvas.drawLine(
      Offset(cutoutRect.left - offset, cutoutRect.bottom - cornerLength),
      Offset(cutoutRect.left - offset, cutoutRect.bottom + offset),
      cornerPaint,
    );
    canvas.drawLine(
      Offset(cutoutRect.left - offset, cutoutRect.bottom + offset),
      Offset(cutoutRect.left + cornerLength, cutoutRect.bottom + offset),
      cornerPaint,
    );

    // Bottom-right corner
    canvas.drawLine(
      Offset(cutoutRect.right - cornerLength, cutoutRect.bottom + offset),
      Offset(cutoutRect.right + offset, cutoutRect.bottom + offset),
      cornerPaint,
    );
    canvas.drawLine(
      Offset(cutoutRect.right + offset, cutoutRect.bottom + offset),
      Offset(cutoutRect.right + offset, cutoutRect.bottom - cornerLength),
      cornerPaint,
    );
  }

  @override
  bool shouldRepaint(covariant _QrOverlayPainter oldDelegate) => false;
}

