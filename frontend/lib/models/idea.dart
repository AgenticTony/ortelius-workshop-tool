/// A single idea submitted by a participant.
class Idea {
  Idea({
    required this.id,
    required this.sessionId,
    required this.participantId,
    required this.participantName,
    required this.content,
    this.category,
    required this.votes,
    required this.createdAt,
    this.votedByMe = false,
  });

  final String id;
  final String sessionId;
  final String participantId;
  final String participantName;
  final String content;
  final String? category;
  final int votes;
  final DateTime createdAt;

  /// Whether the calling participant has voted on this idea. Computed by the
  /// backend per-request (from the idea_votes table); defaults false on
  /// creation or where the caller's identity isn't relevant.
  final bool votedByMe;

  factory Idea.fromJson(Map<String, dynamic> json) {
    return Idea(
      id: json['id'] as String,
      sessionId: json['session_id'] as String,
      participantId: json['participant_id'] as String,
      participantName: json['participant_name'] as String,
      content: json['content'] as String,
      category: json['category'] as String?,
      votes: (json['votes'] as num).toInt(),
      createdAt: DateTime.parse(json['created_at'] as String),
      // Back-compat: older backends don't send this; treat absence as false.
      votedByMe: (json['voted_by_me'] as bool?) ?? false,
    );
  }

  Map<String, dynamic> toJson() => {
        'id': id,
        'session_id': sessionId,
        'participant_id': participantId,
        'participant_name': participantName,
        'content': content,
        'category': category,
        'votes': votes,
        'created_at': createdAt.toIso8601String(),
        'voted_by_me': votedByMe,
      };

  /// Body for POST /sessions/{id}/ideas.
  static Map<String, dynamic> createBody({
    required String participantId,
    required String participantName,
    required String content,
    String? category,
  }) =>
      {
        'participant_id': participantId,
        'participant_name': participantName,
        'content': content,
        if (category != null) 'category': category,
      };

  Idea copyWith({int? votes, bool? votedByMe}) => Idea(
        id: id,
        sessionId: sessionId,
        participantId: participantId,
        participantName: participantName,
        content: content,
        category: category,
        votes: votes ?? this.votes,
        createdAt: createdAt,
        votedByMe: votedByMe ?? this.votedByMe,
      );

  @override
  String toString() => 'Idea(id: $id, votes: $votes, votedByMe: $votedByMe, content: "$content")';
}
