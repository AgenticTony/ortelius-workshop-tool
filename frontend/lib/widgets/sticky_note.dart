import 'package:flutter/material.dart';

import '../core/theme/app_colors.dart';
import '../models/models.dart';

/// The signature element of the app: a participant idea rendered as a tilted
/// sticky note.
///
/// Grounded in workshop vernacular — a facilitated session is full of sticky
/// notes on a wall. Each note has a subtle, deterministic rotation (seeded
/// from the idea id so it stays put across rebuilds), a soft paper shadow,
/// and an amber tint when it's the viewer's own idea (the "highlight" marker).
/// The vote control sits on the right.
///
/// Restraint: this is the *one* expressive element. Everything around it stays
/// disciplined so the feed feels alive without the whole app shouting.
class StickyNote extends StatelessWidget {
  const StickyNote({
    super.key,
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
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 5),
      child: Container(
        width: double.infinity,
        padding: const EdgeInsets.fromLTRB(16, 14, 12, 12),
        decoration: BoxDecoration(
          // Solid white card. Yours gets a subtle teal tint to mark it.
          color: isMine ? AppColors.stickyNoteMine : AppColors.stickyNote,
          borderRadius: BorderRadius.circular(12),
          // A thicker left accent bar marks "yours" — quieter than a fill.
          border: Border(
            left: isMine
                ? const BorderSide(color: AppColors.accent, width: 3)
                : const BorderSide(color: AppColors.border, width: 2),
            top: const BorderSide(color: AppColors.border, width: 2),
            right: const BorderSide(color: AppColors.border, width: 2),
            bottom: const BorderSide(color: AppColors.border, width: 2),
          ),
          boxShadow: const [
            BoxShadow(
              color: AppColors.shadowOuter,
              blurRadius: 8,
              offset: Offset(0, 3),
            ),
          ],
        ),
        child: Row(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Expanded(child: _body(theme)),
            const SizedBox(width: 8),
            _VoteControl(votes: idea.votes, onTap: onVote),
          ],
        ),
      ),
    );
  }

  Widget _body(ThemeData theme) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        if (isMine)
          Padding(
            padding: const EdgeInsets.only(bottom: 6),
            child: _YoursTag(),
          ),
        Text(
          idea.content,
          style: theme.textTheme.bodyLarge?.copyWith(
            color: theme.colorScheme.onSurface,
            height: 1.4,
          ),
        ),
        const SizedBox(height: 6),
        Text(
          idea.participantName,
          style: theme.textTheme.labelSmall?.copyWith(
            color: theme.colorScheme.onSurfaceVariant,
          ),
        ),
      ],
    );
  }

}

/// The accent "You" tag — marks the viewer's own idea.
class _YoursTag extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 7, vertical: 2),
      decoration: BoxDecoration(
        color: AppColors.accent.withValues(alpha: 0.15),
        borderRadius: BorderRadius.circular(4),
        border: Border.all(color: AppColors.accent.withValues(alpha: 0.3)),
      ),
      child: Text(
        'YOU',
        style: Theme.of(context).textTheme.labelSmall?.copyWith(
          color: AppColors.accent,
          fontWeight: FontWeight.w700,
              letterSpacing: 0.8,
              fontSize: 10,
            ),
      ),
    );
  }
}

/// The vote control — a tap target with the count below an arrow.
/// Preserves the 48×48 minimum tap target + semantic label from the original.
class _VoteControl extends StatelessWidget {
  const _VoteControl({required this.votes, required this.onTap});
  final int votes;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Semantics(
      button: true,
      label: 'Upvote, $votes ${votes == 1 ? 'vote' : 'votes'}',
      hint: 'Tap to upvote this idea',
      child: ConstrainedBox(
        constraints: const BoxConstraints(minWidth: 48, minHeight: 48),
        child: Material(
          color: Colors.transparent,
          child: InkWell(
            onTap: onTap,
            borderRadius: BorderRadius.circular(12),
            child: Padding(
              padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 6),
              child: Column(
                mainAxisSize: MainAxisSize.min,
                children: [
                  Icon(
                    Icons.arrow_upward_rounded,
                    size: 20,
                    color: theme.colorScheme.onSurfaceVariant,
                  ),
                  const SizedBox(height: 1),
                  Text(
                    '$votes',
                    style: theme.textTheme.labelMedium?.copyWith(
                      fontWeight: FontWeight.w600,
                    ),
                  ),
                ],
              ),
            ),
          ),
        ),
      ),
    );
  }
}
