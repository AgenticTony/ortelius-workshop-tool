import 'package:flutter/material.dart';

/// Reveals its child with a fade + upward slide, delayed by [index] so a
/// sequence of these reads as a staggered entrance — the "alive" quality the
/// reference sites (skiper-ui / animmasterlib) sell with motion.
///
/// Restraint (this is a tool, not a portfolio): 220ms total, easeOutCubic, and
/// a small (12px) slide. Skipped entirely when reduced-motion is requested.
class StaggeredReveal extends StatefulWidget {
  const StaggeredReveal({
    super.key,
    required this.child,
    this.index = 0,
    this.delayStep = const Duration(milliseconds: 70),
    this.duration = const Duration(milliseconds: 220),
    this.slide = 12,
  });

  final Widget child;

  /// Position in the stagger. Item N waits N × [delayStep] before starting.
  final int index;

  /// Per-item delay. 70ms feels responsive without rushing a multi-element list.
  final Duration delayStep;

  /// The full in-animation length.
  final Duration duration;

  /// Pixels to slide up from. Small → precise, not theatrical.
  final double slide;

  @override
  State<StaggeredReveal> createState() => _StaggeredRevealState();
}

class _StaggeredRevealState extends State<StaggeredReveal>
    with SingleTickerProviderStateMixin {
  late final AnimationController _c;
  late final Animation<double> _fade;
  late final Animation<Offset> _slide;

  @override
  void initState() {
    super.initState();
    _c = AnimationController(vsync: this, duration: widget.duration);
    _fade = CurvedAnimation(parent: _c, curve: Curves.easeOutCubic);
    _slide = Tween<Offset>(
      begin: Offset(0, widget.slide / 100),
      end: Offset.zero,
    ).animate(CurvedAnimation(parent: _c, curve: Curves.easeOutCubic));

    // Respect reduced-motion: if the platform asks us not to animate, just
    // show the child. We check on first frame via WidgetsBinding so the media
    // query is available.
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (!mounted) return;
      final reduce = MediaQuery.disableAnimationsOf(context);
      if (reduce) {
        _c.value = 1;
        return;
      }
      Future.delayed(
        Duration(milliseconds: widget.index * widget.delayStep.inMilliseconds),
        () {
          if (mounted) _c.forward();
        },
      );
    });
  }

  @override
  void dispose() {
    _c.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return FadeTransition(
      opacity: _fade,
      child: SlideTransition(position: _slide, child: widget.child),
    );
  }
}
