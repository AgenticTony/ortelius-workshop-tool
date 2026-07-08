import 'package:flutter/material.dart';

import '../core/theme/app_colors.dart';

/// A surface card — solid white with a 2px border and a soft drop shadow.
///
/// Projector-first: on a bright canvas in a lit room, translucency and blur
/// wash out and reduce contrast. This previous "glass" widget is now a plain,
/// high-contrast card — solid fill, defined border, soft shadow for depth.
/// The API is preserved so existing call sites keep working; the `blur` /
/// `accentLeft` flags still apply (accentLeft paints a left accent bar).
class GlassCard extends StatelessWidget {
  const GlassCard({
    super.key,
    required this.child,
    this.blur = false, // accepted for back-compat; ignored on light theme
    this.padding = const EdgeInsets.all(16),
    this.radius = 16,
    this.accentLeft = false,
    this.glow = false, // accepted for back-compat; ignored on light theme
    this.margin,
  });

  final Widget child;
  final bool blur;
  final EdgeInsetsGeometry padding;
  final double radius;
  final bool accentLeft;
  final bool glow;
  final EdgeInsetsGeometry? margin;

  @override
  Widget build(BuildContext context) {
    final card = DecoratedBox(
      decoration: BoxDecoration(
        color: AppColors.surface,
        borderRadius: BorderRadius.circular(radius),
        border: Border.all(
          color: accentLeft ? AppColors.accent : AppColors.border,
          width: accentLeft ? 2.5 : 2,
        ),
        boxShadow: const [
          BoxShadow(
            color: AppColors.shadowOuter,
            blurRadius: 12,
            offset: Offset(0, 4),
          ),
        ],
      ),
      child: Padding(padding: padding, child: child),
    );
    if (margin != null) {
      return Padding(padding: margin!, child: card);
    }
    return card;
  }
}

/// A brand-tinted glow halo behind a widget. On the light theme this is a no-op
/// (glow doesn't read on a bright canvas) — kept for back-compat so call sites
/// don't break.
class GlowWrapper extends StatelessWidget {
  const GlowWrapper({super.key, required this.child});
  final Widget child;

  @override
  Widget build(BuildContext context) => child;
}
