from __future__ import annotations

import os
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any
from urllib.parse import urlencode

import requests
from fastapi import HTTPException
from jose import JWTError, jwt

from app.auth.jwt import JWT_ALGORITHM, JWT_SECRET_KEY


OAUTH_STATE_EXPIRE_MINUTES = int(os.getenv("OAUTH_STATE_EXPIRE_MINUTES", "10") or "10")

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
GOOGLE_REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI")

GITHUB_CLIENT_ID = os.getenv("GITHUB_CLIENT_ID")
GITHUB_CLIENT_SECRET = os.getenv("GITHUB_CLIENT_SECRET")
GITHUB_REDIRECT_URI = os.getenv("GITHUB_REDIRECT_URI")

GOOGLE_AUTH_URL = os.getenv(
    "GOOGLE_AUTH_URL",
    "https://accounts.google.com/o/oauth2/v2/auth",
)
GOOGLE_TOKEN_URL = os.getenv(
    "GOOGLE_TOKEN_URL",
    "https://oauth2.googleapis.com/token",
)
GOOGLE_USERINFO_URL = os.getenv(
    "GOOGLE_USERINFO_URL",
    "https://openidconnect.googleapis.com/v1/userinfo",
)

GITHUB_AUTH_URL = os.getenv(
    "GITHUB_AUTH_URL",
    "https://github.com/login/oauth/authorize",
)
GITHUB_TOKEN_URL = os.getenv(
    "GITHUB_TOKEN_URL",
    "https://github.com/login/oauth/access_token",
)
GITHUB_USER_URL = os.getenv(
    "GITHUB_USER_URL",
    "https://api.github.com/user",
)
GITHUB_EMAILS_URL = os.getenv(
    "GITHUB_EMAILS_URL",
    "https://api.github.com/user/emails",
)


def _provider_config(provider: str) -> dict[str, str]:
    provider = provider.lower()

    if provider == "google":
        if not GOOGLE_CLIENT_ID or not GOOGLE_CLIENT_SECRET or not GOOGLE_REDIRECT_URI:
            raise HTTPException(
                status_code=500,
                detail="Google OAuth is not configured.",
            )

        return {
            "client_id": GOOGLE_CLIENT_ID,
            "client_secret": GOOGLE_CLIENT_SECRET,
            "redirect_uri": GOOGLE_REDIRECT_URI,
            "auth_url": GOOGLE_AUTH_URL,
            "token_url": GOOGLE_TOKEN_URL,
        }

    if provider == "github":
        if not GITHUB_CLIENT_ID or not GITHUB_CLIENT_SECRET or not GITHUB_REDIRECT_URI:
            raise HTTPException(
                status_code=500,
                detail="GitHub OAuth is not configured.",
            )

        return {
            "client_id": GITHUB_CLIENT_ID,
            "client_secret": GITHUB_CLIENT_SECRET,
            "redirect_uri": GITHUB_REDIRECT_URI,
            "auth_url": GITHUB_AUTH_URL,
            "token_url": GITHUB_TOKEN_URL,
        }

    raise HTTPException(status_code=404, detail="Unsupported OAuth provider.")


def build_authorization_url(provider: str) -> tuple[str, str]:
    config = _provider_config(provider)
    state = create_oauth_state(provider)

    provider = provider.lower()
    params: dict[str, Any] = {
        "client_id": config["client_id"],
        "redirect_uri": config["redirect_uri"],
        "state": state,
    }

    if provider == "google":
        params.update(
            {
                "response_type": "code",
                "scope": "openid email profile",
                "access_type": "offline",
                "prompt": "consent",
            }
        )
    else:
        params.update(
            {
                "response_type": "code",
                "scope": "read:user user:email",
            }
        )

    return f"{config['auth_url']}?{urlencode(params)}", state


def create_oauth_state(provider: str) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "type": "oauth_state",
        "provider": provider.lower(),
        "nonce": secrets.token_urlsafe(16),
        "iat": now,
        "exp": now + timedelta(minutes=OAUTH_STATE_EXPIRE_MINUTES),
    }

    return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)


def decode_oauth_state(state: str, provider: str) -> dict[str, Any]:
    try:
        payload = jwt.decode(state, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
    except JWTError as exc:
        raise HTTPException(status_code=401, detail="Invalid OAuth state.") from exc

    if payload.get("type") != "oauth_state" or payload.get("provider") != provider.lower():
        raise HTTPException(status_code=401, detail="Invalid OAuth state.")

    return payload


def exchange_google_code(code: str) -> dict[str, Any]:
    config = _provider_config("google")

    response = requests.post(
        config["token_url"],
        data={
            "code": code,
            "client_id": config["client_id"],
            "client_secret": config["client_secret"],
            "redirect_uri": config["redirect_uri"],
            "grant_type": "authorization_code",
        },
        timeout=30,
    )

    if not response.ok:
        raise HTTPException(status_code=400, detail="Google token exchange failed.")

    token_data = response.json()
    access_token = token_data.get("access_token")

    if not access_token:
        raise HTTPException(status_code=400, detail="Google access token missing.")

    profile_response = requests.get(
        GOOGLE_USERINFO_URL,
        headers={"Authorization": f"Bearer {access_token}"},
        timeout=30,
    )

    if not profile_response.ok:
        raise HTTPException(status_code=400, detail="Google profile lookup failed.")

    profile = profile_response.json()

    email = profile.get("email")
    provider_id = profile.get("sub")

    if not email or not provider_id:
        raise HTTPException(status_code=400, detail="Google account is missing email or ID.")

    return {
        "email": email,
        "provider_id": provider_id,
        "username": profile.get("name") or email.split("@")[0],
        "avatar_url": profile.get("picture"),
        "is_verified": bool(profile.get("email_verified", True)),
    }


def exchange_github_code(code: str) -> dict[str, Any]:
    config = _provider_config("github")

    token_response = requests.post(
        config["token_url"],
        data={
            "code": code,
            "client_id": config["client_id"],
            "client_secret": config["client_secret"],
            "redirect_uri": config["redirect_uri"],
        },
        headers={"Accept": "application/json"},
        timeout=30,
    )

    if not token_response.ok:
        raise HTTPException(status_code=400, detail="GitHub token exchange failed.")

    token_data = token_response.json()
    access_token = token_data.get("access_token")

    if not access_token:
        raise HTTPException(status_code=400, detail="GitHub access token missing.")

    profile_response = requests.get(
        GITHUB_USER_URL,
        headers={
            "Authorization": f"Bearer {access_token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        },
        timeout=30,
    )

    if not profile_response.ok:
        raise HTTPException(status_code=400, detail="GitHub profile lookup failed.")

    profile = profile_response.json()

    emails_response = requests.get(
        GITHUB_EMAILS_URL,
        headers={
            "Authorization": f"Bearer {access_token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        },
        timeout=30,
    )

    if not emails_response.ok:
        raise HTTPException(status_code=400, detail="GitHub email lookup failed.")

    primary_email = None
    for email_entry in emails_response.json():
        if email_entry.get("primary") and email_entry.get("verified"):
            primary_email = email_entry.get("email")
            break

    if primary_email is None:
        for email_entry in emails_response.json():
            if email_entry.get("verified"):
                primary_email = email_entry.get("email")
                break

    if primary_email is None:
        primary_email = profile.get("email")

    provider_id = str(profile.get("id") or "")

    if not primary_email or not provider_id:
        raise HTTPException(status_code=400, detail="GitHub account is missing email or ID.")

    display_name = profile.get("name") or profile.get("login") or primary_email.split("@")[0]

    return {
        "email": primary_email,
        "provider_id": provider_id,
        "username": display_name,
        "avatar_url": profile.get("avatar_url"),
        "is_verified": True,
    }