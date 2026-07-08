import 'dart:ui';
import 'package:flutter/material.dart';

import '../core/theme/app_colors.dart';

/// A glassmorphic surface with real depth — translucent gradient fill, layered
/// shadows, a light top-edge that mimics glass catching light, and optional
/// frosted backdrop blur.
///
/// What makes this read as "real product" instead of flat-AI:
///  - **Layered shadows**: a soft outer drop (lifts the card off the canvas)
///    plus a tight inner-top highlight (the recessed-glass read).
///  - **Gradient border**: the top edge is brighter than the bottom, the way
///    real glass catches a light source from above. Uniform borders look dead.
///  - **Vertical fill gradient**: lighter at top-left, darker at bottom-right.
///    This sells "glass" even without a real blur, and gives atmosphere.
///  - **Glow mode**: primary/hovered cards get a brand-tinted halo behind them.
///
/// Two blur modes:
///  - [blur] true (default): real BackdropFilter. Use for prominent cards that
///    appear once or a few times (hero, access code, stat tiles).
///  - [blur] false: simulated glass (no backdrop blur). Use for repeating lists
///    so dozens of cards stay performant.
class GlassCard extends StatelessWidget {
  const GlassCard({
    super.key,
    required this.child,
    this.blur = true,
    this.padding = const EdgeInsets.all(16),
    this.radius = 12,
    this.accentLeft = false,
    this.glow = false,
    this.margin,
  });

  final Widget child;
  final bool blur;
  final EdgeInsetsGeometry padding;
  final double radius;

  /// A brighter left edge — marks an active/highlighted card.
  final bool accentLeft;

  /// A brand-tinted halo behind the card. Use for the primary action / focus.
  final bool glow;

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
    // Translucent fill — lets the canvas/content behind show through.
    const fill = AppColors.surface;

    // Light edge (top) — brighter, simulates light hitting glass from above.
    const lightEdge = AppColors.glassHighlight;
    const darkEdge = AppColors.border;

    // The glass body: gradient fill + layered shadows + gradient border + child.
    Widget body = DecoratedBox(
      decoration: BoxDecoration(
        borderRadius: BorderRadius.circular(radius),
        // Vertical gradient — lighter at top-left (light source), darker at base.
        gradient: LinearGradient(
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
          colors: [
            fill.withValues(alpha: 0.72),
            fill.withValues(alpha: 0.48),
          ],
        ),
        // Layered shadows — the key depth cue.
        //  1. Soft outer drop: lifts the card off the canvas.
        //  2. Tight outer shadow near the card: grounds it.
        boxShadow: [
          BoxShadow(
            color: AppColors.shadowOuter,
            blurRadius: 24,
            offset: const Offset(0, 8), // light from above → shadow falls down
            spreadRadius: 0,
          ),
          BoxShadow(
            color: AppColors.shadowOuter.withValues(alpha: 0.5),
            blurRadius: 6,
            offset: const Offset(0, 2),
            spreadRadius: 0,
          ),
        ],
        // Gradient border — bright top, dark bottom. Drawn via a Border with
        // per-side colors so the light-source reads correctly.
        border: Border(
          top: const BorderSide(color: lightEdge, width: 1),
          left: BorderSide(
            color: accentLeft
                ? AppColors.accent
                : lightEdge.withValues(alpha: 0.6),
            width: accentLeft ? 1.5 : 1,
          ),
          right: const BorderSide(color: darkEdge, width: 1),
          bottom: const BorderSide(color: darkEdge, width: 1),
        ),
      ),
      child: Padding(padding: padding, child: child),
    );

    // Real frosted glass: blur whatever is behind the card.
    if (blur) {
      body = ClipRRect(
        borderRadius: BorderRadius.circular(radius),
        child: BackdropFilter(
          filter: ImageFilter.blur(sigmaX: 10, sigmaY: 10),
          child: body,
        ),
      );
    }

    // Optional brand-tinted glow halo behind the card.
    if (glow) {
      body = Stack(
        clipBehavior: Clip.none,
        children: [
          // The glow: a large blurred accent disc behind the card.
          Positioned.fill(
            child: DecoratedBox(
              decoration: BoxDecoration(
                borderRadius: BorderRadius.circular(radius),
                boxShadow: [
                  BoxShadow(
                    color: AppColors.accentGlow,
                    blurRadius: 32,
                    spreadRadius: 4,
                    offset: Offset.zero,
                  ),
                ],
              ),
            ),
          ),
          body,
        ],
      );
    }

    return body;
  }
}
