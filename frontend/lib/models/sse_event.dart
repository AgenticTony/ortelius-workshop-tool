import 'idea.dart';

/// A typed real-time event from the SSE stream
/// (GET /sessions/{id}/ideas/stream).
///
/// Mirrors the backend event_bus event types. The `data` payload shape
/// depends on `type`:
///  - idea_added          -> full [Idea]
///  - idea_voted          -> {idea_id, votes, voter_id?, action?}
///                           (voter_id + action added with dot-voting;
///                            absent on older backends)
///  - participant_joined  -> {participant_id, name, participant_count}
enum SseEventType { ideaAdded, ideaVoted, participantJoined, unknown }

class SseEvent {
  SseEvent({required this.type, required this.data});

  final SseEventType type;
  final Map<String, dynamic> data;

  /// Parse the raw JSON the SSE "data:" line carries.
  /// Backend sends `{"type": "...", "data": {...}}`.
  factory SseEvent.fromJson(Map<String, dynamic> json) {
    final typeStr = json['type'] as String;
    final payload = (json['data'] as Map<String, dynamic>?) ?? {};
    return SseEvent(
      type: switch (typeStr) {
        'idea_added' => SseEventType.ideaAdded,
        'idea_voted' => SseEventType.ideaVoted,
        'participant_joined' => SseEventType.participantJoined,
        _ => SseEventType.unknown,
      },
      data: payload,
    );
  }

  /// Convenience: if this is an idea_added event, parse the idea.
  Idea? get idea => type == SseEventType.ideaAdded ? Idea.fromJson(data) : null;

  @override
  String toString() => 'SseEvent(type: $type, data: $data)';
}
