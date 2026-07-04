import 'dart:async';
import 'dart:typed_data';

import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/app_providers.dart';
import '../../core/api/workshop_api.dart';
import '../../models/models.dart';
import '../../services/sse_client.dart';

/// State held for the facilitator's current session.
class FacilitatorSessionState {
  const FacilitatorSessionState({
    this.session,
    this.ideas = const [],
    this.participantCount = 0,
    this.analysis,
    this.creating = false,
    this.analysing = false,
    this.connected = false,
    this.error,
    this.pdfBytes,
  });

  final Session? session;
  final List<Idea> ideas;
  final int participantCount;
  final AnalysisResult? analysis;

  /// True while a create-session call is in flight.
  final bool creating;
  /// True while the AI analysis call is in flight.
  final bool analysing;
  /// Whether the SSE live stream is open.
  final bool connected;
  final String? error;

  /// Cached report PDF bytes (set after a download). Kept in state so the UI
  /// can offer "open" without re-downloading.
  final Uint8List? pdfBytes;

  bool get hasSession => session != null;

  FacilitatorSessionState copyWith({
    Session? session,
    List<Idea>? ideas,
    int? participantCount,
    AnalysisResult? analysis,
    bool? creating,
    bool? analysing,
    bool? connected,
    String? error,
    bool clearError = false,
    Uint8List? pdfBytes,
  }) =>
      FacilitatorSessionState(
        session: session ?? this.session,
        ideas: ideas ?? this.ideas,
        participantCount: participantCount ?? this.participantCount,
        analysis: analysis ?? this.analysis,
        creating: creating ?? this.creating,
        analysing: analysing ?? this.analysing,
        connected: connected ?? this.connected,
        error: clearError ? null : (error ?? this.error),
        pdfBytes: pdfBytes ?? this.pdfBytes,
      );
}

/// Controller for the facilitator side: creating a session, watching live
/// input, triggering AI analysis, and downloading the PDF report.
class FacilitatorSessionController
    extends Notifier<FacilitatorSessionState> {
  StreamSubscription<SseEvent>? _sseSub;

  @override
  FacilitatorSessionState build() {
    ref.onDispose(() {
      _disposed = true;
      _reconnectTimer?.cancel();
      _sseSub?.cancel();
      _sseSub = null;
    });
    return const FacilitatorSessionState();
  }

  WorkshopApi get _api => ref.read(workshopApiProvider);
  SseClient get _sse => ref.read(sseClientProvider);

  /// Create a session. The facilitator token is persisted by the API client
  /// (see WorkshopApi.createSession -> TokenStorage); we just open the live
  /// stream for the resulting session.
  Future<bool> createSession({
    required String topic,
    required String framework,
    List<String>? customCategories,
  }) async {
    state = state.copyWith(creating: true, clearError: true);
    try {
      final session = await _api.createSession(
        topic: topic.trim(),
        framework: framework,
        customCategories: customCategories,
      );
      state = state.copyWith(
        session: session,
        creating: false,
        participantCount: 0,
        clearError: true,
      );
      _openStream(session.id);
      return true;
    } catch (e) {
      state = state.copyWith(creating: false, error: '$e');
      return false;
    }
  }

  /// Reconnect to an existing session by id (e.g. on app restart). Loads the
  /// session, current ideas/participants, and any existing analysis.
  Future<bool> resume(String sessionId) async {
    state = state.copyWith(creating: true, clearError: true);
    try {
      final session = await _api.getSession(sessionId);
      final ideas = await _api.listIdeas(sessionId);
      AnalysisResult? analysis;
      try {
        analysis = await _api.getAnalysis(sessionId);
      } catch (_) {
        // No analysis yet — fine.
      }
      state = state.copyWith(
        session: session,
        ideas: ideas,
        participantCount: session.participants.length,
        analysis: analysis,
        creating: false,
        clearError: true,
      );
      _openStream(sessionId);
      return true;
    } catch (e) {
      state = state.copyWith(creating: false, error: '$e');
      return false;
    }
  }

  /// Trigger AI clustering + summarisation. Requires the facilitator token,
  /// which the API client attaches automatically via its interceptor.
  Future<bool> runAnalysis() async {
    final session = state.session;
    if (session == null) return false;
    state = state.copyWith(analysing: true, clearError: true);
    try {
      final result = await _api.runAnalysis(session.id);
      state = state.copyWith(analysing: false, analysis: result, clearError: true);
      return true;
    } catch (e) {
      state = state.copyWith(analysing: false, error: '$e');
      return false;
    }
  }

  /// Download the PDF report. Returns the bytes (also cached in state).
  Future<Uint8List?> downloadReport() async {
    final session = state.session;
    if (session == null) return null;
    try {
      final bytes = await _api.downloadReport(session.id);
      state = state.copyWith(pdfBytes: Uint8List.fromList(bytes), clearError: true);
      return state.pdfBytes;
    } catch (e) {
      state = state.copyWith(error: '$e');
      return null;
    }
  }

  /// Clear the current error (for dismissible banners).
  void dismissError() => state = state.copyWith(clearError: true);

  String? _streamSessionId; // the session we're (re)connecting to
  bool _disposed = false; // guards reconnection after dispose
  Timer? _reconnectTimer;
  int _reconnectAttempts = 0; // for exponential backoff

  void _openStream(String sessionId) {
    _streamSessionId = sessionId;
    _reconnectTimer?.cancel();
    _sseSub?.cancel();
    state = state.copyWith(connected: false);
    _sseSub = _sse.subscribe(sessionId).listen(
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
  /// network blip doesn't strand the client. Uses exponential backoff with a
  /// cap so a dead/ended session isn't hammered indefinitely (2s, 4s, 8s … 30s).
  void _scheduleReconnect() {
    if (_disposed || _streamSessionId == null) return;
    _reconnectTimer?.cancel();
    _reconnectAttempts += 1;
    final base = (_reconnectAttempts * 2).clamp(2, 30);
    _reconnectTimer = Timer(Duration(seconds: base), () {
      if (_disposed || _streamSessionId == null) return;
      _openStream(_streamSessionId!);
    });
  }

  void _onSseEvent(SseEvent event) {
    switch (event.type) {
      case SseEventType.ideaAdded:
        final idea = event.idea;
        if (idea == null) return;
        if (state.ideas.any((i) => i.id == idea.id)) return;
        state = state.copyWith(ideas: [...state.ideas, idea]);
      case SseEventType.ideaVoted:
        final ideaId = event.data['idea_id'] as String?;
        final votes = (event.data['votes'] as num?)?.toInt();
        if (ideaId == null || votes == null) return;
        final updated = state.ideas
            .map((i) => i.id == ideaId ? i.copyWith(votes: votes) : i)
            .toList();
        state = state.copyWith(ideas: updated);
      case SseEventType.participantJoined:
        final count = (event.data['participant_count'] as num?)?.toInt();
        if (count != null) {
          state = state.copyWith(participantCount: count);
        }
      case SseEventType.unknown:
        break;
    }
  }
}

final facilitatorSessionProvider =
    NotifierProvider<FacilitatorSessionController, FacilitatorSessionState>(
  FacilitatorSessionController.new,
);
