// Web-only SSE implementation using the browser-native EventSource API.
//
// WHY THIS EXISTS: Dio's `responseType: ResponseType.stream` does NOT work on
// Flutter Web — Dio uses XMLHttpRequest under the hood on web, and XHR buffers
// the entire response before handing it to Dart, so SSE events never arrive
// incrementally (https://github.com/flutterchina/dio/issues/966). EventSource
// is the browser's purpose-built API for text/event-stream and streams events
// as they arrive.
//
// This file is the "web" side of the conditional import in sse_client.dart.
// It MUST NOT be compiled on non-web platforms because it imports
// dart:js_interop, which doesn't exist there.
import 'dart:async';
import 'dart:convert';
import 'dart:js_interop';

import 'package:dio/dio.dart';
import 'package:web/web.dart' as web;

import '../core/config/app_config.dart';
import '../models/models.dart';

/// Open the SSE stream via the browser-native EventSource. Web only.
///
/// Mirrors [subscribeSse] in sse_stream_io.dart: returns a broadcast
/// [Stream] of parsed [SseEvent]s. The caller owns the subscription; we close
/// the underlying EventSource when the stream is cancelled.
///
/// [dio] is unused on web (EventSource replaces Dio for SSE) but accepted to
/// keep the signature identical across the two platform impls so the facade
/// can call one `platform.subscribeSse(...)` unconditionally.
Stream<SseEvent> subscribeSse(String sessionId, Dio dio) {
  final controller = StreamController<SseEvent>.broadcast();
  final url = '${AppConfig.apiBaseUrl}/sessions/$sessionId/ideas/stream';

  final source = web.EventSource(url);

  // Messages: the server sends `event: idea_added\ndata: {...}\n\n`. EventSource
  // fires the named event (idea_added/idea_voted/...) AND a generic message
  // event. We listen on `onMessage` since our data payload always carries the
  // type field in the JSON — SseEvent.fromJson reads it.
  final messageSub = source.onMessage.listen((event) {
    final jsData = event.data;
    if (jsData == null) return;
    final dataStr = (jsData as JSString).toDart;
    if (dataStr.isEmpty) return;
    try {
      final json = jsonDecode(dataStr) as Map<String, dynamic>;
      controller.add(SseEvent.fromJson(json));
    } catch (_) {
      // Malformed payload — drop rather than kill the whole stream.
    }
  });

  // EventSource auto-reconnects on transient errors (network blips). But if
  // the connection dies hard, forward the error so the controllers' existing
  // reconnect logic kicks in too.
  final errorSub = source.onError.listen((_) {
    // Only surface an error if the EventSource gave up (readyState == CLOSED).
    // While it's CONNECTING (auto-retrying), stay quiet — the heartbeats will
    // resume once it reconnects.
    if (source.readyState == web.EventSource.CLOSED) {
      controller.addError('SSE connection closed');
    }
  });

  // Tear down the EventSource + listeners when the consumer cancels.
  controller.onCancel = () {
    messageSub.cancel();
    errorSub.cancel();
    source.close();
  };

  return controller.stream;
}
