import 'package:flutter/material.dart';

import '../core/theme/app_colors.dart';

/// A tappable card with real interactive feedback — the kind of micro-response
/// the reference sites use to make UI feel alive: it scales down on press and,
/// for the primary variant, carries a soft accent glow.
///
/// This replaces the dead-static Material tiles on the home screen. Motion is
/// small (3% scale) and quick (90ms) — a tool, not a toy. Reduced-motion is
/// respected: only the glow/colour change remains, no scale.
class InteractiveTile extends StatefulWidget {
  const InteractiveTile({
    super.key,
    required this.onTap,
    required this.child,
    this.primary = false,
    this.radius = 16,
  });

  final VoidCallback onTap;
  final Widget child;

  /// Primary tiles get the accent fill + a brand glow halo.
  final bool primary;
  final double radius;

  @override
  State<InteractiveTile> createState() => _InteractiveTileState();
}

class _InteractiveTileState extends State<InteractiveTile> {
  bool _pressed = false;

  void _set(bool v) {
    if (_pressed == v) return;
    if (!mounted) return;
    final reduce = MediaQuery.disableAnimationsOf(context);
    setState(() => _pressed = reduce ? false : v);
  }

  @override
  Widget build(BuildContext context) {
    final reduce = MediaQuery.disableAnimationsOf(context);
    // Scale down on press (skip when reduced-motion).
    final scale = (_pressed && !reduce) ? 0.97 : 1.0;

    return MouseRegion(
      cursor: SystemMouseCursors.click,
      child: GestureDetector(
        onTapDown: (_) => _set(true),
        onTapUp: (_) => _set(false),
        onTapCancel: () => _set(false),
        onTap: widget.onTap,
        child: AnimatedScale(
          scale: scale,
          duration: const Duration(milliseconds: 90),
          curve: Curves.easeOut,
          child: AnimatedContainer(
            duration: const Duration(milliseconds: 160),
            decoration: BoxDecoration(
              borderRadius: BorderRadius.circular(widget.radius),
              // Primary tiles carry the accent glow halo on the surface beneath.
              boxShadow: widget.primary
                  ? [
                      BoxShadow(
                        color: AppColors.accentGlow.withValues(alpha: 0.55),
                        blurRadius: _pressed ? 18 : 26,
                        spreadRadius: 0,
                      ),
                    ]
                  : null,
            ),
            child: widget.child,
          ),
        ),
      ),
    );
  }
}
