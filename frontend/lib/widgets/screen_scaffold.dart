import 'package:flutter/material.dart';

import '../core/theme/layout.dart';

/// The shared screen shell every centered/form screen uses.
///
/// Replaces the repeated `Center > ConstrainedBox(maxWidth) > Padding > Column`
/// pattern and — critically — does NOT use `CrossAxisAlignment.stretch`, which
/// was the root cause of the "stretched boxes" feeling. Children size naturally
/// within the content column; buttons/inputs breathe instead of spanning edge
/// to edge.
///
/// Pass [maxWidth] to override the default [Layout.contentMaxWidth].
class ScreenScaffold extends StatelessWidget {
  const ScreenScaffold({
    super.key,
    required this.child,
    this.maxWidth = Layout.contentMaxWidth,
    this.padding = const EdgeInsets.symmetric(
      horizontal: Layout.padding,
      vertical: 32,
    ),
    this.alignment = Alignment.center,
  });

  final Widget child;
  final double maxWidth;
  final EdgeInsetsGeometry padding;
  final AlignmentGeometry alignment;

  @override
  Widget build(BuildContext context) {
    return Align(
      alignment: alignment,
      child: ConstrainedBox(
        constraints: BoxConstraints(maxWidth: maxWidth),
        child: Padding(padding: padding, child: child),
      ),
    );
  }
}

/// A scrollable variant for forms longer than the viewport.
class ScrollableScaffold extends StatelessWidget {
  const ScrollableScaffold({
    super.key,
    required this.child,
    this.maxWidth = Layout.contentMaxWidth,
    this.appBar,
    this.padding = const EdgeInsets.symmetric(
      horizontal: Layout.padding,
      vertical: 24,
    ),
  });

  final Widget child;
  final double maxWidth;
  final PreferredSizeWidget? appBar;
  final EdgeInsetsGeometry padding;

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: appBar,
      body: Center(
        child: ConstrainedBox(
          constraints: BoxConstraints(maxWidth: maxWidth),
          child: SingleChildScrollView(
            padding: padding,
            child: child,
          ),
        ),
      ),
    );
  }
}
