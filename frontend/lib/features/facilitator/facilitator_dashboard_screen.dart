import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:qr_flutter/qr_flutter.dart';

import '../../core/config/app_config.dart';
import '../../core/theme/app_colors.dart';
import '../../core/theme/layout.dart';
import '../../widgets/empty_state.dart';
import '../../widgets/error_banner.dart';
import '../../widgets/glass_card.dart';
import '../../widgets/live_indicator.dart';
import '../../widgets/section_heading.dart';
import '../../widgets/staggered_reveal.dart';
import '../../widgets/sticky_note.dart';
import 'facilitator_session_controller.dart';

/// Facilitator dashboard: the live workshop control center. Shows the access
/// code + QR for participants to join, live participant/idea counts, the live
/// idea feed (as sticky notes), and the trigger to run AI analysis.
class FacilitatorDashboardScreen extends ConsumerWidget {
  const FacilitatorDashboardScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final state = ref.watch(facilitatorSessionProvider);
    final session = state.session;
    if (session == null) {
      // No active session — bounce to create.
      WidgetsBinding.instance.addPostFrameCallback((_) => context.go('/facilitate/new'));
      return const Scaffold(body: Center(child: CircularProgressIndicator()));
    }
    final theme = Theme.of(context);

    // The QR encodes a join URL participants can scan with their phone.
    final origin = AppConfig.webOrigin;
    final base = (origin != null && origin.isNotEmpty)
        ? origin
        : AppConfig.apiBaseUrl;
    final joinUrl = '$base/#/join?code=${session.accessCode}';

    return Scaffold(
      appBar: AppBar(
        title: Text(session.topic),
        actions: [
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 16),
            child: Center(child: LiveIndicator(connected: state.connected)),
          ),
        ],
      ),
      body: Center(
        child: ConstrainedBox(
          constraints: const BoxConstraints(maxWidth: Layout.dashboardMaxWidth),
          child: ListView(
            padding: const EdgeInsets.symmetric(
                horizontal: Layout.padding, vertical: 20),
            children: [
              if (state.error != null)
                ErrorBanner(
                  message: state.error!,
                  onDismiss: () => ref
                      .read(facilitatorSessionProvider.notifier)
                      .dismissError(),
                ),

              // ── Access code + QR ────────────────────────────────────
              StaggeredReveal(
                index: 0,
                child: _AccessCodeCard(
                    accessCode: session.accessCode, joinUrl: joinUrl),
              ),
              const SizedBox(height: Layout.sectionGap),

              // ── Live counts ────────────────────────────────────────
              StaggeredReveal(
                index: 1,
                child: Row(
                  children: [
                    _StatTile(
                      icon: Icons.group_rounded,
                      label: 'Participants',
                      value: state.participantCount,
                    ),
                    const SizedBox(width: 12),
                    _StatTile(
                      icon: Icons.lightbulb_rounded,
                      label: 'Ideas',
                      value: state.ideas.length,
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 24),

              // ── Live idea feed ──────────────────────────────────────
              SectionHeading(
                eyebrow: 'Live',
                title: state.ideas.isEmpty
                    ? 'Waiting for ideas'
                    : '${state.ideas.length} idea${state.ideas.length == 1 ? '' : 's'}',
              ),
              const SizedBox(height: 12),
              if (state.ideas.isEmpty)
                const EmptyState(
                  icon: Icons.lightbulb_outline_rounded,
                  message: 'No ideas yet',
                  detail: 'Share the access code or QR to invite participants.',
                )
              else
                ...state.ideas.map((idea) => StickyNote(
                      idea: idea,
                      isMine: false,
                      onVote: () {},
                    )),
              const SizedBox(height: 28),

              // ── Run analysis ────────────────────────────────────────
              _AnalysisControl(state: state, onRun: () => _runAnalysis(context, ref)),
              if (state.ideas.isEmpty)
                Padding(
                  padding: const EdgeInsets.only(top: 8),
                  child: Text(
                    'Add at least one idea before running analysis.',
                    textAlign: TextAlign.center,
                    style: theme.textTheme.bodySmall?.copyWith(
                      color: theme.colorScheme.onSurfaceVariant,
                    ),
                  ),
                ),
              if (state.analysis != null)
                Padding(
                  padding: const EdgeInsets.only(top: 12),
                  child: OutlinedButton.icon(
                    onPressed: () => context.go('/facilitate/report'),
                    icon: const Icon(Icons.analytics_outlined),
                    label: const Text('View analysis & download PDF'),
                  ),
                ),
            ],
          ),
        ),
      ),
    );
  }

  Future<void> _runAnalysis(BuildContext context, WidgetRef ref) async {
    final ok = await ref.read(facilitatorSessionProvider.notifier).runAnalysis();
    if (!context.mounted) return;
    if (ok) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Analysis complete')),
      );
    } else {
      final err =
          ref.read(facilitatorSessionProvider).error ?? 'Analysis failed';
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(err)));
    }
  }
}

/// The access code presented large + mono, with a copy button and the QR.
class _AccessCodeCard extends StatelessWidget {
  const _AccessCodeCard({required this.accessCode, required this.joinUrl});
  final String accessCode;
  final String joinUrl;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return GlassCard(
      padding: const EdgeInsets.all(20),
      child: Column(
          children: [
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        'JOIN CODE',
                        style: theme.textTheme.labelSmall?.copyWith(
                          color: theme.colorScheme.onSurfaceVariant,
                          fontWeight: FontWeight.w600,
                          letterSpacing: 1.5,
                        ),
                      ),
                      const SizedBox(height: 6),
                      SelectableText(
                        accessCode,
                        style: GoogleFonts.jetBrainsMono(
                          fontSize: 30,
                          fontWeight: FontWeight.w700,
                          letterSpacing: 6,
                          color: theme.colorScheme.onSurface,
                        ),
                        semanticsLabel:
                            'Access code: ${accessCode.split('').join(' ')}',
                      ),
                    ],
                  ),
                ),
                IconButton.outlined(
                  tooltip: 'Copy code',
                  icon: const Icon(Icons.copy_rounded, size: 20),
                  onPressed: () async {
                    await Clipboard.setData(ClipboardData(text: accessCode));
                    if (!context.mounted) return;
                    ScaffoldMessenger.of(context).showSnackBar(
                      const SnackBar(content: Text('Code copied')),
                    );
                  },
                ),
              ],
            ),
            const SizedBox(height: 16),
            const Divider(),
            const SizedBox(height: 16),
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
                  size: 180,
                  backgroundColor: Colors.white,
                ),
              ),
            ),
            const SizedBox(height: 10),
            Text(
              'or scan the QR to join',
              style: theme.textTheme.bodySmall?.copyWith(
                color: theme.colorScheme.onSurfaceVariant,
              ),
            ),
          ],
        ),
    );
  }
}

/// A stat tile — participants / ideas. Quiet, numeric, not stretched.
class _StatTile extends StatelessWidget {
  const _StatTile({required this.icon, required this.label, required this.value});
  final IconData icon;
  final String label;
  final int value;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Expanded(
      child: GlassCard(
        padding: const EdgeInsets.symmetric(vertical: 18, horizontal: 14),
        child: Column(
            children: [
              Icon(icon, size: 24, color: AppColors.accent),
              const SizedBox(height: 8),
              Text(
                '$value',
                style: theme.textTheme.headlineMedium?.copyWith(
                  fontWeight: FontWeight.w700,
                  color: theme.colorScheme.onSurface,
                ),
              ),
              const SizedBox(height: 2),
              Text(
                label,
                style: theme.textTheme.labelSmall?.copyWith(
                  color: theme.colorScheme.onSurfaceVariant,
                ),
              ),
            ],
        ),
      ),
    );
  }
}

/// The run-analysis button, with a loading state.
class _AnalysisControl extends StatelessWidget {
  const _AnalysisControl({required this.state, required this.onRun});
  final FacilitatorSessionState state;
  final VoidCallback onRun;

  @override
  Widget build(BuildContext context) {
    final disabled = state.analysing || state.ideas.isEmpty;
    return SizedBox(
      width: double.infinity,
      child: FilledButton.icon(
        onPressed: disabled ? null : onRun,
        icon: state.analysing
            ? const SizedBox(
                width: 18,
                height: 18,
                child: CircularProgressIndicator(strokeWidth: 2))
            : const Icon(Icons.auto_awesome_rounded),
        label: Text(state.analysing ? 'Analysing…' : 'Run AI analysis'),
      ),
    );
  }
}
