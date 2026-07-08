import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:qr_flutter/qr_flutter.dart';

import '../../core/config/app_config.dart';
import '../../core/theme/app_colors.dart';
import '../../models/idea.dart';
import '../../widgets/error_banner.dart';
import '../../widgets/live_indicator.dart';
import 'facilitator_session_controller.dart';

/// Facilitator dashboard — projector-first live workshop control center.
///
/// Two zones: a fixed left rail (join code + QR + live counts) and a
/// vote-sorted, auto-responsive idea feed on the right. Sized for readability
/// from the back of a room. The header + Run Analysis button stay pinned; only
/// the idea grid scrolls.
class FacilitatorDashboardScreen extends ConsumerWidget {
  const FacilitatorDashboardScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final state = ref.watch(facilitatorSessionProvider);
    final session = state.session;
    if (session == null) {
      WidgetsBinding.instance.addPostFrameCallback((_) => context.go('/facilitate/new'));
      return const Scaffold(body: Center(child: CircularProgressIndicator()));
    }

    // Reflect the session topic in the browser tab / app-switcher title so the
    // tab isn't stuck on a generic name while the app bar shows the live topic.
    // (Web: this updates document.title.)
    SystemChrome.setApplicationSwitcherDescription(
      ApplicationSwitcherDescription(label: '${session.topic} · Workshop Tool'),
    );

    final origin = AppConfig.webOrigin;
    final base =
        (origin != null && origin.isNotEmpty) ? origin : AppConfig.apiBaseUrl;
    final joinUrl = '$base/#/join?code=${session.accessCode}';

    // Sort a COPY by votes desc (live re-sorts as votes come in).
    final ideas = [...state.ideas]..sort((a, b) => b.votes.compareTo(a.votes));
    final maxVotes = ideas.isEmpty ? 0 : ideas.first.votes;

    return Scaffold(
      appBar: AppBar(
        title: Text(session.topic),
        actions: [
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 20),
            child: Center(child: LiveIndicator(connected: state.connected)),
          ),
        ],
      ),
      body: SafeArea(
        child: Center(
          child: ConstrainedBox(
            constraints: const BoxConstraints(maxWidth: 1600),
            child: Padding(
              padding: const EdgeInsets.fromLTRB(32, 24, 32, 24),
              child: LayoutBuilder(
                builder: (context, constraints) {
                  final wide = constraints.maxWidth >= 900;
                  final rail = _JoinRail(
                    accessCode: session.accessCode,
                    joinUrl: joinUrl,
                    participantCount: state.participantCount,
                    ideaCount: state.ideas.length,
                  );
                  final feed = _IdeaFeed(
                    state: state,
                    ideas: ideas,
                    maxVotes: maxVotes,
                    onRun: () => _runAnalysis(context, ref),
                    onDismissError: () => ref
                        .read(facilitatorSessionProvider.notifier)
                        .dismissError(),
                    onViewReport: () => context.go('/facilitate/report'),
                  );

                  if (!wide) {
                    return ListView(
                      children: [rail, const SizedBox(height: 24), feed],
                    );
                  }
                  return Row(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      SizedBox(width: 400, child: rail),
                      const SizedBox(width: 32),
                      Expanded(child: feed),
                    ],
                  );
                },
              ),
            ),
          ),
        ),
      ),
    );
  }

  Future<void> _runAnalysis(BuildContext context, WidgetRef ref) async {
    final ok = await ref.read(facilitatorSessionProvider.notifier).runAnalysis();
    if (!context.mounted) return;
    final msg = ok
        ? 'Analysis complete'
        : (ref.read(facilitatorSessionProvider).error ?? 'Analysis failed');
    ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(msg)));
  }
}

// ─────────────────────────────────────────────────────────────────────────
// Left rail: join code + QR + live counts.
// ─────────────────────────────────────────────────────────────────────────
class _JoinRail extends StatelessWidget {
  const _JoinRail({
    required this.accessCode,
    required this.joinUrl,
    required this.participantCount,
    required this.ideaCount,
  });

  final String accessCode;
  final String joinUrl;
  final int participantCount;
  final int ideaCount;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        Card(
          child: Padding(
            padding: const EdgeInsets.all(28),
            child: Column(
              children: [
                Text(
                  'JOIN CODE',
                  style: theme.textTheme.labelSmall
                      ?.copyWith(letterSpacing: 2, color: AppColors.textTertiary),
                ),
                const SizedBox(height: 8),
                SelectableText(
                  accessCode,
                  textAlign: TextAlign.center,
                  style: GoogleFonts.jetBrainsMono(
                    fontSize: 56,
                    height: 1.0,
                    fontWeight: FontWeight.w800,
                    letterSpacing: 5,
                    color: AppColors.navy,
                  ),
                  semanticsLabel: 'Access code: ${accessCode.split('').join(' ')}',
                ),
                const SizedBox(height: 20),
                Container(
                  padding: const EdgeInsets.all(22),
                  decoration: BoxDecoration(
                    color: AppColors.accentSoft,
                    borderRadius: BorderRadius.circular(16),
                  ),
                  child: Column(
                    children: [
                      Semantics(
                        label: 'QR code for participants to join',
                        child: Container(
                          padding: const EdgeInsets.all(12),
                          decoration: BoxDecoration(
                            color: Colors.white,
                            borderRadius: BorderRadius.circular(12),
                          ),
                          child: QrImageView(
                            data: joinUrl,
                            version: QrVersions.auto,
                            size: 200,
                            backgroundColor: Colors.white,
                          ),
                        ),
                      ),
                      const SizedBox(height: 14),
                      Text(
                        'Scan to join',
                        style: theme.textTheme.titleMedium
                            ?.copyWith(color: AppColors.textSecondary),
                      ),
                    ],
                  ),
                ),
              ],
            ),
          ),
        ),
        const SizedBox(height: 18),
        Row(
          children: [
            Expanded(child: _StatTile(label: 'People', value: participantCount)),
            const SizedBox(width: 16),
            Expanded(child: _StatTile(label: 'Ideas', value: ideaCount)),
          ],
        ),
      ],
    );
  }
}

class _StatTile extends StatelessWidget {
  const _StatTile({required this.label, required this.value});
  final String label;
  final int value;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Card(
      child: Padding(
        padding: const EdgeInsets.symmetric(vertical: 20, horizontal: 16),
        child: Column(
          children: [
            Text(
              '$value',
              style: theme.textTheme.displayMedium
                  ?.copyWith(color: AppColors.navy),
            ),
            const SizedBox(height: 6),
            Text(
              label.toUpperCase(),
              style: theme.textTheme.labelSmall
                  ?.copyWith(letterSpacing: 1, color: AppColors.textSecondary),
            ),
          ],
        ),
      ),
    );
  }
}

// ─────────────────────────────────────────────────────────────────────────
// Right column: header (pinned) + scrolling responsive grid + Run button.
// ─────────────────────────────────────────────────────────────────────────
class _IdeaFeed extends StatelessWidget {
  const _IdeaFeed({
    required this.state,
    required this.ideas,
    required this.maxVotes,
    required this.onRun,
    required this.onDismissError,
    required this.onViewReport,
  });

  final FacilitatorSessionState state;
  final List<Idea> ideas;
  final int maxVotes;
  final VoidCallback onRun;
  final VoidCallback onDismissError;
  final VoidCallback onViewReport;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final count = ideas.length;

    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        if (state.error != null)
          Padding(
            padding: const EdgeInsets.only(bottom: 16),
            child:
                ErrorBanner(message: state.error!, onDismiss: onDismissError),
          ),

        // Header (pinned). The live indicator lives in the app bar only — no
        // duplicate here.
        Row(
          children: [
            Expanded(
              child: Text(
                count == 0 ? 'Waiting for ideas' : '$count ideas so far',
                style: theme.textTheme.displaySmall,
              ),
            ),
            if (count > 0) ...[
              _Pill(
                icon: Icons.arrow_upward_rounded,
                label: 'Most voted',
                color: AppColors.textSecondary,
              ),
              const SizedBox(width: 12),
            ],
          ],
        ),
        const SizedBox(height: 18),

        // Scrolling grid.
        Expanded(
          child: count == 0
              ? const _EmptyFeed()
              : LayoutBuilder(
                  builder: (context, c) {
                    // Auto columns: adapt to width AND count. Max card width
                    // ~360px keeps text legible; more ideas => more columns.
                    final byWidth = (c.maxWidth / 360).floor().clamp(1, 4);
                    final byCount = count <= 4 ? 2 : (count <= 12 ? 3 : 4);
                    final cols = byWidth < byCount ? byWidth : byCount;
                    // Nudge text down as the grid gets denser.
                    final fontSize =
                        count <= 6 ? 21.0 : (count <= 12 ? 18.0 : 16.0);

                    return GridView.builder(
                      padding:
                          const EdgeInsets.only(top: 4, right: 4, bottom: 4),
                      gridDelegate:
                          SliverGridDelegateWithFixedCrossAxisCount(
                        crossAxisCount: cols,
                        crossAxisSpacing: 16,
                        mainAxisSpacing: 16,
                        mainAxisExtent: 168,
                      ),
                      itemCount: count,
                      itemBuilder: (context, i) {
                        final idea = ideas[i];
                        return _IdeaCard(
                          text: idea.content,
                          authorName: idea.participantName,
                          votes: idea.votes,
                          isTop: maxVotes > 0 && idea.votes == maxVotes,
                          fontSize: fontSize,
                        );
                      },
                    );
                  },
                ),
        ),

        const SizedBox(height: 18),

        // Run analysis (pinned).
        FilledButton.icon(
          onPressed: (state.analysing || count == 0) ? null : onRun,
          icon: state.analysing
              ? const SizedBox(
                  width: 20,
                  height: 20,
                  child: CircularProgressIndicator(
                      strokeWidth: 2, color: Colors.white),
                )
              : const Icon(Icons.auto_awesome_rounded),
          label: Text(state.analysing ? 'Analysing…' : 'Run AI analysis'),
        ),
        if (count == 0)
          Padding(
            padding: const EdgeInsets.only(top: 8),
            child: Text(
              'Add at least one idea before running analysis.',
              textAlign: TextAlign.center,
              style: theme.textTheme.bodySmall,
            ),
          ),
        if (state.analysis != null)
          Padding(
            padding: const EdgeInsets.only(top: 12),
            child: OutlinedButton.icon(
              onPressed: onViewReport,
              icon: const Icon(Icons.analytics_outlined),
              label: const Text('View analysis & download PDF'),
            ),
          ),
      ],
    );
  }
}

/// A single idea card. The "TOP VOTED" badge is an IN-FLOW child at the top of
/// the card (not a Positioned/overhang) — nothing extends beyond the card
/// bounds, so it can never be clipped by the scroll viewport.
class _IdeaCard extends StatelessWidget {
  const _IdeaCard({
    required this.text,
    required this.authorName,
    required this.votes,
    required this.isTop,
    required this.fontSize,
  });

  final String text;
  final String authorName;
  final int votes;
  final bool isTop;
  final double fontSize;

  String get _initials {
    final parts = authorName.trim().split(RegExp(r'\s+'));
    if (parts.isEmpty || parts.first.isEmpty) return '?';
    if (parts.length == 1) {
      return parts.first.characters.first.toUpperCase();
    }
    return (parts.first.characters.first + parts.last.characters.first)
        .toUpperCase();
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final edge = isTop ? AppColors.gold : AppColors.accent;

    return Container(
      decoration: BoxDecoration(
        color: AppColors.surface,
        borderRadius: BorderRadius.circular(14),
        border: Border(
          left: BorderSide(color: edge, width: 6),
          top: BorderSide(color: isTop ? AppColors.gold : AppColors.border, width: 2),
          right:
              BorderSide(color: isTop ? AppColors.gold : AppColors.border, width: 2),
          bottom:
              BorderSide(color: isTop ? AppColors.gold : AppColors.border, width: 2),
        ),
        boxShadow: const [
          BoxShadow(
            color: AppColors.shadowOuter,
            blurRadius: 8,
            offset: Offset(0, 3),
          ),
        ],
      ),
      child: Padding(
        padding: const EdgeInsets.fromLTRB(16, 12, 14, 12),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // In-flow badge — never clipped by the viewport.
            Row(
              children: [
                if (isTop) ...[
                  Container(
                    padding:
                        const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                    decoration: BoxDecoration(
                      color: AppColors.goldSoft,
                      borderRadius: BorderRadius.circular(6),
                      border: Border.all(color: AppColors.gold, width: 1.5),
                    ),
                    child: Row(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        const Icon(Icons.arrow_upward_rounded,
                            size: 13, color: AppColors.gold),
                        const SizedBox(width: 3),
                        Text(
                          'TOP VOTED',
                          style: theme.textTheme.labelSmall?.copyWith(
                            color: AppColors.gold,
                            fontWeight: FontWeight.w800,
                            letterSpacing: 0.8,
                          ),
                        ),
                      ],
                    ),
                  ),
                  const Spacer(),
                ] else
                  const Spacer(),
                CircleAvatar(
                  radius: 14,
                  backgroundColor: AppColors.accentSoft,
                  child: Text(
                    _initials,
                    style: theme.textTheme.labelSmall
                        ?.copyWith(color: AppColors.accent),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 10),
            Expanded(
              child: Text(
                text,
                style: theme.textTheme.bodyLarge?.copyWith(
                  fontSize: fontSize,
                  height: 1.3,
                  fontWeight: FontWeight.w600,
                  color: AppColors.textPrimary,
                ),
                maxLines: 4,
                overflow: TextOverflow.ellipsis,
              ),
            ),
            const SizedBox(height: 8),
            Row(
              children: [
                Icon(Icons.arrow_upward_rounded,
                    size: 16, color: AppColors.vote),
                const SizedBox(width: 4),
                Text(
                  '$votes',
                  style: theme.textTheme.titleMedium
                      ?.copyWith(color: AppColors.vote),
                ),
                const Spacer(),
                Text(
                  authorName,
                  style: theme.textTheme.labelSmall,
                  overflow: TextOverflow.ellipsis,
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }
}

/// The empty state for the idea grid.
class _EmptyFeed extends StatelessWidget {
  const _EmptyFeed();

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Center(
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(Icons.lightbulb_outline_rounded,
              size: 56, color: AppColors.textTertiary),
          const SizedBox(height: 12),
          Text(
            'No ideas yet',
            style: theme.textTheme.titleLarge,
          ),
          const SizedBox(height: 4),
          Text(
            'Share the access code or QR to invite participants.',
            textAlign: TextAlign.center,
            style: theme.textTheme.bodySmall,
          ),
        ],
      ),
    );
  }
}

/// A small pill chip for the header.
class _Pill extends StatelessWidget {
  const _Pill({
    required this.icon,
    required this.label,
    required this.color,
  });

  final IconData icon;
  final String label;
  final Color color;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
      decoration: BoxDecoration(
        color: AppColors.surfaceRaised,
        borderRadius: BorderRadius.circular(20),
        border: Border.all(color: AppColors.border, width: 2),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(icon, size: 14, color: color),
          const SizedBox(width: 4),
          Text(
            label,
            style: theme.textTheme.labelSmall?.copyWith(color: color),
          ),
        ],
      ),
    );
  }
}
