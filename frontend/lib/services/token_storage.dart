import 'package:flutter_secure_storage/flutter_secure_storage.dart';

/// Persists the facilitator token per session, securely.
///
/// The facilitator token is issued once at session creation and never
/// re-served; we key it by session id so a facilitator can hold tokens for
/// multiple sessions. On web, flutter_secure_storage falls back to
/// encrypted local storage; on mobile it uses the platform keystore/keychain.
class TokenStorage {
  TokenStorage({FlutterSecureStorage? storage})
      : _storage = storage ?? const FlutterSecureStorage();

  final FlutterSecureStorage _storage;

  // Android keystore doesn't tolerate long keys; keep it short and stable.
  static const _keyPrefix = 'fac_token_';

  Future<void> save(String sessionId, String token) async {
    await _storage.write(key: '$_keyPrefix$sessionId', value: token);
  }

  Future<String?> read(String sessionId) async {
    return _storage.read(key: '$_keyPrefix$sessionId');
  }

  Future<void> delete(String sessionId) async {
    await _storage.delete(key: '$_keyPrefix$sessionId');
  }
}
