import 'package:flutter_dotenv/flutter_dotenv.dart';

/// Reads environment configuration loaded from assets/.env via flutter_dotenv.
///
/// The backend base URL is the only value needed at this stage. Other config
/// (e.g. feature flags) can live here later.
class AppConfig {
  const AppConfig._();

  /// Must be called before any config value is read — typically in main()
  /// before runApp().
  static Future<void> load() async {
    await dotenv.load(fileName: '.env');
  }

  static String get apiBaseUrl {
    final url = dotenv.maybeGet('API_BASE_URL') ?? 'http://localhost:8000';
    // Strip a trailing slash so path joining is predictable.
    return url.endsWith('/') ? url.substring(0, url.length - 1) : url;
  }
}
