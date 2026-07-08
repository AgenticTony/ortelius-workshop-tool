import 'package:flutter/material.dart';

import '../core/theme/layout.dart';
import '../models/models.dart';
import 'empty_state.dart';
import 'sticky_note.dart';

/// The live idea feed, backed by an [AnimatedList] so newly-arrived ideas
/// slide+fade in instead of popping. This is the "alive" moment that matters
/// most: ideas stream in over SSE mid-session, and motion makes that arrival
/// legible instead of jarring.
///
/// Diffs the incoming [ideas] list against the last-seen one. When new ids
/// appear at the tail (the normal arrival order), they're inserted with an
/// animation. Removes/reorders are handled by a full keyed rebuild.
class IdeaFeed extends StatefulWidget {
  const IdeaFeed({
    super.key,
    required this.ideas,
    required this.myParticipantId,
    required this.onVote,
  });

  final List<Idea> ideas;
  final String? myParticipantId;
  final void Function(String ideaId) onVote;

  @override
  State<IdeaFeed> createState() => _IdeaFeedState();
}

class _IdeaFeedState extends State<IdeaFeed> {
  final GlobalKey<AnimatedListState> _listKey = GlobalKey<AnimatedListState>();

  @override
  void didUpdateWidget(covariant IdeaFeed oldWidget) {
    super.didUpdateWidget(oldWidget);
    _syncInsertions(oldWidget.ideas, widget.ideas);
  }

  /// Insert any newly-arrived ideas into the AnimatedList so they animate in.
  void _syncInsertions(List<Idea> prev, List<Idea> next) {
    final prevIds = prev.map((e) => e.id).toSet();
    // Only count tail-appended items as "new arrivals" (the normal SSE/submit
    // path). If the list shrinks or reorders (session change / reload), we let
    // the keyed rebuild handle it rather than animating every slot.
    final added = <int>[];
    for (var i = 0; i < next.length; i++) {
      if (!prevIds.contains(next[i].id) &&
          (i >= prev.length || next[i].id != prev[i].id)) {
        // Only treat as insertion if it's genuinely at/after the previous tail.
        if (i >= prev.length) added.add(i);
      }
    }
    if (added.isEmpty) {
      return;
    }
    // Insert in order with a tiny per-item stagger so a burst of ideas reads
    // as a cascade, not a single hard block.
    for (var n = 0; n < added.length; n++) {
      final index = added[n];
      final reduce = MediaQuery.disableAnimationsOf(context);
      WidgetsBinding.instance.addPostFrameCallback((_) {
        if (!mounted) return;
        _listKey.currentState?.insertItem(
          index,
          duration: reduce
              ? const Duration(milliseconds: 1)
              : const Duration(milliseconds: 280),
        );
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    if (widget.ideas.isEmpty) {
      return const EmptyState(
        icon: Icons.lightbulb_outline_rounded,
        message: 'No ideas yet',
        detail: 'Be the first to share one.',
      );
    }
    return Center(
      child: ConstrainedBox(
        constraints:
            const BoxConstraints(maxWidth: Layout.dashboardMaxWidth),
        child: AnimatedList(
          key: _listKey,
          initialItemCount: widget.ideas.length,
          padding:
              const EdgeInsets.fromLTRB(Layout.padding, 12, Layout.padding, 24),
          itemBuilder: (context, index, animation) {
            if (index >= widget.ideas.length) return const SizedBox.shrink();
            final idea = widget.ideas[index];
            final isMine = idea.participantId == widget.myParticipantId;
            return _AnimatedIdea(
              animation: animation,
              idea: idea,
              isMine: isMine,
              onVote: () => widget.onVote(idea.id),
            );
          },
        ),
      ),
    );
  }
}

class _AnimatedIdea extends StatelessWidget {
  const _AnimatedIdea({
    required this.animation,
    required this.idea,
    required this.isMine,
    required this.onVote,
  });

  final Animation<double> animation;
  final Idea idea;
  final bool isMine;
  final VoidCallback onVote;

  @override
  Widget build(BuildContext context) {
    return SizeTransition(
      sizeFactor: animation,
      axisAlignment: -1.0,
      child: FadeTransition(
        opacity: animation,
        child: SlideTransition(
          position: animation.drive(
            Tween<Offset>(
              begin: const Offset(0, 0.12),
              end: Offset.zero,
            ).chain(CurveTween(curve: Curves.easeOutCubic)),
          ),
          child: StickyNote(
            idea: idea,
            isMine: isMine,
            onVote: onVote,
          ),
        ),
      ),
    );
  }
}
