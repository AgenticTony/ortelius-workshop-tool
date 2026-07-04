import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../models/models.dart';
import '../../widgets/empty_state.dart';
import '../../widgets/error_banner.dart';
import 'participant_session_controller.dart';

/// The participant's live workshop room: a real-time feed of ideas, an input
/// bar to submit one, and tap-to-vote on each idea.
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
          // Live-connection indicator.
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 12),
            child: Center(
              child: _LiveDot(connected: state.connected),
            ),
          ),
        ],
      ),
      body: session == null
          ? const Center(child: CircularProgressIndicator())
          : Column(
              children: [
                if (state.error != null)
                  Padding(
                    padding: const EdgeInsets.fromLTRB(12, 8, 12, 0),
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
      return EmptyState(
        icon: Icons.lightbulb_outline,
        message: 'No ideas yet',
        detail: 'Be the first to share one.',
      );
    }
    return ListView.builder(
      padding: const EdgeInsets.symmetric(vertical: 8),
      itemCount: ideas.length,
      itemBuilder: (context, index) {
        final idea = ideas[index];
        final isMine = idea.participantId == myParticipantId;
        return _IdeaCard(
          idea: idea,
          isMine: isMine,
          onVote: () =>
              ref.read(participantSessionProvider.notifier).vote(idea.id),
        );
      },
    );
  }

  Widget _ideaInput(bool loading) {
    return SafeArea(
      child: Padding(
        padding: const EdgeInsets.fromLTRB(12, 8, 8, 8),
        child: Row(
          children: [
            Expanded(
              child: TextField(
                controller: _ideaController,
                textInputAction: TextInputAction.send,
                onSubmitted: (_) => _submit(),
                maxLines: 3,
                minLines: 1,
                decoration: const InputDecoration(
                  hintText: 'Share an idea…',
                  border: OutlineInputBorder(),
                ),
              ),
            ),
            const SizedBox(width: 8),
            IconButton.filled(
              onPressed: loading ? null : _submit,
              icon: const Icon(Icons.send),
            ),
          ],
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
        Icon(
          Icons.fiber_manual_record,
          size: 12,
          color: connected ? Colors.green : Colors.grey,
        ),
        const SizedBox(width: 4),
        Text(
          connected ? 'Live' : 'Connecting…',
          style: Theme.of(context).textTheme.labelSmall,
        ),
      ],
    );
  }
}

class _IdeaCard extends StatelessWidget {
  const _IdeaCard({
    required this.idea,
    required this.isMine,
    required this.onVote,
  });

  final Idea idea;
  final bool isMine;
  final VoidCallback onVote;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Card(
      margin: const EdgeInsets.symmetric(horizontal: 12, vertical: 4),
      child: Padding(
        padding: const EdgeInsets.fromLTRB(16, 12, 12, 12),
        child: Row(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  if (isMine)
                    Container(
                      margin: const EdgeInsets.only(bottom: 4),
                      padding: const EdgeInsets.symmetric(
                          horizontal: 6, vertical: 2),
                      decoration: BoxDecoration(
                        color: theme.colorScheme.primaryContainer,
                        borderRadius: BorderRadius.circular(4),
                      ),
                      child: Text('You',
                          style: TextStyle(
                              fontSize: 10,
                              color: theme.colorScheme.onPrimaryContainer)),
                    ),
                  Text(idea.content, style: theme.textTheme.bodyLarge),
                  const SizedBox(height: 4),
                  Text(
                    idea.participantName,
                    style: theme.textTheme.labelSmall,
                  ),
                ],
              ),
            ),
            const SizedBox(width: 8),
            _VoteButton(votes: idea.votes, onTap: onVote),
          ],
        ),
      ),
    );
  }
}

class _VoteButton extends StatelessWidget {
  const _VoteButton({required this.votes, required this.onTap});
  final int votes;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    // Semantic label so screen readers announce the action + count, and a
    // 48x48 minimum tap target (Material accessibility guideline).
    return Semantics(
      button: true,
      label: 'Upvote, $votes ${votes == 1 ? 'vote' : 'votes'}',
      hint: 'Tap to upvote this idea',
      child: ConstrainedBox(
        constraints: const BoxConstraints(minWidth: 48, minHeight: 48),
        child: InkWell(
          onTap: onTap,
          borderRadius: BorderRadius.circular(20),
          child: Padding(
            padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 8),
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                const Icon(Icons.arrow_upward, size: 20),
                Text('$votes', style: Theme.of(context).textTheme.labelMedium),
              ],
            ),
          ),
        ),
      ),
    );
  }
}
