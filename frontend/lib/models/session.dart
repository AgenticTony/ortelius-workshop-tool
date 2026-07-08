import 'participant.dart';

/// A workshop session. Created by the facilitator.
///
/// `facilitatorToken` is only populated on the create-session response —
/// the frontend must store it securely and send it as a bearer token on
/// protected routes (/analyse, /report). It is null on every other endpoint.
class Session {
  Session({
    required this.id,
    required this.topic,
    required this.framework,
    required this.customCategories,
    required this.accessCode,
    required this.status,
    required this.participants,
    required this.createdAt,
    this.facilitatorToken,
    this.voteBudget = 3,
  });

  final String id;
  final String topic;
  final String framework; // "swot" | "pestel" | "custom"
  final List<String> customCategories;
  final String accessCode;
  final String status; // "active" | "closed" | "analysed"
  final List<Participant> participants;
  final DateTime createdAt;

  /// Plaintext facilitator token. Only present on POST /sessions responses.
  final String? facilitatorToken;

  /// Dot-voting: max votes each participant may cast across the session.
  final int voteBudget;

  factory Session.fromJson(Map<String, dynamic> json) {
    return Session(
      id: json['id'] as String,
      topic: json['topic'] as String,
      framework: json['framework'] as String,
      customCategories:
          (json['custom_categories'] as List<dynamic>).cast<String>(),
      accessCode: json['access_code'] as String,
      status: json['status'] as String,
      participants: (json['participants'] as List<dynamic>)
          .map((p) => Participant.fromJson(p as Map<String, dynamic>))
          .toList(),
      createdAt: DateTime.parse(json['created_at'] as String),
      facilitatorToken: json['facilitator_token'] as String?,
      // Back-compat: older backends don't send this; default to 3.
      voteBudget: (json['vote_budget'] as num?)?.toInt() ?? 3,
    );
  }

  Map<String, dynamic> toJson() => {
        'id': id,
        'topic': topic,
        'framework': framework,
        'custom_categories': customCategories,
        'access_code': accessCode,
        'status': status,
        'participants': participants.map((p) => p.toJson()).toList(),
        'created_at': createdAt.toIso8601String(),
        // facilitatorToken deliberately omitted — never re-sent to the API.
      };

  /// Body for POST /sessions.
  static Map<String, dynamic> createBody({
    required String topic,
    required String framework,
    List<String>? customCategories,
  }) =>
      {
        'topic': topic,
        'framework': framework,
        if (customCategories != null) 'custom_categories': customCategories,
      };

  @override
  String toString() =>
      'Session(id: $id, topic: $topic, framework: $framework, status: $status)';
}
