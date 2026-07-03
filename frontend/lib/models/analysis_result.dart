/// The AI analysis result for a session.
///
/// `categories` is a map of framework category ID (e.g. "strengths",
/// "political") to the ideas clustered into it. Keys are dynamic — they
/// depend on the session's framework (SWOT, PESTEL, or custom).
class AnalysisResult {
  AnalysisResult({
    required this.sessionId,
    required this.framework,
    required this.categories,
    required this.keyThemes,
    required this.decisionsMade,
    required this.openQuestions,
    required this.recommendedNextSteps,
  });

  final String sessionId;
  final String framework;
  final Map<String, List<ClusteredIdea>> categories;
  final List<String> keyThemes;
  final List<String> decisionsMade;
  final List<String> openQuestions;
  final List<String> recommendedNextSteps;

  factory AnalysisResult.fromJson(Map<String, dynamic> json) {
    final rawCategories = json['categories'] as Map<String, dynamic>;
    return AnalysisResult(
      sessionId: json['session_id'] as String,
      framework: json['framework'] as String,
      categories: rawCategories.map(
        (key, value) => MapEntry(
          key,
          (value as List<dynamic>)
              .map((e) => ClusteredIdea.fromJson(e as Map<String, dynamic>))
              .toList(),
        ),
      ),
      keyThemes: (json['key_themes'] as List<dynamic>).cast<String>(),
      decisionsMade:
          (json['decisions_made'] as List<dynamic>).cast<String>(),
      openQuestions:
          (json['open_questions'] as List<dynamic>).cast<String>(),
      recommendedNextSteps:
          (json['recommended_next_steps'] as List<dynamic>).cast<String>(),
    );
  }

  @override
  String toString() =>
      'AnalysisResult(session: $sessionId, framework: $framework, '
      'categories: ${categories.keys.toList()})';
}

/// An idea as it appears inside a cluster: a reference to the original plus
/// the AI-generated summary in context.
class ClusteredIdea {
  ClusteredIdea({required this.ideaId, required this.summary});

  final String ideaId;
  final String summary;

  factory ClusteredIdea.fromJson(Map<String, dynamic> json) {
    return ClusteredIdea(
      ideaId: json['idea_id'] as String,
      summary: json['summary'] as String,
    );
  }

  @override
  String toString() => 'ClusteredIdea(ideaId: $ideaId, summary: "$summary")';
}
