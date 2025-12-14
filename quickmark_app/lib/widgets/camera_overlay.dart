import 'package:flutter/material.dart';

class CameraOverlay extends StatelessWidget {
  final String message;
  final double progress;
  final bool showProgress;
  final bool faceDetected;
  final bool blinkDetected;
  final bool headMoved;
  final bool isQrMode;
  final VoidCallback? onCancel;

  const CameraOverlay({
    super.key,
    required this.message,
    this.progress = 0.0,
    this.showProgress = false,
    this.faceDetected = false,
    this.blinkDetected = false,
    this.headMoved = false,
    this.isQrMode = false,
    this.onCancel,
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
              color: Colors.black.withOpacity(0.75),
              borderRadius: BorderRadius.circular(16),
              border: Border.all(
                color: Colors.white.withOpacity(0.2),
                width: 1,
              ),
            ),
            child: Column(
              children: [
                Text(
                  message,
                  style: const TextStyle(
                    color: Colors.white,
                    fontSize: 16,
                    fontWeight: FontWeight.w500,
                  ),
                  textAlign: TextAlign.center,
                ),
                if (showProgress) ...[
                  const SizedBox(height: 16),
                  // Liveness check indicators
                  _buildLivenessIndicators(),
                  const SizedBox(height: 12),
                  // Progress bar
                  ClipRRect(
                    borderRadius: BorderRadius.circular(6),
                    child: LinearProgressIndicator(
                      value: progress,
                      backgroundColor: Colors.white.withOpacity(0.2),
                      valueColor: AlwaysStoppedAnimation<Color>(
                        progress >= 0.7 ? Colors.green : Colors.blue,
                      ),
                      minHeight: 8,
                    ),
                  ),
                  const SizedBox(height: 8),
                  Text(
                    '${(progress * 100).toInt()}% Complete',
                    style: TextStyle(
                      color: Colors.white.withOpacity(0.8),
                      fontSize: 12,
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
                icon: const Icon(Icons.close, size: 20),
                label: const Text('Cancel'),
                style: ElevatedButton.styleFrom(
                  backgroundColor: Colors.red.shade600,
                  foregroundColor: Colors.white,
                  padding: const EdgeInsets.symmetric(horizontal: 32, vertical: 14),
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(30),
                  ),
                  elevation: 4,
                ),
              ),
            ),
          ),
      ],
    );
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
      const ovalWidth = 240.0;
      const ovalHeight = 320.0;
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

  Widget _buildLivenessIndicators() {
    return Row(
      mainAxisAlignment: MainAxisAlignment.center,
      children: [
        _buildIndicator(
          icon: Icons.face,
          label: 'Face',
          isComplete: faceDetected,
        ),
        const SizedBox(width: 24),
        _buildIndicator(
          icon: Icons.visibility,
          label: 'Blink',
          isComplete: blinkDetected,
        ),
        const SizedBox(width: 24),
        _buildIndicator(
          icon: Icons.rotate_left,
          label: 'Turn',
          isComplete: headMoved,
        ),
      ],
    );
  }

  Widget _buildIndicator({
    required IconData icon,
    required String label,
    required bool isComplete,
  }) {
    return Column(
      children: [
        Container(
          padding: const EdgeInsets.all(8),
          decoration: BoxDecoration(
            color: isComplete ? Colors.green : Colors.white.withOpacity(0.2),
            shape: BoxShape.circle,
            border: Border.all(
              color: isComplete ? Colors.green : Colors.white.withOpacity(0.5),
              width: 2,
            ),
          ),
          child: Icon(
            isComplete ? Icons.check : icon,
            color: Colors.white,
            size: 20,
          ),
        ),
        const SizedBox(height: 4),
        Text(
          label,
          style: TextStyle(
            color: isComplete ? Colors.green : Colors.white.withOpacity(0.7),
            fontSize: 10,
            fontWeight: FontWeight.w500,
          ),
        ),
      ],
    );
  }
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
        ? (progress >= 0.7 ? Colors.green : Colors.blue)
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
      ..color = Colors.green
      ..style = PaintingStyle.stroke
      ..strokeWidth = 4;

    canvas.drawRRect(
      RRect.fromRectAndRadius(cutoutRect, const Radius.circular(20)),
      borderPaint,
    );

    // Draw corner markers
    final cornerPaint = Paint()
      ..color = Colors.green
      ..style = PaintingStyle.stroke
      ..strokeWidth = 6
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

