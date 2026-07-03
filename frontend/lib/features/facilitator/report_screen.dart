import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../models/models.dart';
import 'facilitator_session_controller.dart';

/// Renders the AI analysis result and offers a PDF download. Reached from the
/// dashboard once analysis has been run.
class ReportScreen extends ConsumerWidget {
  const ReportScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final state = ref.watch(facilitatorSessionProvider);
    final analysis = state.analysis;
    if (analysis == null) {
      return Scaffold(
        appBar: AppBar(title: const Text('Analysis')),
        body: const Center(child: Text('No analysis yet. Run it from the dashboard.')),
      );
    }
    final theme = Theme.of(context);
    return Scaffold(
      appBar: AppBar(
        title: Text('${analysis.framework.toUpperCase()} analysis'),
        actions: [
          IconButton(
            tooltip: 'Download PDF',
            onPressed: () => _downloadPdf(context, ref),
            icon: const Icon(Icons.download_outlined),
          ),
        ],
      ),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          // ── Category grid ────────────────────────────────────
          Text('Clustered ideas', style: theme.textTheme.titleMedium),
          const SizedBox(height: 8),
          _CategoryGrid(analysis: analysis),
          const SizedBox(height: 24),
          // ── Themes ───────────────────────────────────────────
          if (analysis.keyThemes.isNotEmpty) ...[
            Text('Key themes', style: theme.textTheme.titleMedium),
            const SizedBox(height: 8),
            ...analysis.keyThemes.map((t) => _Bullet(text: t, icon: Icons.star_outline)),
            const SizedBox(height: 16),
          ],
          // ── Decisions ────────────────────────────────────────
          if (analysis.decisionsMade.isNotEmpty) ...[
            Text('Decisions made', style: theme.textTheme.titleMedium),
            const SizedBox(height: 8),
            ...analysis.decisionsMade
                .map((t) => _Bullet(text: t, icon: Icons.check_circle_outline)),
            const SizedBox(height: 16),
          ],
          // ── Questions ────────────────────────────────────────
          if (analysis.openQuestions.isNotEmpty) ...[
            Text('Open questions', style: theme.textTheme.titleMedium),
            const SizedBox(height: 8),
            ...analysis.openQuestions
                .map((t) => _Bullet(text: t, icon: Icons.help_outline)),
            const SizedBox(height: 16),
          ],
          // ── Next steps ───────────────────────────────────────
          if (analysis.recommendedNextSteps.isNotEmpty) ...[
            Text('Recommended next steps', style: theme.textTheme.titleMedium),
            const SizedBox(height: 8),
            ...analysis.recommendedNextSteps
                .map((t) => _Bullet(text: t, icon: Icons.arrow_forward)),
            const SizedBox(height: 24),
          ],
          // ── Download button (mobile-friendly) ────────────────
          FilledButton.icon(
            onPressed: () => _downloadPdf(context, ref),
            icon: const Icon(Icons.picture_as_pdf_outlined),
            label: const Text('Download PDF report'),
          ),
          if (state.pdfBytes != null)
            Padding(
              padding: const EdgeInsets.only(top: 8),
              child: Text(
                'PDF ready (${state.pdfBytes!.length ~/ 1024} KB).',
                textAlign: TextAlign.center,
                style: theme.textTheme.bodySmall,
              ),
            ),
        ],
      ),
    );
  }

  Future<void> _downloadPdf(BuildContext context, WidgetRef ref) async {
    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(content: Text('Generating PDF…')),
    );
    final bytes = await ref
        .read(facilitatorSessionProvider.notifier)
        .downloadReport();
    if (!context.mounted) return;
    if (bytes == null) {
      final err =
          ref.read(facilitatorSessionProvider).error ?? 'Download failed';
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(err)));
    } else {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('PDF ready (${bytes.length ~/ 1024} KB)')),
      );
      // Note: actually saving/sharing the file is platform-specific (web vs
      // mobile). For web, an anchor-download is wired in Milestone 5 polish.
    }
  }
}

/// A responsive grid of category cards, each listing the clustered ideas.
class _CategoryGrid extends StatelessWidget {
  const _CategoryGrid({required this.analysis});
  final AnalysisResult analysis;

  @override
  Widget build(BuildContext context) {
    final entries = analysis.categories.entries.toList();
    return LayoutBuilder(builder: (context, constraints) {
      // 2 columns when there's room, else 1.
      final cols = constraints.maxWidth > 600 ? 2 : 1;
      final rows = (entries.length / cols).ceil();
      return Column(
        children: [
          for (int r = 0; r < rows; r++)
            Padding(
              padding: const EdgeInsets.only(bottom: 8),
              child: Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  for (int c = 0; c < cols; c++) ...[
                    if (c > 0) const SizedBox(width: 8),
                    Expanded(
                      child: (r * cols + c) < entries.length
                          ? _CategoryCard(entry: entries[r * cols + c])
                          : const SizedBox(),
                    ),
                  ],
                ],
              ),
            ),
        ],
      );
    });
  }
}

class _CategoryCard extends StatelessWidget {
  const _CategoryCard({required this.entry});
  final MapEntry<String, List<ClusteredIdea>> entry;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final title = entry.key[0].toUpperCase() + entry.key.substring(1);
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(12),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(title,
                style: theme.textTheme.titleSmall
                    ?.copyWith(color: theme.colorScheme.primary)),
            const SizedBox(height: 8),
            if (entry.value.isEmpty)
              Text('No items', style: theme.textTheme.bodySmall)
            else
              ...entry.value.map(
                (idea) => Padding(
                  padding: const EdgeInsets.only(bottom: 4),
                  child: Row(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      const Text('•  '),
                      Expanded(child: Text(idea.summary)),
                    ],
                  ),
                ),
              ),
          ],
        ),
      ),
    );
  }
}

class _Bullet extends StatelessWidget {
  const _Bullet({required this.text, required this.icon});
  final String text;
  final IconData icon;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 4),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Icon(icon, size: 20),
          const SizedBox(width: 8),
          Expanded(child: Text(text)),
        ],
      ),
    );
  }
}
