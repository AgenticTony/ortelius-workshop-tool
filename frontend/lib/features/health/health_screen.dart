import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/app_providers.dart';
import '../../core/theme/layout.dart';
import '../../core/config/app_config.dart';

/// Connection-check screen. The Milestone 2 demo target: proves the app
/// builds, loads config, and can reach the backend /health endpoint.
class HealthScreen extends ConsumerStatefulWidget {
  const HealthScreen({super.key, this.autoCheck = true});

  /// Whether to fire a /health check automatically on first frame.
  /// Disable in tests to avoid a lingering network timer.
  final bool autoCheck;

  @override
  ConsumerState<HealthScreen> createState() => _HealthScreenState();
}

class _HealthScreenState extends ConsumerState<HealthScreen> {
  bool _loading = false;
  Map<String, dynamic>? _result;
  Object? _error;

  Future<void> _check() async {
    if (!mounted) return;
    setState(() {
      _loading = true;
      _error = null;
    });
    try {
      final api = ref.read(workshopApiProvider);
      final result = await api.health();
      if (!mounted) return; // navigated away during the await
      setState(() => _result = result);
    } catch (e) {
      if (!mounted) return;
      setState(() => _error = e);
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  @override
  void initState() {
    super.initState();
    if (widget.autoCheck) {
      // Fire the first check on load.
      WidgetsBinding.instance.addPostFrameCallback((_) => _check());
    }
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Scaffold(
      appBar: AppBar(title: const Text('Workshop Tool — Connection')),
      body: Center(
        child: ConstrainedBox(
          constraints: const BoxConstraints(maxWidth: Layout.contentMaxWidth),
          child: Padding(
            padding: const EdgeInsets.all(24),
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                _statusIcon(),
                const SizedBox(height: 16),
                Text(
                  _statusText(),
                  textAlign: TextAlign.center,
                  style: theme.textTheme.titleMedium,
                ),
                const SizedBox(height: 8),
                Text(
                  'Backend: ${AppConfig.apiBaseUrl}',
                  textAlign: TextAlign.center,
                  style: theme.textTheme.bodySmall,
                ),
                if (_result != null) ...[
                  const SizedBox(height: 12),
                  Card(
                    child: Padding(
                      padding: const EdgeInsets.all(12),
                      child: Text(_result.toString()),
                    ),
                  ),
                ],
                if (_error != null) ...[
                  const SizedBox(height: 12),
                  Text(
                    '$_error',
                    textAlign: TextAlign.center,
                    style: theme.textTheme.bodySmall
                        ?.copyWith(color: theme.colorScheme.error),
                  ),
                ],
                const SizedBox(height: 24),
                FilledButton.icon(
                  onPressed: _loading ? null : _check,
                  icon: _loading
                      ? const SizedBox(
                          width: 16,
                          height: 16,
                          child: CircularProgressIndicator(strokeWidth: 2),
                        )
                      : const Icon(Icons.refresh),
                  label: Text(_loading ? 'Checking…' : 'Re-check'),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }

  Widget _statusIcon() {
    if (_loading) {
      return const SizedBox(
        width: 48,
        height: 48,
        child: CircularProgressIndicator(),
      );
    }
    if (_error != null) {
      return const Icon(Icons.error_outline, size: 48, color: Colors.red);
    }
    if (_result != null) {
      return const Icon(Icons.check_circle, size: 48, color: Colors.green);
    }
    return const Icon(Icons.hourglass_empty, size: 48, color: Colors.grey);
  }

  String _statusText() {
    if (_loading) return 'Checking connection…';
    if (_error != null) return 'Could not reach the backend';
    if (_result != null) return 'Connected';
    return 'Ready';
  }
}
