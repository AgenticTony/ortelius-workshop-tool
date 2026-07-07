import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';

import 'app_colors.dart';

/// Workshop Tool typography — "Dark, technical, corporate."
///
/// Two faces, used with discipline:
///  - Inter for everything — body, headings, UI. Tightened tracking on
///    headings gives it a product/tool feel without a "designed" display face.
///  - JetBrains Mono for the access code and numeric/data labels only — the
///    mono texture is what signals "technical" (terminals, IDEs, dashboards).
///
/// Avoiding a separate characterful display face (Space Grotesk etc.) keeps
/// this from reading as a templated portfolio site. One family, well-set.
abstract class AppTypography {
  AppTypography._();

  static TextTheme build() {
    final base = GoogleFonts.inter(
      color: AppColors.textPrimary,
    );
    return TextTheme(
      // Display — Inter, tight tracking, semibold. No characterful face.
      displayLarge: base.copyWith(fontSize: 42, height: 1.1, fontWeight: FontWeight.w700, letterSpacing: -0.5),
      displayMedium: base.copyWith(fontSize: 32, height: 1.15, fontWeight: FontWeight.w700, letterSpacing: -0.4),
      displaySmall: base.copyWith(fontSize: 26, height: 1.2, fontWeight: FontWeight.w600, letterSpacing: -0.3),
      headlineLarge: base.copyWith(fontSize: 22, height: 1.25, fontWeight: FontWeight.w600),
      headlineMedium: base.copyWith(fontSize: 20, height: 1.3, fontWeight: FontWeight.w600),
      headlineSmall: base.copyWith(fontSize: 18, height: 1.35, fontWeight: FontWeight.w600),
      // Title — screen / section headers.
      titleLarge: base.copyWith(fontSize: 17, height: 1.3, fontWeight: FontWeight.w600),
      titleMedium: base.copyWith(fontSize: 15, height: 1.4, fontWeight: FontWeight.w600),
      titleSmall: base.copyWith(fontSize: 13, height: 1.4, fontWeight: FontWeight.w600),
      // Body.
      bodyLarge: base.copyWith(fontSize: 15, height: 1.55, color: AppColors.textPrimary),
      bodyMedium: base.copyWith(fontSize: 14, height: 1.5, color: AppColors.textPrimary),
      bodySmall: base.copyWith(fontSize: 13, height: 1.5, color: AppColors.textSecondary),
      // Labels — uppercase eyebrows, meta. Medium weight, slight tracking.
      labelLarge: base.copyWith(fontSize: 14, fontWeight: FontWeight.w600, letterSpacing: 0.1),
      labelMedium: base.copyWith(fontSize: 12, fontWeight: FontWeight.w500, letterSpacing: 0.3, color: AppColors.textSecondary),
      labelSmall: base.copyWith(fontSize: 11, fontWeight: FontWeight.w500, letterSpacing: 0.5, color: AppColors.textSecondary),
    );
  }

  /// Mono face — exposed for the access code + numeric stats.
  /// Use sparingly; it's the technical-texture accent.
  static TextStyle mono({double size = 14, FontWeight weight = FontWeight.w500, Color color = AppColors.textPrimary}) {
    return GoogleFonts.jetBrainsMono(
      fontSize: size,
      fontWeight: weight,
      color: color,
      letterSpacing: 0.2,
    );
  }
}
