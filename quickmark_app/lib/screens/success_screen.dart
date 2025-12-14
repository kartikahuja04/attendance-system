import 'package:flutter/material.dart';
import 'package:intl/intl.dart';
import '../widgets/custom_button.dart';

class SuccessScreen extends StatelessWidget {
  final String sessionId;
  final String studentId;
  final DateTime timestamp;

  const SuccessScreen({
    super.key,
    required this.sessionId,
    required this.studentId,
    required this.timestamp,
  });

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
              // Success Icon
              Container(
                padding: const EdgeInsets.all(24),
                decoration: BoxDecoration(
                  color: Colors.green[50],
                  shape: BoxShape.circle,
                ),
                child: Icon(
                  Icons.check_circle,
                  size: 100,
                  color: Colors.green[600],
                ),
              ),
              const SizedBox(height: 32),

              // Success Message
              Text(
                'Attendance Marked!',
                style: Theme.of(context).textTheme.displaySmall?.copyWith(
                      color: Colors.green[700],
                      fontWeight: FontWeight.bold,
                    ),
                textAlign: TextAlign.center,
              ),
              const SizedBox(height: 16),

              Text(
                'Your attendance has been successfully recorded',
                style: Theme.of(context).textTheme.bodyLarge?.copyWith(
                      color: Colors.grey[600],
                    ),
                textAlign: TextAlign.center,
              ),
              const SizedBox(height: 48),

              // Details Card
              Card(
                child: Padding(
                  padding: const EdgeInsets.all(20),
                  child: Column(
                    children: [
                      _DetailRow(
                        icon: Icons.person,
                        label: 'Student ID',
                        value: studentId,
                      ),
                      const Divider(height: 24),
                      _DetailRow(
                        icon: Icons.class_,
                        label: 'Session ID',
                        value: sessionId,
                      ),
                      const Divider(height: 24),
                      _DetailRow(
                        icon: Icons.access_time,
                        label: 'Time',
                        value: DateFormat('MMM dd, yyyy - hh:mm a').format(timestamp),
                      ),
                    ],
                  ),
                ),
              ),
              const SizedBox(height: 48),

              // Done Button
              CustomButton(
                text: 'Done',
                onPressed: () {
                  Navigator.of(context).popUntil((route) => route.isFirst);
                },
                icon: Icons.home,
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class _DetailRow extends StatelessWidget {
  final IconData icon;
  final String label;
  final String value;

  const _DetailRow({
    required this.icon,
    required this.label,
    required this.value,
  });

  @override
  Widget build(BuildContext context) {
    return Row(
      children: [
        Icon(icon, color: Colors.grey[600], size: 20),
        const SizedBox(width: 12),
        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                label,
                style: Theme.of(context).textTheme.bodySmall?.copyWith(
                      color: Colors.grey[600],
                    ),
              ),
              const SizedBox(height: 4),
              Text(
                value,
                style: Theme.of(context).textTheme.bodyLarge?.copyWith(
                      fontWeight: FontWeight.w500,
                    ),
              ),
            ],
          ),
        ),
      ],
    );
  }
}
