import 'dart:async';

import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/app_providers.dart';
import '../../core/api/workshop_api.dart';
import '../../core/reconnect.dart';
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
      _disposed = true;
      _reconnectTimer?.cancel();
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
      // Source the SSE token from storage (single source of truth, same one the
      // REST interceptor uses) so a storage-write failure can't leave SSE
      // connected while submit/vote 401s.
      _streamToken = await _api.tokenFor(sessionId);
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
      // Source the SSE token from storage (single source of truth, same one the
      // REST interceptor uses) so a storage-write failure can't leave SSE
      // connected while submit/vote 401s.
      _streamToken = await _api.tokenFor(sessionId);
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
      final idea = await _api.submitIdea(
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
      // Add the returned idea to the local list immediately. SSE should also
      // deliver it, but mobile browsers can buffer SSE, so don't rely on it
      // for the submitter's own idea. _onSseEvent dedupes by id.
      if (!state.ideas.any((i) => i.id == idea.id)) {
        state = state.copyWith(ideas: [...state.ideas, idea]);
      }
      state = state.copyWith(loading: false, clearError: true);
    } catch (e) {
      state = state.copyWith(loading: false, error: '$e');
    }
  }

  /// Toggle a dot-vote on an idea. If already voted, removes the vote;
  /// otherwise casts one (budget permitting). Optimistic update + rollback.
  Future<void> vote(String ideaId) async {
    final session = state.session;
    if (session == null) return;

    final current = state.ideas.firstWhere(
      (i) => i.id == ideaId,
      orElse: () => state.ideas.first, // defensive; shouldn't happen
    );
    final wasVoted = current.votedByMe;

    // Budget pre-check before casting a new vote. If the user is trying to
    // vote (not un-vote) and has already spent the budget, surface the error.
    if (!wasVoted) {
      final used = state.ideas.where((i) => i.votedByMe).length;
      if (used >= session.voteBudget) {
        state = state.copyWith(
          error: "You've used all ${session.voteBudget} of your votes.",
        );
        return;
      }
    }

    // Optimistic toggle: flip votedByMe + adjust the count ±1.
    final updated = state.ideas
        .map((i) => i.id == ideaId
            ? i.copyWith(
                votes: wasVoted ? i.votes - 1 : i.votes + 1,
                votedByMe: !wasVoted,
              )
            : i)
        .toList();
    state = state.copyWith(ideas: updated, clearError: true);

    try {
      final result = wasVoted
          ? await _api.unvoteIdea(session.id, ideaId)
          : await _api.voteIdea(session.id, ideaId);
      // Reconcile this idea against current state (concurrent SSE may have
      // landed during the await). Trust the server's count + voted_by_me.
      final reconciled = state.ideas
          .map((i) => i.id == ideaId
              ? i.copyWith(votes: result.votes, votedByMe: result.votedByMe)
              : i)
          .toList();
      state = state.copyWith(ideas: reconciled, clearError: true);
    } catch (e) {
      // Roll back ONLY this idea's optimistic toggle — restoring a whole-state
      // snapshot captured pre-await would wipe concurrent SSE updates.
      final rolledBack = state.ideas
          .map((i) => i.id == ideaId
              ? i.copyWith(
                  votes: wasVoted ? i.votes + 1 : i.votes - 1,
                  votedByMe: wasVoted,
                )
              : i)
          .toList();
      state = state.copyWith(ideas: rolledBack, error: '$e');
    }
  }

  /// Clear the current error (for dismissible banners).
  void dismissError() => state = state.copyWith(clearError: true);

  String? _streamSessionId; // the session we're (re)connecting to
  String? _streamToken; // participant/facilitator token for the SSE stream
  bool _disposed = false; // guards reconnection after dispose
  Timer? _reconnectTimer;
  int _reconnectAttempts = 0; // for exponential backoff

  void _openStream(String sessionId) {
    _streamSessionId = sessionId;
    _reconnectTimer?.cancel();
    _sseSub?.cancel();
    state = state.copyWith(connected: false);
    final token = _streamToken;
    if (token == null || token.isEmpty) {
      // No usable token (e.g. storage write failed, or resume before join).
      // Surface it instead of subscribing with '' and looping 401 forever.
      state = state.copyWith(
        connected: false,
        error: 'Not authenticated for live updates — please rejoin.',
      );
      return;
    }
    _sseSub = _sse.subscribe(sessionId, token: token).listen(
      _onSseEvent,
      onError: (Object e) {
        state = state.copyWith(connected: false, error: '$e');
        _scheduleReconnect();
      },
      onDone: () {
        state = state.copyWith(connected: false);
        _scheduleReconnect();
      },
    );
    // A fresh successful open resets the backoff counter.
    _reconnectAttempts = 0;
    state = state.copyWith(connected: true);
  }

  /// Reconnect the SSE stream after a delay, so a backend restart or brief
  /// network blip doesn't strand the client. Exponential backoff with jitter
  /// and a 30s cap (see [reconnectDelay]) — a dead/ended session is retried
  /// less and less aggressively rather than hammered every 2s.
  void _scheduleReconnect() {
    if (_disposed || _streamSessionId == null) return;
    _reconnectTimer?.cancel();
    _reconnectAttempts += 1;
    _reconnectTimer = Timer(reconnectDelay(_reconnectAttempts), () {
      if (_disposed || _streamSessionId == null) return;
      _openStream(_streamSessionId!);
    });
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
        final votes = (event.data['votes'] as num?)?.toInt();
        if (ideaId == null || votes == null) return;
        // Dot-voting: the payload now carries who voted and whether it was a
        // vote or an unvote. If *we* were the actor, update our votedByMe flag
        // (it's already correct via the optimistic update, but this covers
        // reconnect/reload reconciliation).
        final voterId = event.data['voter_id'] as String?;
        final action = event.data['action'] as String?;
        final isMine = voterId != null && voterId == state.participantId;
        final votedByMe = isMine ? (action != 'unvote') : null;
        final updated = state.ideas
            .map((i) => i.id == ideaId
                ? i.copyWith(
                    votes: votes,
                    votedByMe: votedByMe ?? i.votedByMe,
                  )
                : i)
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
