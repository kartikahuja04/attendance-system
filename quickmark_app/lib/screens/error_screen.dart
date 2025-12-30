import 'package:flutter/material.dart';
import '../widgets/custom_button.dart';
import '../utils/theme.dart';

class ErrorScreen extends StatelessWidget {
  final String errorMessage;
  final String? errorType;

  const ErrorScreen({
    super.key,
    required this.errorMessage,
    this.errorType,
  });

  IconData get _errorIcon {
    if (errorType == 'expired') return Icons.timer_off;
    if (errorType == 'already_marked') return Icons.done_all;
    if (errorType == 'network') return Icons.wifi_off;
    return Icons.error_outline;
  }

  Color get _errorColor {
    if (errorType == 'already_marked') return AppTheme.warningColor;
    return AppTheme.errorColor;
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: SafeArea(
        child: Padding(
          padding: const EdgeInsets.all(24),
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              // Error Icon
              Container(
                padding: const EdgeInsets.all(24),
                decoration: BoxDecoration(
                  color: _errorColor.withOpacity(0.1),
                  shape: BoxShape.circle,
                ),
                child: Icon(
                  _errorIcon,
                  size: 100,
                  color: _errorColor,
                ),
              ),
              const SizedBox(height: 32),

              // Error Title
              Text(
                errorType == 'already_marked'
                    ? 'Already Marked'
                    : errorType == 'expired'
                        ? 'QR Code Expired'
                        : 'Error',
                style: Theme.of(context).textTheme.displaySmall?.copyWith(
                      color: _errorColor,
                      fontWeight: FontWeight.bold,
                    ),
                textAlign: TextAlign.center,
              ),
              const SizedBox(height: 16),

              // Error Message
              Text(
                errorMessage,
                style: Theme.of(context).textTheme.bodyLarge?.copyWith(
                      color: Colors.grey[600],
                    ),
                textAlign: TextAlign.center,
              ),
              const SizedBox(height: 48),

              // Action Buttons
              if (errorType == 'expired' || errorType == 'network') ...[
                CustomButton(
                  text: 'Try Again',
                  onPressed: () {
                    Navigator.of(context).pop();
                  },
                  icon: Icons.refresh,
                ),
                const SizedBox(height: 16),
              ],

              CustomButton(
                text: 'Go Home',
                onPressed: () {
                  Navigator.of(context).popUntil((route) => route.isFirst);
                },
                isOutlined: true,
                icon: Icons.home,
              ),
            ],
          ),
        ),
      ),
    );
  }
}
