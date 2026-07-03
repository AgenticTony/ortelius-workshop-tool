/// Data models for the Workshop Tool frontend.
///
/// These mirror the backend Pydantic models one-to-one. Field names and JSON
/// keys match the API contract (docs/api-contract.md). Datetimes are parsed
/// from the ISO-8601 strings the backend returns.
///
/// Kept as hand-written classes (not freezed) for this scaffold: fewer moving
/// parts, no build_runner step. Migrate to freezed in a later milestone if
/// copyWith/equality semantics become painful.
library;

export 'session.dart';
export 'idea.dart';
export 'participant.dart';
export 'analysis_result.dart';
export 'join_response.dart';
export 'sse_event.dart';
