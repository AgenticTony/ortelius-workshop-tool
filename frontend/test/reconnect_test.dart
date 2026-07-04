// Unit tests for the SSE reconnect backoff helper.
//
// Guards against regressing to the original flat/linear retry (which hammered
// a dead session every 2s). Asserts exponential growth, the 30s base cap, and
// the ±25% jitter bounds.
import 'package:flutter_test/flutter_test.dart';
import 'package:workshop_tool/core/reconnect.dart';

void main() {
  group('reconnectDelay', () {
    test('grows exponentially, not linearly', () {
      // attempt 1 → ~2s, 2 → ~4s, 3 → ~8s (linear would be 2,4,6).
      // Use the midpoint (no-jitter) expectation by checking the band.
      expect(reconnectDelay(1).inMilliseconds, inInclusiveRange(1500, 2500));
      expect(reconnectDelay(2).inMilliseconds, inInclusiveRange(3000, 5000));
      expect(reconnectDelay(3).inMilliseconds, inInclusiveRange(6000, 10000));
      expect(reconnectDelay(4).inMilliseconds, inInclusiveRange(12000, 20000));
    });

    test('caps the base delay at 30s (±jitter)', () {
      // Beyond the exponential knee the base is clamped to 30s; jitter then
      // varies the result within ±25% of 30s.
      for (final attempt in [5, 6, 10, 50]) {
        final ms = reconnectDelay(attempt).inMilliseconds;
        expect(ms, inInclusiveRange(22500, 37500), reason: 'attempt $attempt');
      }
    });

    test('never returns a non-positive delay', () {
      for (var a = 1; a <= 20; a++) {
        expect(reconnectDelay(a).inMilliseconds, greaterThan(0));
      }
    });
  });
}
