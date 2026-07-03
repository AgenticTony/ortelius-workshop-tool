import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'api/workshop_api.dart';
import '../services/token_storage.dart';

/// Single shared API client. Override in tests with a fake Dio.
final workshopApiProvider = Provider<WorkshopApi>((ref) {
  return WorkshopApi();
});

/// Single shared token storage.
final tokenStorageProvider = Provider<TokenStorage>((ref) {
  return TokenStorage();
});
