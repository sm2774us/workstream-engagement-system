"""Azure Entra ID (OAuth 2.0 / OIDC / JWT) authentication dependency.

Validates bearer tokens issued by Entra ID against the tenant's JWKS
endpoint. In production the JWKS document is fetched once and cached
with a TTL; here we model the same interface so the dependency can be
swapped from `MockJWKSClient` to `EntraJWKSClient` with zero call-site
changes (an interview-friendly seam for discussing testability).
"""
from __future__ import annotations

import time
from typing import Any, Protocol

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt

from app.core.config import Settings, get_settings

bearer_scheme = HTTPBearer(auto_error=True)


class JWKSClient(Protocol):
    """Resolves the signing key set used to verify Entra ID tokens."""

    def get_signing_key(self, kid: str) -> dict[str, Any]:
        ...


class MockJWKSClient:
    """Deterministic JWKS stand-in used for local dev and tests.

    A real deployment replaces this with a client that fetches
    `{authority}/{tenant}/discovery/v2.0/keys` and caches results,
    honoring `Cache-Control` headers from Entra ID.
    """

    def __init__(self, keys: dict[str, dict[str, Any]] | None = None) -> None:
        self._keys = keys or {}

    def get_signing_key(self, kid: str) -> dict[str, Any]:
        if kid not in self._keys:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Unknown signing key id",
            )
        return self._keys[kid]


class Principal:
    """Authenticated caller identity extracted from a validated token."""

    def __init__(self, claims: dict[str, Any]) -> None:
        self.claims = claims
        self.subject: str = claims.get("sub", "")
        self.roles: list[str] = claims.get("roles", [])
        self.name: str = claims.get("name", claims.get("preferred_username", ""))
        self.issued_at: float = claims.get("iat", time.time())

    def has_role(self, role: str) -> bool:
        """Return True if the Entra ID app role is present on the token."""
        return role in self.roles


def _decode_dev_token(token: str, settings: Settings) -> dict[str, Any]:
    """Decode a locally-signed HS256 token for dev/demo mode.

    Production tokens are RS256, signed by Entra ID and verified against
    the tenant JWKS (see `EntraJWKSClient` in README for the full seam).
    Dev mode uses a shared secret so the showcase runs with zero Azure
    dependencies.
    """
    try:
        return jwt.decode(
            token,
            key="dev-shared-secret-do-not-use-in-prod",
            algorithms=["HS256"],
            audience=settings.jwt_audience,
            options={"verify_aud": True},
        )
    except JWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token: {exc}",
        ) from exc


async def get_current_principal(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    settings: Settings = Depends(get_settings),
) -> Principal:
    """FastAPI dependency: validate the Entra ID bearer token.

    Args:
        credentials: The `Authorization: Bearer <token>` header contents.
        settings: Cached application settings.

    Returns:
        The authenticated `Principal` for the request.

    Raises:
        HTTPException: 401 if the token is missing, expired, or invalid.
    """
    claims = _decode_dev_token(credentials.credentials, settings)
    return Principal(claims)


def require_role(role: str):
    """Return a FastAPI dependency enforcing an Entra ID app role claim."""

    async def _dependency(principal: Principal = Depends(get_current_principal)) -> Principal:
        if not principal.has_role(role):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Missing required role: {role}",
            )
        return principal

    return _dependency
