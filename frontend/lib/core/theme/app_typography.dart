import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';

import 'app_colors.dart';

/// Typography — "Light, corporate, projector-first."
///
/// Inter for everything (heavier weights than a normal web app so text reads
/// from the back of a room). JetBrains Mono reserved for the join code only.
abstract class AppTypography {
  AppTypography._();

  static TextTheme build() {
    final base = GoogleFonts.inter(color: AppColors.textPrimary);
    return TextTheme(
      displayLarge: base.copyWith(
          fontSize: 44, height: 1.05, fontWeight: FontWeight.w900, letterSpacing: -0.5),
      displayMedium: base.copyWith(
          fontSize: 34, height: 1.1, fontWeight: FontWeight.w900, letterSpacing: -0.4),
      displaySmall: base.copyWith(
          fontSize: 28, height: 1.15, fontWeight: FontWeight.w800, letterSpacing: -0.3),
      headlineLarge:
          base.copyWith(fontSize: 24, height: 1.2, fontWeight: FontWeight.w800),
      headlineMedium:
          base.copyWith(fontSize: 20, height: 1.25, fontWeight: FontWeight.w800),
      headlineSmall:
          base.copyWith(fontSize: 18, height: 1.3, fontWeight: FontWeight.w700),
      titleLarge:
          base.copyWith(fontSize: 18, height: 1.3, fontWeight: FontWeight.w700),
      titleMedium:
          base.copyWith(fontSize: 16, height: 1.35, fontWeight: FontWeight.w700),
      titleSmall:
          base.copyWith(fontSize: 14, height: 1.4, fontWeight: FontWeight.w700),
      bodyLarge:
          base.copyWith(fontSize: 18, height: 1.4, fontWeight: FontWeight.w600),
      bodyMedium: base.copyWith(fontSize: 15, height: 1.45),
      bodySmall: base.copyWith(
          fontSize: 14, height: 1.45, color: AppColors.textSecondary),
      labelLarge: base.copyWith(
          fontSize: 16, fontWeight: FontWeight.w800, letterSpacing: 0.2),
      labelMedium: base.copyWith(
          fontSize: 14,
          fontWeight: FontWeight.w700,
          letterSpacing: 0.3,
          color: AppColors.textSecondary),
      labelSmall: base.copyWith(
          fontSize: 13,
          fontWeight: FontWeight.w700,
          letterSpacing: 0.6,
          color: AppColors.textTertiary),
    );
  }

  /// Mono — join code + numeric data only.
  static TextStyle mono({
    double size = 14,
    FontWeight weight = FontWeight.w800,
    Color color = AppColors.navy,
  }) {
    return GoogleFonts.jetBrainsMono(
        fontSize: size, fontWeight: weight, color: color, letterSpacing: 2);
  }
}
