"""Tests for the optional Entra ID / OIDC SSO seam."""
import pytest

from app.dependencies import get_db, resolve_principal
from app.errors import AuthenticationError
from app.security_oidc import looks_like_jwt, oidc_enabled, verify_oidc_token


def test_oidc_disabled_by_default(monkeypatch):
    monkeypatch.delenv("OIDC_JWKS_URL", raising=False)
    monkeypatch.delenv("OIDC_ISSUER", raising=False)
    assert not oidc_enabled()
    assert verify_oidc_token("opaque-token") is None
    assert verify_oidc_token("a.b.c") is None  # JWT-shaped, but OIDC is off


def test_looks_like_jwt():
    assert looks_like_jwt("header.payload.sig")
    assert not looks_like_jwt("opaque-token")
    assert not looks_like_jwt("two.parts")


def test_resolve_principal_accepts_verified_oidc_jwt(client, sample_session, monkeypatch):
    """A JWT that verify_oidc_token accepts maps to a facilitator Principal."""
    monkeypatch.setattr(
        "app.dependencies.verify_oidc_token", lambda _token: {"sub": "entra-user-123"}
    )
    db = next(client.app.dependency_overrides[get_db]())
    try:
        principal = resolve_principal(sample_session["id"], "header.payload.sig", db)
        assert principal.role == "facilitator"
        assert principal.oidc_sub == "entra-user-123"
    finally:
        db.close()


def test_jwt_shaped_token_rejected_when_oidc_off(client, sample_session, monkeypatch):
    """A JWT-shaped token must not bypass auth when OIDC is disabled.

    It's neither a valid opaque facilitator/participant token nor a verifiable
    IdP JWT → AuthenticationError. (Security guard against "looks like a JWT"
    accidentally trusting an attacker-supplied string.)
    """
    monkeypatch.delenv("OIDC_JWKS_URL", raising=False)
    monkeypatch.delenv("OIDC_ISSUER", raising=False)
    db = next(client.app.dependency_overrides[get_db]())
    try:
        with pytest.raises(AuthenticationError):
            resolve_principal(sample_session["id"], "header.payload.sig", db)
    finally:
        db.close()
