import 'package:flutter/material.dart';

/// A dismissible inline error banner. Renders the [message] in the theme's
/// error container colors with an optional retry action.
class ErrorBanner extends StatelessWidget {
  const ErrorBanner({
    super.key,
    required this.message,
    this.onRetry,
    this.onDismiss,
  });

  final String message;
  final VoidCallback? onRetry;
  final VoidCallback? onDismiss;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Container(
      margin: const EdgeInsets.only(bottom: 12),
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
      decoration: BoxDecoration(
        color: theme.colorScheme.errorContainer,
        borderRadius: BorderRadius.circular(8),
      ),
      child: Row(
        children: [
          Icon(Icons.error_outline, color: theme.colorScheme.onErrorContainer),
          const SizedBox(width: 8),
          Expanded(
            child: Text(
              message,
              style: TextStyle(color: theme.colorScheme.onErrorContainer),
            ),
          ),
          if (onRetry != null)
            TextButton(
              onPressed: onRetry,
              child: Text(
                'Retry',
                style: TextStyle(color: theme.colorScheme.onErrorContainer),
              ),
            ),
          if (onDismiss != null)
            IconButton(
              tooltip: 'Dismiss',
              icon: Icon(Icons.close, size: 18,
                  color: theme.colorScheme.onErrorContainer),
              onPressed: onDismiss,
            ),
        ],
      ),
    );
  }
}
