import 'dart:async';
import 'dart:convert';

import 'package:dio/dio.dart';

import '../core/config/app_config.dart';
import '../models/models.dart';

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
/// Implementation note: dio's `responseType: ResponseType.stream` gives us the
/// raw byte stream; we decode it UTF-8, split on blank lines into frames, and
/// parse each frame's `data:` line (the backend always includes the type in
/// the JSON payload too, so we rely on `SseEvent.fromJson`).
class SseClient {
  SseClient({Dio? dio}) : _dio = dio ?? Dio(BaseOptions(baseUrl: AppConfig.apiBaseUrl));

  final Dio _dio;
  Response<ResponseBody>? _response;
  StreamSubscription<List<int>>? _subscription;

  /// Whether the stream is currently open.
  bool get isActive => _subscription != null;

  /// Open the SSE stream for [sessionId] and return a broadcast [Stream] of
  /// parsed events. Caller should keep a subscription and call [close] when
  /// done (e.g. in a screen's dispose()).
  Stream<SseEvent> subscribe(String sessionId) {
    // Late controller so we can reference it in the error handler.
    final controller = StreamController<SseEvent>.broadcast();

    () async {
      try {
        _response = await _dio.get<ResponseBody>(
          '/sessions/$sessionId/ideas/stream',
          options: Options(
            responseType: ResponseType.stream,
            headers: {'Accept': 'text/event-stream'},
            // SSE is long-lived; no overall timeout.
            receiveTimeout: null,
          ),
        );
        final buffer = StringBuffer();
        _subscription = _response!.data!.stream.listen(
          (bytes) {
            buffer.write(utf8.decode(bytes));
            // Process complete frames (terminated by a blank line). The
            // server may chunk multiple frames or split one, so we loop.
            while (true) {
              final s = buffer.toString();
              final idx = s.indexOf('\n\n');
              if (idx == -1) break;
              final frame = s.substring(0, idx);
              buffer.clear();
              buffer.write(s.substring(idx + 2));
              _handleFrame(frame, controller);
            }
          },
          onError: (Object e) => controller.addError(e),
          onDone: () => controller.close(),
          cancelOnError: true,
        );
      } catch (e) {
        controller.addError(e);
        controller.close();
      }
    }();

    return controller.stream;
  }

  void _handleFrame(String frame, StreamSink<SseEvent> sink) {
    String? dataLine;
    for (final line in frame.split('\n')) {
      // Comment lines (": connected", ": heartbeat") are ignored.
      if (line.startsWith(':')) continue;
      if (line.startsWith('data:')) {
        dataLine = line.substring(5).trim();
      }
    }
    if (dataLine == null || dataLine.isEmpty) return;
    try {
      final json = jsonDecode(dataLine) as Map<String, dynamic>;
      sink.add(SseEvent.fromJson(json));
    } catch (_) {
      // Malformed payload — drop rather than kill the whole stream.
    }
  }

  /// Tear down the connection. Safe to call multiple times.
  Future<void> close() async {
    await _subscription?.cancel();
    _subscription = null;
    _response = null;
  }
}
