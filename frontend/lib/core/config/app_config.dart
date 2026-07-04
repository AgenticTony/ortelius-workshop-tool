import 'package:flutter/foundation.dart';
import 'package:flutter_dotenv/flutter_dotenv.dart';

// Conditional import: the web impl reads window.location; the stub returns null.
// ignore: uri_does_not_exist
import 'origin_stub.dart'
    if (dart.library.js_interop) 'origin_web.dart' as origin;

/// Reads environment configuration loaded from assets/.env via flutter_dotenv.
///
/// URL precedence (first match wins):
///   1. API_BASE_URL in .env — explicit wins. Production builds bake the real
///      API host (https://workshop-api-…onrender.com) in via a Docker build
///      arg so the deployed image points at the API service directly.
///   2. On web only, derive the API from the browser origin + :8000 — useful
///      for local dev (frontend on :7355, API on :8000 of the same host, and
///      for a phone joining the same LAN). This is ONLY a fallback when no
///      explicit API_BASE_URL is set.
///   3. http://localhost:8000 — last-resort default for non-web dev.
class AppConfig {
  const AppConfig._();

  /// Must be called before any config value is read — typically in main()
  /// before runApp().
  static Future<void> load() async {
    await dotenv.load(fileName: '.env');
  }

  static String get apiBaseUrl {
    // 1. Explicit API_BASE_URL always wins (production + mobile dev).
    final explicit = dotenv.maybeGet('API_BASE_URL');
    if (explicit != null && explicit.isNotEmpty) {
      return explicit.endsWith('/')
          ? explicit.substring(0, explicit.length - 1)
          : explicit;
    }

    // 2. Web fallback: derive from browser origin + :8000 (local/LAN dev).
    if (kIsWeb) {
      final o = origin.currentOrigin();
      if (o != null && o.isNotEmpty) {
        final uri = Uri.parse(o);
        return '${uri.scheme}://${uri.host}:8000';
      }
    }

    // 3. Last resort for non-web dev.
    return 'http://localhost:8000';
  }

  /// The origin the web app itself is served from (for building join URLs in
  /// QR codes). On web this is the browser location; elsewhere null.
  static String? get webOrigin => origin.currentOrigin();
}
