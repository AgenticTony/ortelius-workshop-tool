import 'dart:ui';
import 'package:flutter/material.dart';

import '../core/theme/app_colors.dart';

/// A glassmorphic card — translucent surface with a frosted blur and a light
/// edge that simulates glass catching light. Makes cards lift off the dark
/// canvas with depth instead of sitting flat.
///
/// Two modes:
///  - [blur] true (default): real BackdropFilter blur. Use for prominent cards
///    that appear once or a few times (hero, access code, stat tiles). Expensive
///    when there are many on screen.
///  - [blur] false: simulated glass (translucent fill + gradient + light edge,
///    no backdrop blur). Use for repeating lists (the idea feed) so dozens of
///    cards stay performant.
class GlassCard extends StatelessWidget {
  const GlassCard({
    super.key,
    required this.child,
    this.blur = true,
    this.padding = const EdgeInsets.all(16),
    this.radius = 12,
    this.accentLeft = false,
    this.margin,
  });

  final Widget child;
  final bool blur;
  final EdgeInsetsGeometry padding;
  final double radius;
  /// A brighter left edge — marks an active/highlighted card.
  final bool accentLeft;
  /// Outer margin (the glass itself has no margin by default).
  final EdgeInsetsGeometry? margin;

  @override
  Widget build(BuildContext context) {
    if (margin != null) {
      return Padding(padding: margin!, child: _build(context));
    }
    return _build(context);
  }

  Widget _build(BuildContext context) {
    final isLight = Theme.of(context).brightness == Brightness.light;
    // The translucent fill — lets the canvas/content behind show through.
    final fill = AppColors.surface.withValues(alpha: isLight ? 0.72 : 0.55);

    // The light edge — brighter top + left borders simulate light hitting glass.
    final lightEdge = AppColors.textPrimary.withValues(alpha: isLight ? 0.35 : 0.10);
    final darkEdge = AppColors.border;

    // The glass body: gradient fill + child, with a light top-edge highlight.
    Widget body = Container(
      decoration: BoxDecoration(
        borderRadius: BorderRadius.circular(radius),
        // Vertical gradient — lighter at top (light source), darker at base.
        // This is what sells "glass" even without a real blur.
        gradient: LinearGradient(
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
          colors: [
            fill.withValues(alpha: isLight ? 0.85 : 0.65),
            fill.withValues(alpha: isLight ? 0.60 : 0.40),
          ],
        ),
        border: Border(
          top: BorderSide(color: lightEdge, width: 1),
          left: accentLeft
              ? const BorderSide(color: AppColors.accent, width: 1.5)
              : BorderSide(color: lightEdge.withValues(alpha: isLight ? 0.5 : 0.4), width: 1),
          right: BorderSide(color: darkEdge, width: 1),
          bottom: BorderSide(color: darkEdge, width: 1),
        ),
      ),
      child: Padding(padding: padding, child: child),
    );

    if (!blur) return body;

    // Real frosted glass: blur whatever is behind the card.
    return ClipRRect(
      borderRadius: BorderRadius.circular(radius),
      child: BackdropFilter(
        filter: ImageFilter.blur(sigmaX: 8, sigmaY: 8),
        child: body,
      ),
    );
  }
}
