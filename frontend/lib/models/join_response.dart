/// Response from POST /sessions/{id}/join and POST /sessions/join/{code}.
///
/// Carries the participant ID and (for code-join) the session ID so the client
/// can resolve the session it joined and subscribe to the SSE stream.
class JoinResponse {
  JoinResponse({required this.participantId, this.sessionId, this.participantToken});

  final String participantId;

  /// Populated by both join routes; essential for the code-join path where
  /// the client doesn't otherwise know the session id.
  final String? sessionId;

  /// Participant bearer token (issued once at join). Required to submit ideas,
  /// vote, and open the SSE stream. Persist it via [TokenStorage].
  final String? participantToken;

  factory JoinResponse.fromJson(Map<String, dynamic> json) {
    return JoinResponse(
      participantId: json['participant_id'] as String,
      sessionId: json['session_id'] as String?,
      participantToken: json['participant_token'] as String?,
    );
  }

  @override
  String toString() =>
      'JoinResponse(participantId: $participantId, sessionId: $sessionId)';
}
