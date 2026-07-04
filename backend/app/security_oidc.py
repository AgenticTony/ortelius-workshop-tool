"""Optional OIDC bearer-token verification (Entra ID / Azure AD).

When ``OIDC_ISSUER`` + ``OIDC_JWKS_URL`` (+ optional ``OIDC_AUDIENCE``) are set,
a caller may present a JWT access token issued by the IdP instead of an opaque
facilitator/participant token. We verify the signature against the IdP's public
JWKS (no client secret needed to *verify* — only to mint), check issuer /
audience / expiry, and map the caller to a facilitator [Principal] — i.e. an
enterprise-SSO admin login.

This is the security-critical seam. Mapping an IdP identity (the ``sub`` claim)
to a workshop *participant* is a product-integration step (a per-session
``oidc_sub`` column + claim mapping at join) intentionally left to the deploy;
the opaque participant-token path remains the default.

Disabled entirely (no-op) unless the env vars are set, so dev/test are
unaffected. Entra ID's well-known endpoints:

    OIDC_ISSUER=https://login.microsoftonline.com/<tenant-id>/v2.0
    OIDC_JWKS_URL=https://login.microsoftonline.com/<tenant-id>/discovery/v2.0/keys
    OIDC_AUDIENCE=<app-client-id>
"""
from __future__ import annotations

import logging
import os
from functools import lru_cache
from typing import Any

import jwt

logger = logging.getLogger(__name__)


def oidc_enabled() -> bool:
    return bool(os.getenv("OIDC_JWKS_URL") and os.getenv("OIDC_ISSUER"))


@lru_cache(maxsize=1)
def _jwks_client() -> "jwt.PyJWKClient":
    # Cached + key-cached so we don't fetch JWKS per request.
    return jwt.PyJWKClient(os.environ["OIDC_JWKS_URL"], cache_keys=True, lifespan=3600)


def looks_like_jwt(token: str) -> bool:
    """Cheap structural check: a JWT has three dot-separated base64 segments."""
    return token.count(".") == 2


def verify_oidc_token(token: str) -> dict[str, Any] | None:
    """Verify an OIDC JWT; return its claims on success, None on any failure.

    Returns None (not raises) so the caller can fall back to other auth schemes.
    """
    if not oidc_enabled() or not looks_like_jwt(token):
        return None
    try:
        signing_key = _jwks_client().get_signing_key_from_jwt(token)
        audience = os.getenv("OIDC_AUDIENCE") or None
        claims: dict[str, Any] = jwt.decode(
            token,
            signing_key.key,
            algorithms=["RS256"],
            issuer=os.environ["OIDC_ISSUER"],
            audience=audience,
            options={"verify_aud": audience is not None},
            leeway=30,
        )
        return claims
    except Exception:  # noqa: BLE001 - any JWT error means "not a valid IdP token"
        logger.warning("OIDC token verification failed", exc_info=True)
        return None
