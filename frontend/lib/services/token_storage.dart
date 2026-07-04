import 'package:flutter_secure_storage/flutter_secure_storage.dart';

/// Persists facilitator and participant bearer tokens per session, securely.
///
/// The facilitator token gates cost-incurring routes (analysis, report); the
/// participant token (issued once at join) gates submit/vote/SSE. We key each
/// by session id so a device can hold tokens for multiple sessions. On web,
/// flutter_secure_storage falls back to encrypted local storage; on mobile it
/// uses the platform keystore/keychain.
class TokenStorage {
  TokenStorage({FlutterSecureStorage? storage})
      : _storage = storage ?? const FlutterSecureStorage();

  final FlutterSecureStorage _storage;

  // Android keystore doesn't tolerate long keys; keep prefixes short and stable.
  static const _facPrefix = 'fac_token_';
  static const _parPrefix = 'par_token_';

  // ── Facilitator ─────────────────────────────────────────────
  Future<void> saveFacilitator(String sessionId, String token) async {
    await _storage.write(key: '$_facPrefix$sessionId', value: token);
  }

  Future<String?> readFacilitator(String sessionId) async {
    return _storage.read(key: '$_facPrefix$sessionId');
  }

  // ── Participant ─────────────────────────────────────────────
  Future<void> saveParticipant(String sessionId, String token) async {
    await _storage.write(key: '$_parPrefix$sessionId', value: token);
  }

  Future<String?> readParticipant(String sessionId) async {
    return _storage.read(key: '$_parPrefix$sessionId');
  }

  /// Best-available read token for a session: participant first (the common
  /// case for live updates), then facilitator.
  Future<String?> readAny(String sessionId) async {
    return await readParticipant(sessionId) ?? await readFacilitator(sessionId);
  }

  Future<void> delete(String sessionId) async {
    await _storage.delete(key: '$_facPrefix$sessionId');
    await _storage.delete(key: '$_parPrefix$sessionId');
  }
}
