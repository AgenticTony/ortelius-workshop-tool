import 'package:flutter/foundation.dart';
import 'package:flutter_dotenv/flutter_dotenv.dart';

// Conditional import: the web impl reads window.location; the stub returns null.
// ignore: uri_does_not_exist
import 'origin_stub.dart'
    if (dart.library.js_interop) 'origin_web.dart' as origin;

/// Reads environment configuration loaded from assets/.env via flutter_dotenv.
///
/// On web, the API base URL is derived from the browser's current origin so
/// the same build works from any host (simulator, phone over LAN) without
/// rebuilding — the backend is expected to be served on the adjacent port 8000
/// of the same host. On non-web (simulator/desktop) it falls back to the
/// API_BASE_URL in .env.
class AppConfig {
  const AppConfig._();

  /// Must be called before any config value is read — typically in main()
  /// before runApp().
  static Future<void> load() async {
    await dotenv.load(fileName: '.env');
  }

  static String get apiBaseUrl {
    // On web, prefer the browser's origin so the phone over LAN resolves the
    // backend on the same host. We assume the API runs on port 8000 of the
    // machine serving the web app.
    if (kIsWeb) {
      final o = origin.currentOrigin();
      if (o != null && o.isNotEmpty) {
        // Replace whatever port the web app is on with 8000 (the API).
        final uri = Uri.parse(o);
        return '${uri.scheme}://${uri.host}:8000';
      }
    }
    final url = dotenv.maybeGet('API_BASE_URL') ?? 'http://localhost:8000';
    return url.endsWith('/') ? url.substring(0, url.length - 1) : url;
  }

  /// The origin the web app itself is served from (for building join URLs in
  /// QR codes). On web this is the browser location; elsewhere null.
  static String? get webOrigin => origin.currentOrigin();
}
