import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:qr_flutter/qr_flutter.dart';

import '../../core/config/app_config.dart';
import 'facilitator_session_controller.dart';

/// Facilitator dashboard: the live workshop control center. Shows the access
/// code + QR for participants to join, live participant/idea counts, the live
/// idea feed, and the trigger to run AI analysis.
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

    // The QR encodes a join URL participants can scan. On web, that's the
    // app's own origin with the /join route and the access code as a query
    // param; a real deployment would use the public app URL.
    final joinUrl = '${AppConfig.apiBaseUrl}/#/join?code=${session.accessCode}';

    return Scaffold(
      appBar: AppBar(
        title: Text(session.topic),
        actions: [
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 12),
            child: Center(child: _LiveDot(connected: state.connected)),
          ),
        ],
      ),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          if (state.error != null)
            Container(
              margin: const EdgeInsets.only(bottom: 12),
              padding: const EdgeInsets.all(12),
              decoration: BoxDecoration(
                color: theme.colorScheme.errorContainer,
                borderRadius: BorderRadius.circular(8),
              ),
              child: Text(state.error!,
                  style: TextStyle(color: theme.colorScheme.onErrorContainer)),
            ),
          // ── Access code + QR ──────────────────────────────────
          Card(
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: Column(
                children: [
                  Text('Participants join with this code',
                      style: theme.textTheme.labelLarge),
                  const SizedBox(height: 4),
                  Text(
                    session.accessCode,
                    style: theme.textTheme.displaySmall
                        ?.copyWith(fontWeight: FontWeight.bold, letterSpacing: 4),
                  ),
                  const SizedBox(height: 16),
                  QrImageView(
                    data: joinUrl,
                    version: QrVersions.auto,
                    size: 200,
                    backgroundColor: Colors.white,
                  ),
                  const SizedBox(height: 8),
                  Text('or scan the QR code',
                      style: theme.textTheme.bodySmall),
                ],
              ),
            ),
          ),
          const SizedBox(height: 16),
          // ── Live counts ──────────────────────────────────────
          Row(
            children: [
              _StatCard(
                icon: Icons.group_outlined,
                label: 'Participants',
                value: '${state.participantCount}',
              ),
              const SizedBox(width: 12),
              _StatCard(
                icon: Icons.lightbulb_outline,
                label: 'Ideas',
                value: '${state.ideas.length}',
              ),
            ],
          ),
          const SizedBox(height: 16),
          // ── Live idea feed ───────────────────────────────────
          Text('Live ideas', style: theme.textTheme.titleSmall),
          const SizedBox(height: 8),
          if (state.ideas.isEmpty)
            const Padding(
              padding: EdgeInsets.symmetric(vertical: 24),
              child: Center(child: Text('Waiting for the first idea…')),
            )
          else
            ...state.ideas.map((idea) => ListTile(
                  dense: true,
                  leading: const Icon(Icons.circle, size: 8),
                  title: Text(idea.content),
                  subtitle: Text(
                      '${idea.participantName} • ${idea.votes} vote${idea.votes == 1 ? '' : 's'}'),
                )),
          const SizedBox(height: 24),
          // ── Run analysis ─────────────────────────────────────
          FilledButton.icon(
            onPressed: (state.analysing || state.ideas.isEmpty)
                ? null
                : () => _runAnalysis(context, ref),
            icon: state.analysing
                ? const SizedBox(
                    width: 18, height: 18,
                    child: CircularProgressIndicator(strokeWidth: 2))
                : const Icon(Icons.auto_awesome_outlined),
            label: Text(state.analysing ? 'Analysing…' : 'Run AI analysis'),
          ),
          if (state.ideas.isEmpty)
            Padding(
              padding: const EdgeInsets.only(top: 8),
              child: Text(
                'Add at least one idea before running analysis.',
                style: theme.textTheme.bodySmall,
                textAlign: TextAlign.center,
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

class _StatCard extends StatelessWidget {
  const _StatCard(
      {required this.icon, required this.label, required this.value});
  final IconData icon;
  final String label;
  final String value;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Expanded(
      child: Card(
        child: Padding(
          padding: const EdgeInsets.symmetric(vertical: 16, horizontal: 12),
          child: Column(
            children: [
              Icon(icon, size: 28, color: theme.colorScheme.primary),
              const SizedBox(height: 8),
              Text(value,
                  style: theme.textTheme.headlineMedium
                      ?.copyWith(fontWeight: FontWeight.bold)),
              Text(label, style: theme.textTheme.bodySmall),
            ],
          ),
        ),
      ),
    );
  }
}

class _LiveDot extends StatelessWidget {
  const _LiveDot({required this.connected});
  final bool connected;

  @override
  Widget build(BuildContext context) {
    return Row(
      mainAxisSize: MainAxisSize.min,
      children: [
        Icon(Icons.fiber_manual_record,
            size: 12, color: connected ? Colors.green : Colors.grey),
        const SizedBox(width: 4),
        Text(connected ? 'Live' : 'Connecting…',
            style: Theme.of(context).textTheme.labelSmall),
      ],
    );
  }
}
