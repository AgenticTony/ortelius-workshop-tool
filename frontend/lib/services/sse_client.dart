import 'dart:async';

import 'package:dio/dio.dart';

import '../core/config/app_config.dart';
import '../models/models.dart';

// Conditional import: on web, use the browser-native EventSource (Dio's stream
// mode doesn't work on web — XHR buffers the whole response). On non-web, use
// the Dio-based stream (dart:io HttpClient streams incrementally). Both impls
// expose `Stream<SseEvent> subscribeSse(String sessionId, Dio dio)`.
// ignore: uri_does_not_exist
import 'sse_stream_io.dart'
    if (dart.library.js_interop) 'sse_stream_web.dart' as platform;

/// Subscribes to the backend's Server-Sent Events stream for a session and
/// emits typed [SseEvent]s.
///
/// The backend serves `GET /sessions/{id}/ideas/stream` as `text/event-stream`
/// with frames like:
/// ```
/// event: idea_added
/// data: {"type":"idea_added","data":{...}}
///
/// ```
/// and periodic `: heartbeat` / `: connected` comment lines we ignore.
///
/// Platform handling: on web the stream is opened with the browser's native
/// EventSource (see sse_stream_web.dart); on mobile/desktop it uses Dio's
/// response stream (sse_stream_io.dart). This split exists because Dio's
/// `responseType: stream` relies on XHR on web, which buffers the response and
/// never delivers incremental SSE events.
class SseClient {
  SseClient({Dio? dio})
      : _dio = dio ?? Dio(BaseOptions(baseUrl: AppConfig.apiBaseUrl));

  final Dio _dio;

  /// Open the SSE stream for [sessionId] and return a broadcast [Stream] of
  /// parsed events. Caller should keep a subscription and cancel it when done
  /// (e.g. in a controller's dispose/reconnect).
  Stream<SseEvent> subscribe(String sessionId) =>
      platform.subscribeSse(sessionId, _dio);
}
