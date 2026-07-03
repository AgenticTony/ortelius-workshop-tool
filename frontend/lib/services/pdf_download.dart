import 'package:flutter/foundation.dart';

// Conditional import: when dart:js_interop is available (web), use the real
// JS-interop implementation; otherwise use the non-web stub. Each platform
// file exposes the same savePdfWeb() function.
// ignore: uri_does_not_exist
import 'pdf_download_stub.dart'
    if (dart.library.js_interop) 'pdf_download_web.dart' as platform;

/// Saves PDF bytes under [filename]. On the web it triggers a browser
/// download via a blob + anchor element; on iOS/macOS/Android it's a no-op
/// (returns false — could wire share_plus later).
///
/// Returns true if the bytes were delivered to the user (web), false
/// otherwise (caller may then just show the byte count).
bool savePdf(Uint8List bytes, String filename) {
  if (!kIsWeb) return false;
  return platform.savePdfWeb(bytes, filename);
}
