import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../core/theme/app_colors.dart';
import '../../core/theme/layout.dart';
import '../../models/models.dart';
import '../../widgets/empty_state.dart';
import '../../widgets/error_banner.dart';
import '../../widgets/glass_card.dart';
import '../../widgets/live_indicator.dart';
import '../../widgets/sticky_note.dart';
import 'participant_session_controller.dart';

/// The participant's live workshop room: a real-time feed of ideas as sticky
/// notes, an input bar to submit one, and tap-to-vote on each idea.
class WorkshopScreen extends ConsumerStatefulWidget {
  const WorkshopScreen({super.key});

  @override
  ConsumerState<WorkshopScreen> createState() => _WorkshopScreenState();
}

class _WorkshopScreenState extends ConsumerState<WorkshopScreen> {
  final _ideaController = TextEditingController();

  @override
  void initState() {
    super.initState();
    // If we arrived here without joining (deep link / refresh), bounce back.
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (!mounted) return;
      final s = ref.read(participantSessionProvider);
      if (s.session == null) {
        context.go('/join');
      }
    });
  }

  @override
  void dispose() {
    _ideaController.dispose();
    super.dispose();
  }

  Future<void> _submit() async {
    final text = _ideaController.text.trim();
    if (text.isEmpty) return;
    // Clear optimistically, but restore the text if the submit fails so the
    // user doesn't lose what they typed.
    _ideaController.clear();
    await ref.read(participantSessionProvider.notifier).submitIdea(text);
    if (!mounted) return;
    final err = ref.read(participantSessionProvider).error;
    if (err != null) {
      _ideaController.text = text;
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(err)));
    }
  }

  @override
  Widget build(BuildContext context) {
    final state = ref.watch(participantSessionProvider);
    final session = state.session;
    return Scaffold(
      appBar: AppBar(
        title: Text(session?.topic ?? 'Workshop'),
        actions: [
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 16),
            child: Center(child: LiveIndicator(connected: state.connected)),
          ),
        ],
      ),
      body: session == null
          ? const Center(child: CircularProgressIndicator())
          : Column(
              children: [
                if (state.error != null)
                  Padding(
                    padding: const EdgeInsets.fromLTRB(
                        Layout.padding, 12, Layout.padding, 0),
                    child: ErrorBanner(
                      message: state.error!,
                      onDismiss: () => ref
                          .read(participantSessionProvider.notifier)
                          .dismissError(),
                    ),
                  ),
                Expanded(child: _ideaList(state.ideas, state.participantId)),
                _ideaInput(state.loading),
              ],
            ),
    );
  }

  Widget _ideaList(List<Idea> ideas, String? myParticipantId) {
    if (ideas.isEmpty) {
      return const EmptyState(
        icon: Icons.lightbulb_outline_rounded,
        message: 'No ideas yet',
        detail: 'Be the first to share one.',
      );
    }
    return Center(
      child: ConstrainedBox(
        constraints: const BoxConstraints(maxWidth: Layout.dashboardMaxWidth),
        child: ListView.builder(
          padding: const EdgeInsets.fromLTRB(
              Layout.padding, 12, Layout.padding, 24),
          itemCount: ideas.length,
          itemBuilder: (context, index) {
            final idea = ideas[index];
            final isMine = idea.participantId == myParticipantId;
            return StickyNote(
              idea: idea,
              isMine: isMine,
              onVote: () =>
                  ref.read(participantSessionProvider.notifier).vote(idea.id),
            );
          },
        ),
      ),
    );
  }

  Widget _ideaInput(bool loading) {
    final theme = Theme.of(context);
    return SafeArea(
      child: Center(
        child: ConstrainedBox(
          constraints: const BoxConstraints(maxWidth: Layout.dashboardMaxWidth),
          child: GlassCard(
            blur: true,
            radius: 14,
            margin: const EdgeInsets.fromLTRB(
                Layout.padding, 4, Layout.padding, 8),
            padding: const EdgeInsets.fromLTRB(12, 6, 6, 6),
            child: Row(
              crossAxisAlignment: CrossAxisAlignment.end,
              children: [
                Expanded(
                  child: TextField(
                    controller: _ideaController,
                    textInputAction: TextInputAction.send,
                    onSubmitted: (_) => _submit(),
                    maxLines: 3,
                    minLines: 1,
                    decoration: InputDecoration(
                      hintText: 'Share an idea…',
                      hintStyle: theme.textTheme.bodyMedium?.copyWith(
                        color: theme.colorScheme.onSurfaceVariant
                            .withValues(alpha: 0.6),
                      ),
                      border: InputBorder.none,
                      enabledBorder: InputBorder.none,
                      focusedBorder: InputBorder.none,
                      contentPadding: const EdgeInsets.symmetric(
                          horizontal: 8, vertical: 10),
                    ),
                  ),
                ),
                const SizedBox(width: 4),
                IconButton.filled(
                  onPressed: loading ? null : _submit,
                  icon: const Icon(Icons.send_rounded),
                  style: IconButton.styleFrom(
                    backgroundColor: AppColors.accent,
                    foregroundColor: Colors.white,
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
