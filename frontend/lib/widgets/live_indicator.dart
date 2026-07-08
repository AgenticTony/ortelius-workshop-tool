import 'package:flutter/material.dart';

import '../core/theme/app_colors.dart';

/// A compact live-connection indicator: a pulsing green dot + label.
///
/// Replaces the `_LiveDot` that was duplicated in both the dashboard and the
/// workshop screen. The pulse is the one ambient motion in the app — it makes
/// "live" feel alive without animating everything. Respects reduced motion:
/// when the platform asks for fewer animations the dot stays static.
class LiveIndicator extends StatefulWidget {
  const LiveIndicator({super.key, required this.connected});

  final bool connected;

  @override
  State<LiveIndicator> createState() => _LiveIndicatorState();
}

class _LiveIndicatorState extends State<LiveIndicator>
    with SingleTickerProviderStateMixin {
  late final AnimationController _controller;
  late final Animation<double> _scale;

  @override
  void initState() {
    super.initState();
    _controller = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 1400),
    );
    // Curved ease-in-out pulse between 0.7 and 1.0.
    _scale = Tween(begin: 0.7, end: 1.0).animate(
      CurvedAnimation(parent: _controller, curve: Curves.easeInOut),
    );
    if (widget.connected) _controller.repeat(reverse: true);
  }

  @override
  void didUpdateWidget(covariant LiveIndicator oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (widget.connected && !oldWidget.connected) {
      _controller.repeat(reverse: true);
    } else if (!widget.connected && oldWidget.connected) {
      _controller.stop();
    }
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final reduceMotion = MediaQuery.disableAnimationsOf(context);
    // Green is the universal "connected/healthy" signal. On the light theme we
    // use a deeper green so it holds contrast on a bright projector.
    const liveColor = AppColors.live;
    final color = widget.connected ? liveColor : theme.colorScheme.outline;
    final dot = Container(
      width: 8,
      height: 8,
      decoration: BoxDecoration(
        color: color,
        shape: BoxShape.circle,
        // Soft glow when live — the green "energy".
        boxShadow: widget.connected
            ? [BoxShadow(color: color.withValues(alpha: 0.35), blurRadius: 5)]
            : null,
      ),
    );

    return Row(
      mainAxisSize: MainAxisSize.min,
      children: [
        reduceMotion
            ? dot
            : ScaleTransition(scale: _scale, child: dot),
        const SizedBox(width: 6),
        Text(
          widget.connected ? 'Live' : 'Connecting…',
          style: theme.textTheme.labelSmall?.copyWith(
            color: widget.connected
                ? liveColor
                : theme.colorScheme.onSurfaceVariant,
            fontWeight: FontWeight.w600,
          ),
        ),
      ],
    );
  }
}
