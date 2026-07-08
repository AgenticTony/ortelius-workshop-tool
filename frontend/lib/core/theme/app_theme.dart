import 'package:flutter/material.dart';

import 'app_colors.dart';
import 'app_typography.dart';

/// Workshop Tool theme — light, corporate, high-contrast.
///
/// Projector-first: built for a facilitator displaying this on a shared
/// screen in a lit room, where back-of-room legibility is the job. Depth via
/// soft shadows + 2px borders (not glassmorphism — glass washes out on a
/// bright projector). Larger radii and taller controls for touch + distance.
class AppTheme {
  AppTheme._();

  static ThemeData build() {
    final colors = AppColors.scheme;
    final text = AppTypography.build();

    return ThemeData(
      useMaterial3: true,
      brightness: Brightness.light,
      colorScheme: colors,
      textTheme: text,
      scaffoldBackgroundColor: AppColors.canvas,

      // ── App bar: solid surface, 2px divider ───────────────────────────
      appBarTheme: AppBarTheme(
        centerTitle: false,
        backgroundColor: AppColors.surface,
        surfaceTintColor: Colors.transparent,
        foregroundColor: AppColors.textPrimary,
        elevation: 0,
        scrolledUnderElevation: 0,
        titleTextStyle:
            text.headlineMedium?.copyWith(color: AppColors.textPrimary),
        shape: const Border(
            bottom: BorderSide(color: AppColors.border, width: 2)),
      ),

      // ── Cards: solid white, 2px border, soft shadow ───────────────────
      cardTheme: CardThemeData(
        elevation: 0,
        color: AppColors.surface,
        surfaceTintColor: Colors.transparent,
        shadowColor: const Color(0x1A0B1524),
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(16),
          side: const BorderSide(color: AppColors.border, width: 2),
        ),
        margin: EdgeInsets.zero,
      ),

      // ── Inputs: filled, 2px border, accent focus ──────────────────────
      inputDecorationTheme: InputDecorationTheme(
        filled: true,
        fillColor: AppColors.surface,
        contentPadding:
            const EdgeInsets.symmetric(horizontal: 16, vertical: 15),
        border: OutlineInputBorder(
          borderRadius: BorderRadius.circular(12),
          borderSide: const BorderSide(color: AppColors.border, width: 2),
        ),
        enabledBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(12),
          borderSide: const BorderSide(color: AppColors.border, width: 2),
        ),
        focusedBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(12),
          borderSide: const BorderSide(color: AppColors.accent, width: 2.5),
        ),
        errorBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(12),
          borderSide: const BorderSide(color: AppColors.danger, width: 2),
        ),
        labelStyle:
            text.bodyMedium?.copyWith(color: AppColors.textSecondary),
        hintStyle: text.bodyMedium?.copyWith(color: AppColors.textTertiary),
      ),

      // ── Buttons: 54px tall, 14px radius ───────────────────────────────
      filledButtonTheme: FilledButtonThemeData(
        style: FilledButton.styleFrom(
          minimumSize: const Size(0, 54),
          padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 16),
          backgroundColor: AppColors.accent,
          foregroundColor: Colors.white,
          textStyle: text.labelLarge,
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(14)),
          elevation: 0,
        ),
      ),
      outlinedButtonTheme: OutlinedButtonThemeData(
        style: OutlinedButton.styleFrom(
          minimumSize: const Size(0, 54),
          foregroundColor: AppColors.accent,
          textStyle: text.labelLarge,
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(14)),
          side: const BorderSide(color: AppColors.border, width: 2),
        ),
      ),
      textButtonTheme: TextButtonThemeData(
        style: TextButton.styleFrom(
            foregroundColor: AppColors.accent, textStyle: text.labelLarge),
      ),
      iconButtonTheme: IconButtonThemeData(
        style: IconButton.styleFrom(
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
          side: const BorderSide(color: AppColors.border, width: 2),
        ),
      ),

      // ── Misc ──────────────────────────────────────────────────────────
      dividerTheme:
          const DividerThemeData(color: AppColors.border, thickness: 2, space: 2),
      snackBarTheme: SnackBarThemeData(
        behavior: SnackBarBehavior.floating,
        backgroundColor: AppColors.navy,
        contentTextStyle: text.bodyMedium?.copyWith(color: Colors.white),
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
      ),
      progressIndicatorTheme:
          const ProgressIndicatorThemeData(color: AppColors.accent),
      radioTheme: RadioThemeData(
        fillColor: WidgetStateProperty.resolveWith((states) {
          if (states.contains(WidgetState.selected)) return AppColors.accent;
          return AppColors.textTertiary;
        }),
      ),
      switchTheme: SwitchThemeData(
        thumbColor: WidgetStateProperty.resolveWith((states) {
          if (states.contains(WidgetState.selected)) return Colors.white;
          return AppColors.textTertiary;
        }),
        trackColor: WidgetStateProperty.resolveWith((states) {
          if (states.contains(WidgetState.selected)) return AppColors.accent;
          return AppColors.surfaceRaised;
        }),
      ),
    );
  }
}
