import 'dart:math' show Random;

/// Exponential backoff (with jitter) for SSE/stream reconnects.
///
/// The SSE controllers retry when the stream drops. A flat 2s retry on a
/// dead/ended session hammers the API forever; a real backoff grows the gap
/// so a transient blip is recovered fast but a hard failure backs off. Jitter
/// (±25% by default) de-synchronizes many clients retrying after the same
/// backend restart, avoiding a thundering herd.
///
/// Callers reset their attempt counter to 0 on a successful open, so the
/// sequence restarts after recovery.
const _baseDelay = Duration(seconds: 2);
const _maxDelay = Duration(seconds: 30);

final _rng = Random();

/// Delay before the [attempt]-th reconnect (1-based).
///
/// Grows as 2s, 4s, 8s, 16s, then the 30s cap, with ±[jitterFraction] random
/// jitter. [attempt] is clamped internally so very large counts don't overflow
/// the shift — once the cap is reached the delay stops growing anyway.
Duration reconnectDelay(int attempt, {double jitterFraction = 0.25}) {
  // 2^(attempt-1): attempt 1→1 (2s), 2→2 (4s), 3→4 (8s), 4→8 (16s), 5→16 (32s,
  // capped). Clamp the shift to a safe ceiling so a session that never recovers
  // can't overflow the bit shift; once the raw delay exceeds the cap the result
  // is constant anyway.
  final shift = (attempt - 1).clamp(0, 30);
  final raw = _baseDelay * (1 << shift);
  final capped = raw > _maxDelay ? _maxDelay : raw;
  final jitterMs = (capped.inMilliseconds * jitterFraction).round();
  // Symmetric jitter in [-jitterMs, +jitterMs].
  final offset = (_rng.nextDouble() * 2 - 1) * jitterMs;
  return Duration(milliseconds: capped.inMilliseconds + offset.round());
}
