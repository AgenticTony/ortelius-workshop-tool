import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

import '../../core/theme/app_colors.dart';
import '../../widgets/screen_scaffold.dart';

/// App entry screen: pick facilitator or participant.
///
/// The hero is the thesis — a large display wordmark + a one-line description
/// of what the tool does. Two role tiles sit below, side by side on wide
/// screens, stacked on phones. No stretched buttons: each tile is a real card
/// with its own identity, not an edge-to-edge strip.
class HomeScreen extends StatelessWidget {
  const HomeScreen({super.key});

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Scaffold(
      body: SafeArea(
        child: ScreenScaffold(
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            crossAxisAlignment: CrossAxisAlignment.center,
            children: [
              // ── Hero: the app's thesis ──────────────────────────────
              Container(
                width: 64,
                height: 64,
                decoration: BoxDecoration(
                  color: AppColors.accent.withValues(alpha: 0.12),
                  borderRadius: BorderRadius.circular(14),
                ),
                child: const Icon(
                  Icons.forum_rounded,
                  size: 32,
                  color: AppColors.accent,
                ),
              ),
              const SizedBox(height: 24),
              Text(
                'Workshop Tool',
                textAlign: TextAlign.center,
                style: theme.textTheme.displaySmall?.copyWith(
                  color: theme.colorScheme.onSurface,
                ),
              ),
              const SizedBox(height: 10),
              Text(
                'Capture, cluster, and report\nworkshop ideas — live.',
                textAlign: TextAlign.center,
                style: theme.textTheme.bodyLarge?.copyWith(
                  color: theme.colorScheme.onSurfaceVariant,
                  height: 1.5,
                ),
              ),
              const SizedBox(height: 40),

              // ── Role tiles ──────────────────────────────────────────
              // Stacked vertically — identical, robust layout on every width.
              _RoleTile(
                icon: Icons.add_rounded,
                title: 'Start a session',
                subtitle: 'Create a workshop as facilitator',
                onTap: () => context.go('/facilitate/new'),
                primary: true,
              ),
              const SizedBox(height: 12),
              _RoleTile(
                icon: Icons.login_rounded,
                title: 'Join a session',
                subtitle: 'Enter an access code',
                onTap: () => context.go('/join'),
              ),
              const SizedBox(height: 20),
              TextButton(
                onPressed: () => context.go('/health'),
                child: Text(
                  'Check backend connection',
                  style: theme.textTheme.labelLarge?.copyWith(
                    color: theme.colorScheme.onSurfaceVariant,
                  ),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

/// A role-selection tile — a real card with icon + label, not a stretched bar.
class _RoleTile extends StatelessWidget {
  const _RoleTile({
    required this.icon,
    required this.title,
    required this.subtitle,
    required this.onTap,
    this.primary = false,
  });

  final IconData icon;
  final String title;
  final String subtitle;
  final VoidCallback onTap;
  final bool primary;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return SizedBox(
      width: double.infinity, // fill the centered column on every width
      child: Material(
        color: primary
            ? AppColors.accent
            : theme.colorScheme.surface,
        borderRadius: BorderRadius.circular(16),
        child: InkWell(
          onTap: onTap,
          borderRadius: BorderRadius.circular(16),
          child: Container(
            constraints: const BoxConstraints(minHeight: 88),
            padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 16),
            decoration: BoxDecoration(
              borderRadius: BorderRadius.circular(16),
              border: primary
                  ? null
                  : Border.all(color: theme.colorScheme.outline),
            ),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                Icon(
                  icon,
                  size: 24,
                  color: primary
                      ? Colors.white
                      : theme.colorScheme.onSurface,
                ),
              const SizedBox(height: 12),
                Text(
                  title,
                  style: theme.textTheme.titleMedium?.copyWith(
                    color: primary ? Colors.white : theme.colorScheme.onSurface,
                  ),
                ),
                const SizedBox(height: 2),
                Text(
                  subtitle,
                  style: theme.textTheme.bodySmall?.copyWith(
                    color: primary
                        ? Colors.white.withValues(alpha: 0.85)
                        : theme.colorScheme.onSurfaceVariant,
                  ),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}
