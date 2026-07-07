import 'package:flutter/material.dart';

/// Workshop Tool palette — "Dark, technical, corporate."
///
/// A near-black slate canvas with one disciplined accent. The register is
/// Linear / Vercel / Raycast: a serious tool that earns trust by being quiet
/// and precise, not by decorating. No warm off-white, no templated gradients.
abstract class AppColors {
  AppColors._();

  // ── Core surfaces (dark slate, cool not flat-black) ───────────────────
  /// App background — deep slate (#0B0F17). Not pure black; pure black
  /// flattens depth and looks harsh. Slate gives the surface a substrate.
  static const canvas = Color(0xFF0B0F17);

  /// Primary card / elevated surface.
  static const surface = Color(0xFF141A24);

  /// Higher-elevation surface (inputs, hovered tiles).
  static const surfaceRaised = Color(0xFF1C2330);

  /// Hairline borders — barely visible, just enough to define edges.
  static const border = Color(0xFF242C3A);

  /// Stronger border for focus / active states.
  static const borderStrong = Color(0xFF3A4555);

  // ── Text ──────────────────────────────────────────────────────────────
  /// Primary text — high-contrast off-white (#E6EAF0). Not pure white;
  /// pure white on dark is glaring and reduces legibility at length.
  static const textPrimary = Color(0xFFE6EAF0);

  /// Secondary text — labels, captions, metadata.
  static const textSecondary = Color(0xFF8B95A7);

  /// Tertiary / disabled.
  static const textTertiary = Color(0xFF5B6577);

  // ── Accent (one disciplined color — the whole brand) ─────────────────
  /// Indigo (#5B7CFA). Used for primary actions, active states, focus rings.
  /// Picked to read as "technical / product" on dark, not playful.
  static const accent = Color(0xFF5B7CFA);

  /// Accent at lower opacity for fills (primary-container equivalent).
  static const accentMuted = Color(0xFF1E2A4A);

  // ── Semantic ──────────────────────────────────────────────────────────
  /// Live / connected / success — emerald, used ONLY for the live indicator
  /// and success states. Never decorative.
  static const live = Color(0xFF10B981);

  /// Error / destructive.
  static const danger = Color(0xFFEF4444);

  /// Vote / highlight on sticky notes — kept as a quiet amber, not the brand.
  static const vote = Color(0xFFF59E0B);

  // ── ColorScheme (assembled for Material components) ──────────────────
  // Dark-only by design — see main.dart (no themeMode flip).
  static const scheme = ColorScheme(
    brightness: Brightness.dark,
    primary: accent,
    onPrimary: Color(0xFFFFFFFF),
    primaryContainer: accentMuted,
    onPrimaryContainer: Color(0xFFB4C5FF),
    secondary: vote,
    onSecondary: Color(0xFF1A1300),
    secondaryContainer: Color(0xFF2A1F08),
    onSecondaryContainer: Color(0xFFFDE68A),
    tertiary: Color(0xFF64748B),
    onTertiary: Color(0xFFFFFFFF),
    error: danger,
    onError: Color(0xFFFFFFFF),
    errorContainer: Color(0xFF3B1414),
    onErrorContainer: Color(0xFFFECACA),
    surface: surface,
    onSurface: textPrimary,
    surfaceContainerLowest: canvas,
    surfaceContainerLow: surface,
    surfaceContainer: surfaceRaised,
    surfaceContainerHigh: Color(0xFF222B3B),
    surfaceContainerHighest: Color(0xFF2A3447),
    onSurfaceVariant: textSecondary,
    outline: border,
    outlineVariant: Color(0xFF1A212C),
    scrim: Color(0xCC000000),
  );

  // ── Sticky note fills (the one warm touch — restrained) ──────────────
  /// Others' idea notes — subtle warm tint on dark.
  static const stickyNote = Color(0xFF1A1F2E);

  /// Your-own idea note — slightly warmer to mark it.
  static const stickyNoteMine = Color(0xFF24200C);
}
