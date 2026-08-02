from datetime import datetime

from sqlalchemy.orm import Session

from app.auth.models import (
    AuthToken,
    TokenType,
    User,
    UserVideoHistory,
    Video,
)


# ==========================================================
# Users
# ==========================================================

def get_user_by_email(
    db: Session,
    email: str,
) -> User | None:
    return (
        db.query(User)
        .filter(User.email == email)
        .first()
    )


def get_user_by_username(
    db: Session,
    username: str,
) -> User | None:
    return (
        db.query(User)
        .filter(User.username == username)
        .first()
    )


def get_user_by_provider(
    db: Session,
    provider: str,
    provider_id: str,
) -> User | None:
    return (
        db.query(User)
        .filter(
            User.provider == provider,
            User.provider_id == provider_id,
        )
        .first()
    )


def create_user(
    db: Session,
    **kwargs,
) -> User:
    user = User(**kwargs)

    db.add(user)
    db.commit()
    db.refresh(user)

    return user


def update_video(
    db: Session,
    video: Video,
    **kwargs,
) -> Video:
    for key, value in kwargs.items():
        setattr(video, key, value)

    db.commit()
    db.refresh(video)

    return video


def update_user(
    db: Session,
    user: User,
    **kwargs,
) -> User:
    for key, value in kwargs.items():
        setattr(user, key, value)

    db.commit()
    db.refresh(user)

    return user


# ==========================================================
# Auth Tokens
# ==========================================================

def save_refresh_token(
    db: Session,
    **kwargs,
) -> AuthToken:
    token = AuthToken(**kwargs)

    db.add(token)
    db.commit()
    db.refresh(token)

    return token


def get_refresh_token_by_jti(
    db: Session,
    jti: str,
) -> AuthToken | None:
    return (
        db.query(AuthToken)
        .filter(
            AuthToken.jti == jti,
            AuthToken.token_type == TokenType.REFRESH,
        )
        .first()
    )


def is_refresh_token_valid(
    token: AuthToken | None,
) -> bool:
    if token is None:
        return False

    if token.revoked:
        return False

    if token.used:
        return False

    if token.expires_at < datetime.utcnow():
        return False

    return True


def revoke_refresh_token(
    db: Session,
    token: AuthToken,
) -> None:
    token.revoked = True

    db.commit()


def revoke_all_refresh_tokens(
    db: Session,
    user_id: str,
) -> None:
    (
        db.query(AuthToken)
        .filter(
            AuthToken.user_id == user_id,
            AuthToken.token_type == TokenType.REFRESH,
            AuthToken.revoked.is_(False),
        )
        .update(
            {
                AuthToken.revoked: True,
            },
            synchronize_session=False,
        )
    )

    db.commit()


# ==========================================================
# Email Verification / Password Reset Tokens
# ==========================================================

def get_token_by_hash(
    db: Session,
    token_hash: str,
    token_type: TokenType | None = None,
) -> AuthToken | None:
    query = db.query(AuthToken).filter(AuthToken.token_hash == token_hash)

    if token_type is not None:
        query = query.filter(AuthToken.token_type == token_type)

    return query.first()


# ==========================================================
# Videos
# ==========================================================

def create_video(
    db: Session,
    **kwargs,
) -> Video:
    video = Video(**kwargs)

    db.add(video)
    db.commit()
    db.refresh(video)

    return video


def upsert_video(
    db: Session,
    youtube_video_id: str,
    **kwargs,
) -> Video:
    video = get_video(db, youtube_video_id)

    if video is None:
        return create_video(
            db,
            youtube_video_id=youtube_video_id,
            **kwargs,
        )

    return update_video(
        db,
        video,
        **kwargs,
    )


def get_video(
    db: Session,
    youtube_video_id: str,
) -> Video | None:
    return (
        db.query(Video)
        .filter(
            Video.youtube_video_id == youtube_video_id
        )
        .first()
    )


# ==========================================================
# History
# ==========================================================

def create_history(
    db: Session,
    **kwargs,
) -> UserVideoHistory:
    history = UserVideoHistory(**kwargs)

    db.add(history)
    db.commit()
    db.refresh(history)

    return history


def history_exists(
    db: Session,
    user_id: str,
    video_id: str,
) -> bool:
    return (
        db.query(UserVideoHistory)
        .filter(
            UserVideoHistory.user_id == user_id,
            UserVideoHistory.video_id == video_id,
        )
        .first()
        is not None
    )


def record_user_video_history(
    db: Session,
    user_id: str,
    video_id: str,
) -> UserVideoHistory:
    return create_history(
        db,
        user_id=user_id,
        video_id=video_id,
    )


def user_has_video_access(
    db: Session,
    user_id: str,
    youtube_video_id: str,
) -> bool:
    return (
        db.query(UserVideoHistory)
        .join(Video, UserVideoHistory.video_id == Video.id)
        .filter(
            UserVideoHistory.user_id == user_id,
            Video.youtube_video_id == youtube_video_id,
        )
        .first()
        is not None
    )
def get_user_by_id(
    db: Session,
    user_id: str,
) -> User | None:
    return (
        db.query(User)
        .filter(User.id == user_id)
        .first()
    )
def mark_token_used(
    db: Session,
    token: AuthToken,
) -> None:
    """
    Mark a one-time token as used.
    """

    token.used = True

    db.commit()


def update_password(
    db: Session,
    user: User,
    password_hash: str,
) -> User:
    """
    Update a user's password.
    """

    user.password_hash = password_hash

    db.commit()
    db.refresh(user)

    return user

def get_summary_history(
    db: Session,
    user_id: str,
) -> list[tuple[UserVideoHistory, Video]]:
    return (
        db.query(UserVideoHistory, Video)
        .join(
            Video,
            UserVideoHistory.video_id == Video.id,
        )
        .filter(
            UserVideoHistory.user_id == user_id,
        )
        .order_by(
            UserVideoHistory.created_at.desc(),
        )
        .all()
    )