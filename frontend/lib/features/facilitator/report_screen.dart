import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/theme/app_colors.dart';
import '../../core/theme/layout.dart';
import '../../models/models.dart';
import '../../services/pdf_download.dart';
import '../../widgets/empty_state.dart';
import '../../widgets/section_heading.dart';
import 'facilitator_session_controller.dart';

/// Renders the AI analysis result and offers a PDF download. Reached from the
/// dashboard once analysis has been run. Structured like a real report:
/// clustered categories first, then themes / decisions / questions / steps.
class ReportScreen extends ConsumerWidget {
  const ReportScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final state = ref.watch(facilitatorSessionProvider);
    final analysis = state.analysis;
    if (analysis == null) {
      return Scaffold(
        appBar: AppBar(title: const Text('Analysis')),
        body: const EmptyState(
          icon: Icons.auto_awesome_outlined,
          message: 'No analysis yet',
          detail: 'Run AI analysis from the dashboard first.',
        ),
      );
    }
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
      body: Center(
        child: ConstrainedBox(
          constraints: const BoxConstraints(maxWidth: Layout.dashboardMaxWidth),
          child: ListView(
            padding: const EdgeInsets.symmetric(
                horizontal: Layout.padding, vertical: 24),
            children: [
              // ── Category grid ────────────────────────────────────
              const SectionHeading(eyebrow: 'Clusters', title: 'Clustered ideas'),
              const SizedBox(height: 12),
              _CategoryGrid(analysis: analysis),
              const SizedBox(height: 32),

              if (analysis.keyThemes.isNotEmpty)
                _InsightBlock(
                  eyebrow: 'Synthesis',
                  title: 'Key themes',
                  items: analysis.keyThemes,
                  icon: Icons.star_rounded,
                  color: AppColors.vote,
                ),
              if (analysis.decisionsMade.isNotEmpty)
                _InsightBlock(
                  title: 'Decisions made',
                  items: analysis.decisionsMade,
                  icon: Icons.check_circle_rounded,
                  color: AppColors.live,
                ),
              if (analysis.openQuestions.isNotEmpty)
                _InsightBlock(
                  title: 'Open questions',
                  items: analysis.openQuestions,
                  icon: Icons.help_rounded,
                  color: AppColors.textSecondary,
                ),
              if (analysis.recommendedNextSteps.isNotEmpty)
                _InsightBlock(
                  title: 'Recommended next steps',
                  items: analysis.recommendedNextSteps,
                  icon: Icons.arrow_forward_rounded,
                  color: AppColors.accent,
                ),

              // ── Download button ───────────────────────────────────
              const SizedBox(height: 16),
              SizedBox(
                width: double.infinity,
                child: FilledButton.icon(
                  onPressed: () => _downloadPdf(context, ref),
                  icon: const Icon(Icons.picture_as_pdf_outlined),
                  label: const Text('Download PDF report'),
                ),
              ),
              if (state.pdfBytes != null)
                Padding(
                  padding: const EdgeInsets.only(top: 8),
                  child: Text(
                    'PDF ready (${state.pdfBytes!.length ~/ 1024} KB).',
                    textAlign: TextAlign.center,
                    style: Theme.of(context).textTheme.bodySmall,
                  ),
                ),
            ],
          ),
        ),
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
      final session = ref.read(facilitatorSessionProvider).session;
      final filename = 'workshop-report-${session?.id ?? 'session'}.pdf';
      final saved = savePdf(bytes, filename);
      if (!context.mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(saved
              ? 'PDF downloaded (${bytes.length ~/ 1024} KB)'
              : 'PDF ready (${bytes.length ~/ 1024} KB)'),
        ),
      );
    }
  }
}

/// A responsive grid of category cards, each listing the clustered ideas.
/// Uses Wrap for robust layout (replaces the hand-rolled Row math).
class _CategoryGrid extends StatelessWidget {
  const _CategoryGrid({required this.analysis});
  final AnalysisResult analysis;

  @override
  Widget build(BuildContext context) {
    final entries = analysis.categories.entries.toList();
    return LayoutBuilder(builder: (context, constraints) {
      final wide = constraints.maxWidth > 560;
      return Wrap(
        spacing: 12,
        runSpacing: 12,
        children: entries.map((e) {
          return SizedBox(
            width: wide ? (constraints.maxWidth - 12) / 2 : double.infinity,
            child: _CategoryCard(entry: e),
          );
        }).toList(),
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
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Container(
                  width: 6,
                  height: 6,
                  decoration: const BoxDecoration(
                    color: AppColors.accent,
                    shape: BoxShape.circle,
                  ),
                ),
                const SizedBox(width: 8),
                Text(
                  title,
                  style: theme.textTheme.titleSmall?.copyWith(
                    color: theme.colorScheme.onSurface,
                  ),
                ),
              ],
            ),
            const SizedBox(height: 10),
            if (entry.value.isEmpty)
              Text('No items',
                  style: theme.textTheme.bodySmall?.copyWith(
                    color: theme.colorScheme.onSurfaceVariant,
                  ))
            else
              ...entry.value.map(
                (idea) => Padding(
                  padding: const EdgeInsets.only(bottom: 6),
                  child: Row(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Padding(
                        padding: const EdgeInsets.only(top: 7),
                        child: Container(
                          width: 4,
                          height: 4,
                          decoration: BoxDecoration(
                            color: theme.colorScheme.onSurfaceVariant,
                            shape: BoxShape.circle,
                          ),
                        ),
                      ),
                      const SizedBox(width: 10),
                      Expanded(
                        child: Text(
                          idea.summary,
                          style: theme.textTheme.bodyMedium,
                        ),
                      ),
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

/// A titled list of insight bullets with an accent icon.
class _InsightBlock extends StatelessWidget {
  const _InsightBlock({
    this.eyebrow,
    required this.title,
    required this.items,
    required this.icon,
    required this.color,
  });

  final String? eyebrow;
  final String title;
  final List<String> items;
  final IconData icon;
  final Color color;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Padding(
      padding: const EdgeInsets.only(bottom: 28),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          SectionHeading(eyebrow: eyebrow, title: title),
          const SizedBox(height: 12),
          ...items.map(
            (t) => Padding(
              padding: const EdgeInsets.only(bottom: 8),
              child: Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Container(
                    margin: const EdgeInsets.only(top: 2),
                    padding: const EdgeInsets.all(5),
                    decoration: BoxDecoration(
                      color: color.withValues(alpha: 0.12),
                      shape: BoxShape.circle,
                    ),
                    child: Icon(icon, size: 14, color: color),
                  ),
                  const SizedBox(width: 10),
                  Expanded(
                    child: Text(
                      t,
                      style: theme.textTheme.bodyLarge?.copyWith(
                        height: 1.5,
                      ),
                    ),
                  ),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }
}
