import 'dart:async';

import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/app_providers.dart';
import '../../core/api/workshop_api.dart';
import '../../models/models.dart';
import '../../services/sse_client.dart';

/// State held for the participant's current workshop session.
class ParticipantSessionState {
  const ParticipantSessionState({
    this.session,
    this.participantId,
    this.ideas = const [],
    this.loading = false,
    this.error,
    this.connected = false,
  });

  final Session? session;
  final String? participantId;
  final List<Idea> ideas;

  /// True while a join / submit / vote call is in flight.
  final bool loading;
  final String? error;

  /// Whether the SSE stream is currently live.
  final bool connected;

  ParticipantSessionState copyWith({
    Session? session,
    String? participantId,
    List<Idea>? ideas,
    bool? loading,
    String? error,
    bool clearError = false,
    bool? connected,
  }) =>
      ParticipantSessionState(
        session: session ?? this.session,
        participantId: participantId ?? this.participantId,
        ideas: ideas ?? this.ideas,
        loading: loading ?? this.loading,
        error: clearError ? null : (error ?? this.error),
        connected: connected ?? this.connected,
      );
}

/// Controller for the participant's session: joining, submitting ideas,
/// voting, and receiving live updates over SSE.
class ParticipantSessionController
    extends Notifier<ParticipantSessionState> {
  StreamSubscription<SseEvent>? _sseSub;

  @override
  ParticipantSessionState build() {
    // Tear down the SSE subscription if the controller is disposed.
    ref.onDispose(() {
      _sseSub?.cancel();
      _sseSub = null;
    });
    return const ParticipantSessionState();
  }

  WorkshopApi get _api => ref.read(workshopApiProvider);
  SseClient get _sse => ref.read(sseClientProvider);

  /// Join a session by its 6-char access code. On success, loads the session
  /// details + existing ideas and opens the SSE stream.
  Future<bool> joinByCode(String accessCode, String name) async {
    state = state.copyWith(loading: true, clearError: true);
    try {
      final join = await _api.joinByCode(accessCode.trim(), name.trim());
      final sessionId = join.sessionId;
      if (sessionId == null) {
        // The backend should always return session_id now; guard regardless.
        state = state.copyWith(
          loading: false,
          error: 'Server did not return a session id',
        );
        return false;
      }
      final session = await _api.getSession(sessionId);
      final ideas = await _api.listIdeas(sessionId);
      state = state.copyWith(
        session: session,
        participantId: join.participantId,
        ideas: ideas,
        loading: false,
        clearError: true,
      );
      _openStream(sessionId);
      return true;
    } catch (e) {
      state = state.copyWith(loading: false, error: '$e');
      return false;
    }
  }

  /// Join by session id (the QR-code path encodes the session id directly).
  Future<bool> joinById(String sessionId, String name) async {
    state = state.copyWith(loading: true, clearError: true);
    try {
      final join = await _api.joinSession(sessionId, name.trim());
      final session = await _api.getSession(sessionId);
      final ideas = await _api.listIdeas(sessionId);
      state = state.copyWith(
        session: session,
        participantId: join.participantId,
        ideas: ideas,
        loading: false,
        clearError: true,
      );
      _openStream(sessionId);
      return true;
    } catch (e) {
      state = state.copyWith(loading: false, error: '$e');
      return false;
    }
  }

  /// Submit a new idea on behalf of the current participant.
  Future<void> submitIdea(String content, {String? category}) async {
    final pid = state.participantId;
    final session = state.session;
    if (pid == null || session == null) {
      state = state.copyWith(error: 'Not joined to a session');
      return;
    }
    state = state.copyWith(loading: true, clearError: true);
    try {
      await _api.submitIdea(
        session.id,
        participantId: pid,
        participantName: session.participants
            .firstWhere((p) => p.id == pid,
                orElse: () => Participant(
                    id: pid, name: 'You', joinedAt: DateTime.now()))
            .name,
        content: content.trim(),
        category: category,
      );
      // The SSE stream will deliver the idea_added event and update the list;
      // no need to optimistically add. Just clear loading.
      state = state.copyWith(loading: false, clearError: true);
    } catch (e) {
      state = state.copyWith(loading: false, error: '$e');
    }
  }

  /// Upvote an idea. Optimistic update + rollback on failure.
  Future<void> vote(String ideaId) async {
    final session = state.session;
    if (session == null) return;

    final original = state.ideas;
    final updated =
        original.map((i) => i.id == ideaId ? i.copyWith(votes: i.votes + 1) : i).toList();
    state = state.copyWith(ideas: updated, clearError: true);

    try {
      final result = await _api.voteIdea(session.id, ideaId);
      final restored = state.ideas
          .map((i) => i.id == ideaId ? i.copyWith(votes: result.votes) : i)
          .toList();
      state = state.copyWith(ideas: restored, clearError: true);
    } catch (e) {
      // Roll back to the pre-vote list.
      state = state.copyWith(ideas: original, error: '$e');
    }
  }

  void _openStream(String sessionId) {
    _sseSub?.cancel();
    state = state.copyWith(connected: false);
    _sseSub = _sse.subscribe(sessionId).listen(
      _onSseEvent,
      onError: (e) => state = state.copyWith(connected: false, error: '$e'),
      onDone: () => state = state.copyWith(connected: false),
    );
    state = state.copyWith(connected: true);
  }

  void _onSseEvent(SseEvent event) {
    switch (event.type) {
      case SseEventType.ideaAdded:
        final idea = event.idea;
        if (idea == null) return;
        // Avoid duplicates (the local submit could race the SSE delivery).
        if (state.ideas.any((i) => i.id == idea.id)) return;
        state = state.copyWith(ideas: [...state.ideas, idea]);
      case SseEventType.ideaVoted:
        final ideaId = event.data['idea_id'] as String?;
        final votes = event.data['votes'] as int?;
        if (ideaId == null || votes == null) return;
        final updated = state.ideas
            .map((i) => i.id == ideaId ? i.copyWith(votes: votes) : i)
            .toList();
        state = state.copyWith(ideas: updated);
      case SseEventType.participantJoined:
        // Could bump a live participant count in future; no-op for now.
        break;
      case SseEventType.unknown:
        break;
    }
  }
}

final participantSessionProvider =
    NotifierProvider<ParticipantSessionController, ParticipantSessionState>(
  ParticipantSessionController.new,
);
