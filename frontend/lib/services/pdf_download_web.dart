// Web-only implementation of savePdf. This file is conditionally imported only
// when compiling for the web (see pdf_download.dart). It MUST NOT be compiled
// on non-web platforms because it imports dart:js_interop, which doesn't exist
// there.
import 'dart:js_interop';
import 'dart:typed_data';

import 'package:web/web.dart' as web;

bool savePdfWeb(Uint8List bytes, String filename) {
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
