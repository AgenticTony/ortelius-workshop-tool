/// Shared layout constants — one content rhythm applied everywhere.
///
/// The old screens sprinkled literal 16 / 24 / 32 paddings and 480 / 560 /
/// unbounded max-widths. This gives every screen a single source of truth.
class Layout {
  Layout._();

  // ── Spacing scale ──────────────────────────────────────────────────────
  /// Standard horizontal padding around screen content.
  static const double padding = 20.0;

  /// Standard gap between stacked sections.
  static const double sectionGap = 16.0;

  /// Smaller gap between tightly-related items.
  static const double itemGap = 8.0;

  // ── Max content widths ─────────────────────────────────────────────────
  /// Max width for form / centered screens (home, join, create, health).
  static const double contentMaxWidth = 460.0;

  /// Max width for data-rich screens (dashboard, report) — readable on desktop.
  static const double dashboardMaxWidth = 760.0;
}
