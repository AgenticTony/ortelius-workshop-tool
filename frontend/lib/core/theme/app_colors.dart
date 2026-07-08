import 'package:flutter/material.dart';

/// Workshop Tool palette — "Light, corporate, projector-first."
///
/// A bright neutral canvas that holds contrast under room lighting and on
/// shared TVs/projectors (dark themes wash out and glare in lit rooms).
/// One disciplined brand accent (teal) + a deep navy for headline numbers.
///
/// Swap `accent` / `navy` for official Ortelius brand colors when available —
/// nothing else needs to change.
abstract class AppColors {
  AppColors._();

  // ── Core surfaces ──────────────────────────────────────────────────────
  static const canvas = Color(0xFFF4F7FA); // app background
  static const surface = Color(0xFFFFFFFF); // cards
  static const surfaceRaised = Color(0xFFEFF3F8); // inputs / hovered tiles
  static const border = Color(0xFFD8E0EA); // 2px card borders
  static const borderStrong = Color(0xFFB9C6D6);

  // ── Text (high contrast for back-of-room legibility) ───────────────────
  static const textPrimary = Color(0xFF0B1524);
  static const textSecondary = Color(0xFF3E4E63);
  static const textTertiary = Color(0xFF7A8AA0);

  // ── Brand accent ───────────────────────────────────────────────────────
  static const accent = Color(0xFF0E7C7B); // teal — primary actions
  static const accentDeep = Color(0xFF0A5F5E); // hover/pressed
  static const accentSoft = Color(0xFFE2F1F0); // tint fills
  static const navy = Color(0xFF12324A); // headline numbers / code

  // ── Semantic ───────────────────────────────────────────────────────────
  static const live = Color(0xFF0E9E4A);
  static const danger = Color(0xFFD1342B);
  static const vote = Color(0xFFC8720A); // amber vote pill
  static const voteSoft = Color(0xFFFBF0E0);
  static const gold = Color(0xFFB8860B); // top-voted highlight
  static const goldSoft = Color(0xFFFBF3DE);

  // ── Sticky note fills ──────────────────────────────────────────────────
  static const stickyNote = Color(0xFFFFFFFF);
  static const stickyNoteMine = Color(0xFFF3F9F9);

  // ── Backward-compat aliases ────────────────────────────────────────────
  // The dark-theme motion layer referenced these. On light, the glass/glow
  // effects are gone (they don't read on a bright canvas), so these aliases
  // route to the closest equivalent so untouched widgets still compile and
  // look right. New code should prefer the named tokens above.
  static const accentMuted = accentSoft;
  static const shadowOuter = Color(0x1A0B1524); // ~10% ink, soft
  static const shadowOuterStrong = Color(0x330B1524);
  static const glassHighlight = Color(0x66FFFFFF);
  static const accentGlow = Color(0x330E7C7B);
  static const canvasTop = canvas;
  static const canvasBottom = canvas;

  // ── ColorScheme (light) ────────────────────────────────────────────────
  static const scheme = ColorScheme(
    brightness: Brightness.light,
    primary: accent,
    onPrimary: Color(0xFFFFFFFF),
    primaryContainer: accentSoft,
    onPrimaryContainer: accentDeep,
    secondary: vote,
    onSecondary: Color(0xFFFFFFFF),
    secondaryContainer: voteSoft,
    onSecondaryContainer: Color(0xFF5C3400),
    tertiary: navy,
    onTertiary: Color(0xFFFFFFFF),
    error: danger,
    onError: Color(0xFFFFFFFF),
    errorContainer: Color(0xFFFCE4E2),
    onErrorContainer: Color(0xFF5C1512),
    surface: surface,
    onSurface: textPrimary,
    surfaceContainerLowest: Color(0xFFFFFFFF),
    surfaceContainerLow: canvas,
    surfaceContainer: surfaceRaised,
    surfaceContainerHigh: Color(0xFFE7EDF4),
    surfaceContainerHighest: Color(0xFFDFE7F0),
    onSurfaceVariant: textSecondary,
    outline: border,
    outlineVariant: Color(0xFFE7EDF4),
    scrim: Color(0x66000000),
  );
}
