from __future__ import annotations

import enum
import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base


# ==========================================================
# ENUMS
# ==========================================================

class AuthProvider(str, enum.Enum):
    LOCAL = "local"
    GOOGLE = "google"
    GITHUB = "github"


class TokenType(str, enum.Enum):
    REFRESH = "refresh"
    VERIFY_EMAIL = "verify_email"
    RESET_PASSWORD = "reset_password"


# ==========================================================
# USER
# ==========================================================

class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )

    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
        index=True
    )

    username: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        nullable=False,
        index=True
    )

    password_hash: Mapped[str | None] = mapped_column(
        Text,
        nullable=True
    )

    provider: Mapped[AuthProvider] = mapped_column(
        Enum(AuthProvider),
        default=AuthProvider.LOCAL,
        nullable=False,
    )

    provider_id: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        unique=True,
    )

    avatar_url: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    is_verified: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    history = relationship(
        "UserVideoHistory",
        back_populates="user",
        cascade="all, delete-orphan",
    )

    review = relationship(
        "Review",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan",
    )

    tokens = relationship(
        "AuthToken",
        back_populates="user",
        cascade="all, delete-orphan",
    )


# ==========================================================
# VIDEO
# ==========================================================

class Video(Base):
    __tablename__ = "videos"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )

    youtube_video_id: Mapped[str] = mapped_column(
        String(20),
        unique=True,
        nullable=False,
        index=True,
    )

    title: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    duration: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    transcript_path: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    summary_output_path: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    mindmap_path: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    users = relationship(
        "UserVideoHistory",
        back_populates="video",
        cascade="all, delete-orphan",
    )


# ==========================================================
# USER VIDEO HISTORY
# ==========================================================

class UserVideoHistory(Base):
    __tablename__ = "user_video_history"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )

    user_id: Mapped[str] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )

    video_id: Mapped[str] = mapped_column(
        ForeignKey("videos.id", ondelete="CASCADE"),
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    user = relationship(
        "User",
        back_populates="history",
    )

    video = relationship(
        "Video",
        back_populates="users",
    )

    # __table_args__ = (
    #     UniqueConstraint(
    #         "user_id",
    #         "video_id",
    #         name="uq_user_video",
    #     ),
    # )


# ==========================================================
# AUTH TOKENS
# ==========================================================

class AuthToken(Base):
    __tablename__ = "auth_tokens"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )

    user_id: Mapped[str] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Used for refresh JWTs (JWT ID)
    jti: Mapped[str | None] = mapped_column(
        String(36),
        unique=True,
        nullable=True,
    )

    # Used for email verification / password reset tokens
    token_hash: Mapped[str | None] = mapped_column(
        Text,
        unique=True,
        nullable=True,
    )

    token_type: Mapped[TokenType] = mapped_column(
        Enum(TokenType),
        nullable=False,
    )

    expires_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
    )

    revoked: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    used: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    user = relationship(
        "User",
        back_populates="tokens",
    )

# ==========================================================
# INDEXES
# ==========================================================

Index("ix_auth_tokens_user_id", AuthToken.user_id)
Index("ix_history_user", UserVideoHistory.user_id)
Index("ix_history_video", UserVideoHistory.video_id)