import 'package:dio/dio.dart';

import '../config/app_config.dart';
import '../../models/models.dart';
import '../../services/token_storage.dart';

/// Typed client for the Workshop Tool backend.
///
/// All HTTP calls go through this class. A dio interceptor attaches the
/// facilitator bearer token to protected routes when one is stored for the
/// target session. Endpoint paths mirror docs/api-contract.md exactly.
class WorkshopApi {
  WorkshopApi({Dio? dio, TokenStorage? tokenStorage})
      : _dio = dio ?? Dio(BaseOptions(baseUrl: AppConfig.apiBaseUrl)),
        _tokens = tokenStorage ?? TokenStorage() {
    _dio.interceptors.add(
      InterceptorsWrapper(
        onRequest: _attachTokenIfKnown,
      ),
    );
  }

  final Dio _dio;
  final TokenStorage _tokens;

  // ── Sessions ───────────────────────────────────────────────

  /// POST /sessions — create a session. Returns it with `facilitatorToken`
  /// populated; the caller should persist it (see [TokenStorage]).
  Future<Session> createSession({
    required String topic,
    required String framework,
    List<String>? customCategories,
  }) async {
    final res = await _dio.post(
      '/sessions',
      data: Session.createBody(
        topic: topic,
        framework: framework,
        customCategories: customCategories,
      ),
    );
    final session = Session.fromJson(res.data as Map<String, dynamic>);
    // Persist the facilitator token immediately if one was issued.
    if (session.facilitatorToken != null) {
      await _tokens.saveFacilitator(session.id, session.facilitatorToken!);
    }
    return session;
  }

  /// GET /sessions/{id}
  Future<Session> getSession(String sessionId) async {
    final res = await _dio.get('/sessions/$sessionId');
    return Session.fromJson(res.data as Map<String, dynamic>);
  }

  /// POST /sessions/{id}/join  (name in the JSON body — PII stays out of URLs)
  Future<JoinResponse> joinSession(String sessionId, String name) async {
    final res = await _dio.post(
      '/sessions/$sessionId/join',
      data: {'name': name},
    );
    final join = JoinResponse.fromJson(res.data as Map<String, dynamic>);
    await _persistParticipantToken(join, sessionId);
    return join;
  }

  /// POST /sessions/join/{access_code}
  Future<JoinResponse> joinByCode(String accessCode, String name) async {
    final res = await _dio.post(
      '/sessions/join/$accessCode',
      data: {'name': name},
    );
    final join = JoinResponse.fromJson(res.data as Map<String, dynamic>);
    // The joined session id is in the response (the caller only knew the code).
    await _persistParticipantToken(join, join.sessionId ?? '');
    return join;
  }

  Future<void> _persistParticipantToken(JoinResponse join, String sessionId) async {
    if (join.participantToken != null && sessionId.isNotEmpty) {
      await _tokens.saveParticipant(sessionId, join.participantToken!);
    }
  }

  // ── Ideas ──────────────────────────────────────────────────

  /// POST /sessions/{id}/ideas
  Future<Idea> submitIdea(
    String sessionId, {
    required String participantId,
    required String participantName,
    required String content,
    String? category,
  }) async {
    final res = await _dio.post(
      '/sessions/$sessionId/ideas',
      data: Idea.createBody(
        participantId: participantId,
        participantName: participantName,
        content: content,
        category: category,
      ),
    );
    return Idea.fromJson(res.data as Map<String, dynamic>);
  }

  /// GET /sessions/{id}/ideas
  Future<List<Idea>> listIdeas(String sessionId) async {
    final res = await _dio.get('/sessions/$sessionId/ideas');
    final list = res.data as List<dynamic>;
    return list
        .map((e) => Idea.fromJson(e as Map<String, dynamic>))
        .toList();
  }

  /// POST /sessions/{id}/ideas/{ideaId}/vote
  Future<Idea> voteIdea(String sessionId, String ideaId) async {
    final res = await _dio.post('/sessions/$sessionId/ideas/$ideaId/vote');
    return Idea.fromJson(res.data as Map<String, dynamic>);
  }

  // ── Analysis ───────────────────────────────────────────────

  /// POST /sessions/{id}/analyse — requires the facilitator token.
  Future<AnalysisResult> runAnalysis(String sessionId) async {
    final res = await _dio.post(
      '/sessions/$sessionId/analyse',
      options: Options(headers: await _authHeader(sessionId)),
    );
    return AnalysisResult.fromJson(res.data as Map<String, dynamic>);
  }

  /// GET /sessions/{id}/analysis
  Future<AnalysisResult> getAnalysis(String sessionId) async {
    final res = await _dio.get('/sessions/$sessionId/analysis');
    return AnalysisResult.fromJson(res.data as Map<String, dynamic>);
  }

  /// GET /sessions/{id}/report — returns the PDF bytes.
  Future<List<int>> downloadReport(String sessionId) async {
    final res = await _dio.get(
      '/sessions/$sessionId/report',
      options: Options(
        responseType: ResponseType.bytes,
        headers: await _authHeader(sessionId),
      ),
    );
    return (res.data as List).cast<int>();
  }

  // ── Health ─────────────────────────────────────────────────

  /// GET /health
  Future<Map<String, dynamic>> health() async {
    final res = await _dio.get('/health');
    return res.data as Map<String, dynamic>;
  }

  // ── Internals ──────────────────────────────────────────────

  /// Interceptor: attach the stored bearer token to protected paths so callers
  /// don't pass headers manually. Facilitator token for /analyse and /report;
  /// participant token (falling back to facilitator) for the idea routes.
  Future<void> _attachTokenIfKnown(
    RequestOptions options,
    RequestInterceptorHandler handler,
  ) async {
    final path = options.path;
    final segments = path.split('/').where((s) => s.isNotEmpty).toList();
    if (segments.length >= 2 && segments[0] == 'sessions') {
      final sessionId = segments[1];
      final String? token;
      if (path.endsWith('/analyse') || path.endsWith('/report')) {
        token = await _tokens.readFacilitator(sessionId);
      } else {
        // Idea submit/vote/list: participant preferred, facilitator as fallback.
        token = await _tokens.readAny(sessionId);
      }
      if (token != null) {
        options.headers['Authorization'] = 'Bearer $token';
      }
    }
    handler.next(options);
  }

  Future<Map<String, String>> _authHeader(String sessionId) async {
    final token = await _tokens.readFacilitator(sessionId);
    return token == null ? {} : {'Authorization': 'Bearer $token'};
  }

  /// Best-available bearer token for a session (participant or facilitator).
  /// Used by controllers to authenticate the SSE live stream.
  Future<String?> tokenFor(String sessionId) => _tokens.readAny(sessionId);
}
