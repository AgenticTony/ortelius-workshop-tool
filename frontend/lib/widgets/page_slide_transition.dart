import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

/// A page that transitions in with a soft slide-up + fade — replacing go_router's
/// default hard cut with the "alive" motion the reference sites use.
///
/// Restraint: 220ms, easeOutCubic, small offsets. Not theatrical. Respects the
/// platform reduced-motion setting (collapses to a plain fade).
Page<T> pageSlide<T extends Object?>({
  required Widget child,
  required GoRouterState state,
  String? name,
}) {
  return CustomTransitionPage(
    key: state.pageKey,
    name: name,
    child: child,
    transitionDuration: const Duration(milliseconds: 220),
    reverseTransitionDuration: const Duration(milliseconds: 180),
    transitionsBuilder: (context, animation, secondaryAnimation, child) {
      final reduce = MediaQuery.disableAnimationsOf(context);
      if (reduce) {
        return FadeTransition(opacity: animation, child: child);
      }
      // Slide up a little + fade in. Curved so it decelerates into place.
      final curved = CurvedAnimation(
        parent: animation,
        curve: Curves.easeOutCubic,
        reverseCurve: Curves.easeInCubic,
      );
      return FadeTransition(
        opacity: curved,
        child: SlideTransition(
          position: Tween<Offset>(
            begin: const Offset(0, 0.06),
            end: Offset.zero,
          ).animate(curved),
          child: child,
        ),
      );
    },
  );
}
