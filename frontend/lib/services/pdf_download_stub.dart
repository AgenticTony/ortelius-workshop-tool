// Non-web stub. The real web implementation lives in pdf_download_web.dart
// and is conditionally imported only on web. This file is compiled on every
// non-web platform (iOS, macOS, Android) and returns false (not supported
// this milestone — could wire share_plus later).
import 'dart:typed_data';

bool savePdfWeb(Uint8List bytes, String filename) => false;
