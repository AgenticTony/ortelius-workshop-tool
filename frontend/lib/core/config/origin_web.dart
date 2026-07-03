// Web-only: returns the browser's current origin (e.g. http://192.168.50.254:7355).
// Used to derive the backend URL so the same web build works from any host
// (simulator, phone over LAN, etc.) without rebuilding. Only imported on web.
import 'package:web/web.dart' as web;

String? currentOrigin() => web.window.location.origin;
