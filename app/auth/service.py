from __future__ import annotations

import os
from datetime import datetime, timedelta

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.auth import repository
from app.auth.email import email_delivery_enabled, send_email
from app.auth.models import AuthProvider, TokenType
from app.auth.oauth import exchange_github_code, exchange_google_code
from app.auth.jwt import (
    REFRESH_TOKEN_EXPIRE_DAYS,
    create_access_token,
    create_refresh_token,
    decode_token,
)
from app.auth.schemas import (
    ForgotPasswordRequest,
    LoginRequest,
    RefreshRequest,
    RegisterRequest,
    ResetPasswordRequest,
    TokenResponse,
    UserResponse,
    VerifyEmailRequest,
    SummaryHistoryResponse,
    SummaryHistoryItem
)
from app.auth.security import hash_password, hash_token, verify_password
from app.auth.token_utils import generate_secure_token
def _env_int(name: str, default: int) -> int:
    value = os.getenv(name)

    if value is None or not value.strip():
        return default

    return int(value)


VERIFY_EMAIL_TOKEN_EXPIRE_HOURS = _env_int("VERIFY_EMAIL_TOKEN_EXPIRE_HOURS", 24)
RESET_PASSWORD_TOKEN_EXPIRE_MINUTES = _env_int("RESET_PASSWORD_TOKEN_EXPIRE_MINUTES", 30)


def _user_response(user) -> UserResponse:
    return UserResponse.model_validate(user)


def _token_response(
    user,
    access_token: str,
    refresh_token: str,
    verification_token: str | None = None,
) -> TokenResponse:
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user=_user_response(user),
        verification_token=verification_token,
    )


def _issue_refresh_token(db: Session, user_id: str) -> str:
    refresh_token, jti = create_refresh_token(user_id)

    repository.save_refresh_token(
        db,
        user_id=user_id,
        jti=jti,
        token_hash=None,
        token_type=TokenType.REFRESH,
        expires_at=datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS),
        revoked=False,
        used=False,
    )

    return refresh_token


def _send_verification_email(user_email: str, verification_token: str) -> bool:
    frontend_url = os.getenv(
        "FRONTEND_URL",
        "http://localhost:5173",
    )

    verification_url = (
        f"{frontend_url}/verify-email"
        f"?token={verification_token}"
    )

    subject = "Verify your ClipMind account"

    body = (
        "Welcome to ClipMind!\n\n"
        "Please verify your email address by clicking the link below:\n\n"
        f"{verification_url}\n\n"
        "If you did not create a ClipMind account, ignore this email."
    )

    return send_email(user_email, subject, body)

def _send_reset_email(user_email: str, reset_token: str) -> bool:
    frontend_url = os.getenv("FRONTEND_URL", "http://localhost:5173")
    reset_link = f"{frontend_url}/reset-password?token={reset_token}"
    subject = "ClipMind password reset"
    body = (
    "Hi,\n\n"
    "We received a request to reset your ClipMind password.\n\n"
    "Click the link below to choose a new password:\n\n"
    f"{reset_link}\n\n"
    "If you didn't request a password reset, you can safely ignore this email.\n\n"
    f"This link expires in {RESET_PASSWORD_TOKEN_EXPIRE_MINUTES} minutes.\n\n"
    "— ClipMind Team"
)
    return send_email(user_email, subject, body)


def _clean_username(value: str) -> str:
    cleaned = "".join(character.lower() if character.isalnum() else "-" for character in value)
    cleaned = "-".join(part for part in cleaned.split("-") if part)
    return cleaned[:50] or "user"


def _ensure_unique_username(db: Session, base_username: str) -> str:
    candidate = _clean_username(base_username)
    if len(candidate) < 3:
        candidate = f"{candidate}-user"[:50]

    suffix = 0
    unique_candidate = candidate

    while repository.get_user_by_username(db, unique_candidate) is not None:
        suffix += 1
        suffix_text = f"-{suffix}"
        unique_candidate = f"{candidate[:50 - len(suffix_text)]}{suffix_text}"

    return unique_candidate[:50]


def _upsert_oauth_user(
    db: Session,
    provider: AuthProvider,
    email: str,
    provider_id: str,
    username: str,
    avatar_url: str | None,
    is_verified: bool,
) -> object:
    existing_user = repository.get_user_by_provider(db, provider.value, provider_id)

    if existing_user is None:
        existing_user = repository.get_user_by_email(db, email)

    unique_username = _ensure_unique_username(db, username or email.split("@")[0])

    if existing_user is None:
        return repository.create_user(
            db,
            email=email,
            username=unique_username,
            password_hash=None,
            provider=provider,
            provider_id=provider_id,
            avatar_url=avatar_url,
            is_verified=is_verified,
        )

    updates = {
        "provider_id": provider_id,
        "avatar_url": avatar_url or existing_user.avatar_url,
        "is_verified": True,
    }

    if not existing_user.username or existing_user.username.startswith("user-"):
        updates["username"] = unique_username

    return repository.update_user(db, existing_user, **updates)


def oauth_authorization_url(provider: str) -> tuple[str, str]:
    
    from app.auth.oauth import build_authorization_url

    return build_authorization_url(provider)


def oauth_callback(
    db: Session,
    provider: str,
    code: str,
    state: str,
) -> TokenResponse:
    from app.auth.oauth import decode_oauth_state

    decode_oauth_state(state, provider)

    provider_name = provider.lower()

    if provider_name == "google":
        profile = exchange_google_code(code)
        oauth_provider = AuthProvider.GOOGLE
    elif provider_name == "github":
        profile = exchange_github_code(code)
        oauth_provider = AuthProvider.GITHUB
    else:
        raise HTTPException(status_code=404, detail="Unsupported OAuth provider.")

    user = _upsert_oauth_user(
        db,
        provider=oauth_provider,
        email=profile["email"],
        provider_id=profile["provider_id"],
        username=profile["username"],
        avatar_url=profile.get("avatar_url"),
        is_verified=profile.get("is_verified", True),
    )

    access_token = create_access_token(user.id)
    refresh_token = _issue_refresh_token(db, user.id)

    return _token_response(user, access_token, refresh_token)


def register(
    db: Session,
    req: RegisterRequest,
) -> TokenResponse:
    if repository.get_user_by_email(db, req.email):
        raise HTTPException(status_code=400, detail="Email already registered.")

    if repository.get_user_by_username(db, req.username):
        raise HTTPException(status_code=400, detail="Username already taken.")

    user = repository.create_user(
        db,
        email=req.email,
        username=req.username,
        password_hash=hash_password(req.password),
        provider=AuthProvider.LOCAL,
        provider_id=None,
        avatar_url=None,
        is_verified=False,
    )

    verification_token = generate_secure_token()

    repository.save_refresh_token(
        db,
        user_id=user.id,
        jti=None,
        token_hash=hash_token(verification_token),
        token_type=TokenType.VERIFY_EMAIL,
        expires_at=datetime.utcnow() + timedelta(hours=VERIFY_EMAIL_TOKEN_EXPIRE_HOURS),
        revoked=False,
        used=False,
    )

    email_sent = _send_verification_email(user.email, verification_token)

    access_token = create_access_token(user.id)
    refresh_token = _issue_refresh_token(db, user.id)

    return _token_response(
        user,
        access_token,
        refresh_token,
        verification_token=None if email_sent else verification_token,
    )


def login(
    db: Session,
    req: LoginRequest,
) -> TokenResponse:
    user = repository.get_user_by_email(db, req.email)

    if user is None:
        raise HTTPException(status_code=401, detail="Invalid email or password.")

    if user.provider != AuthProvider.LOCAL:
        raise HTTPException(
            status_code=400,
            detail=f"This account uses {user.provider.value.lower()} sign in.",
        )

    if not user.password_hash or not verify_password(req.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password.")

    access_token = create_access_token(user.id)
    refresh_token = _issue_refresh_token(db, user.id)

    return _token_response(user, access_token, refresh_token)


def refresh(
    db: Session,
    refresh_token: str,
) -> TokenResponse:
    try:
        payload = decode_token(refresh_token)
    except Exception as exc:
        raise HTTPException(status_code=401, detail="Invalid refresh token.") from exc

    if payload.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="Invalid token type.")

    jti = payload.get("jti")

    if not jti:
        raise HTTPException(status_code=401, detail="Refresh token missing JTI.")

    token = repository.get_refresh_token_by_jti(db, jti)

    if not repository.is_refresh_token_valid(token):
        raise HTTPException(status_code=401, detail="Refresh token is no longer valid.")

    user = token.user

    new_access_token = create_access_token(user.id)
    new_refresh_token = _issue_refresh_token(db, user.id)

    repository.revoke_refresh_token(db, token)

    return _token_response(user, new_access_token, new_refresh_token)


def logout(
    db: Session,
    refresh_token: str,
) -> dict:
    try:
        payload = decode_token(refresh_token)
    except Exception as exc:
        raise HTTPException(status_code=401, detail="Invalid refresh token.") from exc

    if payload.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="Invalid token type.")

    jti = payload.get("jti")

    if not jti:
        raise HTTPException(status_code=401, detail="Refresh token missing JTI.")

    token = repository.get_refresh_token_by_jti(db, jti)

    if token is None:
        raise HTTPException(status_code=404, detail="Refresh token not found.")

    repository.revoke_refresh_token(db, token)

    return {"message": "Logged out successfully."}


def logout_all(
    db: Session,
    user,
) -> dict:
    repository.revoke_all_refresh_tokens(db, user.id)

    return {"message": "Logged out from all devices."}


def forgot_password(
    db: Session,
    req: ForgotPasswordRequest,
) -> dict:
    user = repository.get_user_by_email(db, req.email)

    if user is None:
        return {
            "message": (
                "If an account with that email exists, a password reset link has been sent."
            )
        }

    raw_token = generate_secure_token()

    repository.save_refresh_token(
        db,
        user_id=user.id,
        jti=None,
        token_hash=hash_token(raw_token),
        token_type=TokenType.RESET_PASSWORD,
        expires_at=datetime.utcnow() + timedelta(minutes=RESET_PASSWORD_TOKEN_EXPIRE_MINUTES),
        revoked=False,
        used=False,
    )

    email_sent = _send_reset_email(user.email, raw_token)

    response = {
        "message": (
            "If an account with that email exists, a password reset link has been sent."
        )
    }

    if not email_sent:
        response["reset_token"] = raw_token

    return response


def verify_email(
    db: Session,
    req: VerifyEmailRequest,
) -> dict:
    token_hash = hash_token(req.token)

    auth_token = repository.get_token_by_hash(
        db,
        token_hash,
        TokenType.VERIFY_EMAIL,
    )

    if auth_token is None:
        raise HTTPException(status_code=400, detail="Invalid verification token.")

    if auth_token.used:
        return {"message": "Email already verified."}

    if auth_token.revoked:
        raise HTTPException(status_code=400, detail="Verification token has been revoked.")

    if auth_token.expires_at < datetime.utcnow():
        raise HTTPException(status_code=400, detail="Verification token has expired.")

    if auth_token.user.is_verified:
        repository.mark_token_used(db, auth_token)
        return {"message": "Email already verified."}

    repository.update_user(db, auth_token.user, is_verified=True)
    repository.mark_token_used(db, auth_token)

    return {"message": "Email verified successfully."}


def reset_password(
    db: Session,
    req: ResetPasswordRequest,
) -> dict:
    token_hash = hash_token(req.token)

    auth_token = repository.get_token_by_hash(
        db,
        token_hash,
        TokenType.RESET_PASSWORD,
    )

    if auth_token is None:
        raise HTTPException(status_code=400, detail="Invalid reset token.")

    if auth_token.used:
        raise HTTPException(status_code=400, detail="Reset token has already been used.")

    if auth_token.revoked:
        raise HTTPException(status_code=400, detail="Reset token has been revoked.")

    if auth_token.expires_at < datetime.utcnow():
        raise HTTPException(status_code=400, detail="Reset token has expired.")

    repository.update_password(
        db,
        auth_token.user,
        hash_password(req.new_password),
    )

    repository.mark_token_used(db, auth_token)
    repository.revoke_all_refresh_tokens(db, auth_token.user.id)

    return {"message": "Password reset successful."}


def get_summary_history(
    db: Session,
    user,
) -> SummaryHistoryResponse:
    history = repository.get_summary_history(
        db=db,
        user_id=user.id,
    )

    return SummaryHistoryResponse(
        items=[
            SummaryHistoryItem(
                youtube_video_id=video.youtube_video_id,
                title=video.title,
                duration=video.duration,
                thumbnail_url=f"https://i.ytimg.com/vi/{video.youtube_video_id}/hqdefault.jpg",
                summarized_at=history_item.created_at,
            )
            for history_item, video in history
        ]
    )