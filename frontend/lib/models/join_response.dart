/// Response from POST /sessions/{id}/join and POST /sessions/join/{code}.
/// Carries only the participant ID — the frontend stores it for later calls.
class JoinResponse {
  JoinResponse({required this.participantId});

  final String participantId;

  factory JoinResponse.fromJson(Map<String, dynamic> json) {
    return JoinResponse(participantId: json['participant_id'] as String);
  }

  @override
  String toString() => 'JoinResponse(participantId: $participantId)';
}
