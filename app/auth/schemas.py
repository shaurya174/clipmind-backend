from pydantic import BaseModel, EmailStr, Field
from datetime import datetime


# ---------- Requests ----------

class RegisterRequest(BaseModel):
    email: EmailStr
    username: str = Field(min_length=3, max_length=50)
    password: str = Field(min_length=8, max_length=128)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class RefreshRequest(BaseModel):
    refresh_token: str


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str = Field(min_length=8, max_length=128)


class VerifyEmailRequest(BaseModel):
    token: str


# ---------- Responses ----------

class UserResponse(BaseModel):
    id: str
    email: EmailStr
    username: str
    provider: str
    avatar_url: str | None
    is_verified: bool

    class Config:
        from_attributes = True
class SummaryHistoryItem(BaseModel):
    youtube_video_id: str
    title: str
    duration: str
    thumbnail_url: str
    summarized_at: datetime

    class Config:
        from_attributes = True


class SummaryHistoryResponse(BaseModel):
    items: list[SummaryHistoryItem]

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: UserResponse
    verification_token: str | None = None