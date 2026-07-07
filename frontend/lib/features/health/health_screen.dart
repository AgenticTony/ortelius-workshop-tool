import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/app_providers.dart';
import '../../core/config/app_config.dart';
import '../../core/theme/app_colors.dart';
import '../../widgets/screen_scaffold.dart';

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
      appBar: AppBar(title: const Text('Backend connection')),
      body: SafeArea(
        child: ScreenScaffold(
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            crossAxisAlignment: CrossAxisAlignment.center,
            children: [
              _statusIcon(),
              const SizedBox(height: 18),
              Text(
                _statusText(),
                textAlign: TextAlign.center,
                style: theme.textTheme.titleLarge?.copyWith(
                  color: theme.colorScheme.onSurface,
                ),
              ),
              const SizedBox(height: 6),
              Text(
                AppConfig.apiBaseUrl,
                textAlign: TextAlign.center,
                style: theme.textTheme.bodySmall?.copyWith(
                  color: theme.colorScheme.onSurfaceVariant,
                ),
              ),
              if (_result != null) ...[
                const SizedBox(height: 16),
                Card(
                  child: Padding(
                    padding: const EdgeInsets.all(14),
                    child: Text(
                      _result.toString(),
                      style: theme.textTheme.bodyMedium?.copyWith(
                        fontFamily: 'monospace',
                      ),
                    ),
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
              const SizedBox(height: 28),
              SizedBox(
                width: double.infinity,
                child: FilledButton.icon(
                  onPressed: _loading ? null : _check,
                  icon: _loading
                      ? const SizedBox(
                          width: 16,
                          height: 16,
                          child: CircularProgressIndicator(strokeWidth: 2),
                        )
                      : const Icon(Icons.refresh_rounded),
                  label: Text(_loading ? 'Checking…' : 'Re-check'),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _statusIcon() {
    final size = 64.0;
    if (_loading) {
      return SizedBox(
        width: size,
        height: size,
        child: const CircularProgressIndicator(),
      );
    }
    if (_error != null) {
      return Container(
        width: size,
        height: size,
        decoration: BoxDecoration(
          color: AppColors.accent.withValues(alpha: 0.12),
          shape: BoxShape.circle,
        ),
        child: Icon(Icons.error_outline_rounded,
            size: 32, color: Theme.of(context).colorScheme.error),
      );
    }
    if (_result != null) {
      return Container(
        width: size,
        height: size,
        decoration: BoxDecoration(
          color: const Color(0xFF10B981).withValues(alpha: 0.12),
          shape: BoxShape.circle,
        ),
        child: const Icon(Icons.check_circle_rounded,
            size: 32, color: Color(0xFF10B981)),
      );
    }
    return Container(
      width: size,
      height: size,
      decoration: BoxDecoration(
        color: AppColors.textSecondary.withValues(alpha: 0.12),
        shape: BoxShape.circle,
      ),
      child: Icon(Icons.hourglass_empty_rounded,
          size: 32, color: AppColors.textSecondary),
    );
  }

  String _statusText() {
    if (_loading) return 'Checking connection…';
    if (_error != null) return 'Could not reach the backend';
    if (_result != null) return 'Connected';
    return 'Ready';
  }
}
