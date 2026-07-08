"""Typed exception classes for the Workshop Tool API.

Each carries an HTTP status, a stable machine-readable `code`, and a
human-readable `detail`. The global handlers in main.py turn these into the
consistent ``{"detail": ..., "code": ...}`` response shape (with a
request_id on the unexpected-error fallback).

Raising a typed error instead of a bare HTTPException keeps the failure
mode named and discoverable, and lets the Claude/analytics layer surface
specific failures (outage vs. parse error vs. not-found) distinctly.
"""
from __future__ import annotations


class WorkshopError(Exception):
    """Base for all typed workshop errors. Carries status + code + detail."""

    status_code: int = 500
    code: str = "workshop_error"

    def __init__(self, detail: str, *, status_code: int | None = None, code: str | None = None):
        super().__init__(detail)
        self.detail = detail
        if status_code is not None:
            self.status_code = status_code
        if code is not None:
            self.code = code


# ── Not-found errors (404) ────────────────────────────────────


class SessionNotFoundError(WorkshopError):
    status_code = 404
    code = "session_not_found"

    def __init__(self, session_id: str | None = None):
        super().__init__("Session not found")
        self.session_id = session_id


class IdeaNotFoundError(WorkshopError):
    status_code = 404
    code = "idea_not_found"

    def __init__(self, idea_id: str | None = None):
        super().__init__("Idea not found")
        self.idea_id = idea_id


class AnalysisNotFoundError(WorkshopError):
    status_code = 404
    code = "analysis_not_found"

    def __init__(self, detail: str = "No analysis found — run POST /analyse first"):
        super().__init__(detail)


class InvalidAccessCodeError(WorkshopError):
    status_code = 404
    code = "invalid_access_code"

    def __init__(self) -> None:
        super().__init__("Invalid access code")


# ── Auth errors (401) ─────────────────────────────────────────


class AuthenticationError(WorkshopError):
    """Facilitator token missing or invalid. Includes WWW-Authenticate."""

    status_code = 401
    code = "unauthorized"

    def __init__(self, detail: str = "Authentication required"):
        super().__init__(detail)


# ── Validation errors (422) ───────────────────────────────────


class FrameworkNotFoundError(WorkshopError):
    status_code = 422
    code = "framework_not_found"

    def __init__(self, framework_id: str | None = None):
        detail = (
            f"Unknown framework '{framework_id}'."
            if framework_id
            else "Unknown framework."
        )
        super().__init__(detail)


class InvalidFrameworkError(WorkshopError):
    """A custom framework is malformed (e.g. too few categories)."""

    status_code = 422
    code = "invalid_framework"

    def __init__(self, detail: str):
        super().__init__(detail)


# ── Upstream / dependency errors ──────────────────────────────


class ClaudeAPIError(WorkshopError):
    """The Anthropic API call failed (outage, rate limit, auth, network).

    Wraps the upstream exception so it surfaces as a clean 503 with a stable
    code rather than an opaque 500.
    """

    status_code = 503
    code = "claude_error"

    def __init__(self, detail: str = "The AI analysis service is unavailable. Please try again."):
        super().__init__(detail)


class ClaudeParseError(WorkshopError):
    """Claude returned a response we couldn't parse as JSON, even after retry."""

    status_code = 502
    code = "claude_parse_error"

    def __init__(self) -> None:
        super().__init__(
            "The AI returned an unparseable response. Please try re-running the analysis."
        )


class AccessCodeCollisionError(WorkshopError):
    """Couldn't generate a unique access code after several attempts.

    This should be effectively impossible (36^6 space); if it fires, it's a
    signal something is wrong. 500 + loud log.
    """

    status_code = 500
    code = "access_code_collision"

    def __init__(self) -> None:
        super().__init__("Could not generate a unique access code. Please retry.")


# ── Conflict / forbidden (409, 403) ────────────────────────────


class VoteBudgetExceededError(WorkshopError):
    """Participant has spent their full dot-voting budget for the session."""

    status_code = 409
    code = "vote_budget_exceeded"

    def __init__(self, detail: str = "You've used all your votes for this session."):
        super().__init__(detail)


class AlreadyVotedError(WorkshopError):
    """Participant already voted on this idea (dot-voting = one per idea)."""

    status_code = 409
    code = "already_voted"

    def __init__(self) -> None:
        super().__init__("You've already voted on this idea.")


class NotVotedError(WorkshopError):
    """Participant tried to remove a vote they never cast."""

    status_code = 404
    code = "not_voted"

    def __init__(self) -> None:
        super().__init__("You haven't voted on this idea.")


class ForbiddenError(WorkshopError):
    """The authenticated caller isn't permitted to perform this action."""

    status_code = 403
    code = "forbidden"

    def __init__(self, detail: str = "You don't have permission to do that."):
        super().__init__(detail)
