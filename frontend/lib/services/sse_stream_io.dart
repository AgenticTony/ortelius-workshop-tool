// SSE stream implementation for non-web platforms (iOS, Android, desktop).
//
// Dio's `responseType: ResponseType.stream` works here because Dio uses
// dart:io's HttpClient on these platforms, which exposes incremental response
// chunks. On the web platform this does NOT work — Dio falls back to XHR,
// which buffers the whole response (see sse_stream_web.dart for the EventSource
// impl used there).
//
// This file is the "stub" side of the conditional import in sse_client.dart:
// it is compiled on every platform that is NOT web.
import 'dart:async';
import 'dart:convert';

import 'package:dio/dio.dart';

import '../models/models.dart';

/// Open the SSE stream via Dio (dart:io HttpClient). Used on mobile/desktop.
///
/// Mirrors [subscribeSse] in sse_stream_web.dart: returns a broadcast
/// [Stream] of parsed [SseEvent]s. The caller owns the subscription and
/// should cancel it when done (the controllers cancel on dispose/reconnect).
Stream<SseEvent> subscribeSse(String sessionId, Dio dio) {
  final controller = StreamController<SseEvent>.broadcast();

  () async {
    try {
      final response = await dio.get<ResponseBody>(
        '/sessions/$sessionId/ideas/stream',
        options: Options(
          responseType: ResponseType.stream,
          headers: {'Accept': 'text/event-stream'},
          // SSE is long-lived; no overall timeout.
          receiveTimeout: null,
        ),
      );
      final buffer = StringBuffer();
      final subscription = response.data!.stream.listen(
        (bytes) {
          buffer.write(utf8.decode(bytes));
          // Process complete frames (terminated by a blank line). The server
          // may chunk multiple frames or split one, so we loop.
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
      // If the stream is cancelled (e.g. controller disposed / reconnect),
      // cancel the underlying dio subscription.
      controller.onCancel = () => subscription.cancel();
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
