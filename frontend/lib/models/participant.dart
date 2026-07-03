/// A workshop participant. Created when someone joins a session.
class Participant {
  Participant({
    required this.id,
    required this.name,
    required this.joinedAt,
  });

  final String id;
  final String name;
  final DateTime joinedAt;

  factory Participant.fromJson(Map<String, dynamic> json) {
    return Participant(
      id: json['id'] as String,
      name: json['name'] as String,
      joinedAt: DateTime.parse(json['joined_at'] as String),
    );
  }

  Map<String, dynamic> toJson() => {
        'id': id,
        'name': name,
        'joined_at': joinedAt.toIso8601String(),
      };

  @override
  String toString() => 'Participant(id: $id, name: $name)';
}
