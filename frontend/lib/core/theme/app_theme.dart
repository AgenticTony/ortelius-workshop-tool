import 'package:flutter/material.dart';

/// App-wide Material 3 theme. Kept intentionally simple for the scaffold;
/// brand colors and typography land in the polish milestone.
ThemeData appTheme() {
  final colorScheme = ColorScheme.fromSeed(
    seedColor: const Color(0xFF2E5C8A),
    brightness: Brightness.light,
  );
  return ThemeData(
    colorScheme: colorScheme,
    useMaterial3: true,
    appBarTheme: AppBarTheme(
      centerTitle: false,
      backgroundColor: colorScheme.surface,
      foregroundColor: colorScheme.onSurface,
      elevation: 0,
      scrolledUnderElevation: 2,
    ),
    cardTheme: const CardThemeData(
      elevation: 1,
      margin: EdgeInsets.symmetric(vertical: 6, horizontal: 0),
    ),
  );
}
