"""Facilitator token generation and verification.

A facilitator token is an opaque bearer token issued once at session creation.
We store only its SHA-256 hash (never the plaintext) and verify incoming
tokens by comparing hashes. This is demo-grade auth — fine for gating
cost-incurring routes (analysis, report) in a workshop setting; full
facilitator accounts / SSO are a future/prod concern (see production-readiness.md).
"""

import hashlib
import secrets


def generate_token() -> str:
    """Generate an opaque bearer token (URL-safe, ~43 chars).

    Used for both facilitator and participant tokens — both are random,
    unstructured, verified by hash. Demo-grade auth; full SSO/IdP is a
    production concern (see production-readiness.md).
    """
    return secrets.token_urlsafe(32)


def generate_facilitator_token() -> str:
    """Generate a new opaque facilitator token (URL-safe, ~43 chars)."""
    return generate_token()


def generate_participant_token() -> str:
    """Generate a new opaque participant token (issued once at join)."""
    return generate_token()


def hash_token(token: str) -> str:
    """SHA-256 hex digest of a token. Store this, never the plaintext."""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def verify_token(token: str, stored_hash: str | None) -> bool:
    """Constant-ish comparison of a presented token against the stored hash.

    Returns False if no hash is stored (pre-token sessions) or on any mismatch.
    """
    if not stored_hash:
        return False
    return secrets.compare_digest(hash_token(token), stored_hash)
