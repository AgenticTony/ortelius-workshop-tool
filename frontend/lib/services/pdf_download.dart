import 'dart:js_interop';

import 'package:flutter/foundation.dart';
import 'package:web/web.dart' as web;

/// Saves PDF bytes under [filename]. On the web it triggers a browser
/// download via a blob + anchor element; elsewhere (mobile/desktop) it's a
/// no-op stub for now (a future milestone can wire share_plus or file saving).
///
/// Returns true if the bytes were delivered to the user (web), false if the
/// platform isn't supported for direct save (caller may then just show the
/// byte count / offer an alternative).
bool savePdf(Uint8List bytes, String filename) {
  if (!kIsWeb) {
    // Mobile/desktop save is out of scope for this milestone; the bytes are
    // still held by the controller and could be handed to share_plus later.
    return false;
  }
  // Build a blob from the bytes and trigger an anchor download.
  final blob = web.Blob(
    [bytes.toJS].toJS,
    web.BlobPropertyBag(type: 'application/pdf'),
  );
  final url = web.URL.createObjectURL(blob);
  final anchor = web.document.createElement('a') as web.HTMLAnchorElement;
  anchor.href = url;
  anchor.download = filename;
  anchor.style.display = 'none';
  web.document.body?.appendChild(anchor);
  anchor.click();
  anchor.remove();
  web.URL.revokeObjectURL(url);
  return true;
}
