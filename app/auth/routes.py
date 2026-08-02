from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
import os
from urllib.parse import urlencode
from database import get_db
from app.auth.dependencies import get_current_user
from app.auth.schemas import (
    RegisterRequest,
    LoginRequest,
    TokenResponse,
    UserResponse,
    RefreshRequest,
    ResetPasswordRequest,
    ForgotPasswordRequest,
    VerifyEmailRequest,
    SummaryHistoryResponse
)
from app.auth.service import (
    register,
    login,
    logout,
    logout_all,
    reset_password,
    forgot_password,
    verify_email,
    refresh,
    oauth_authorization_url,
    oauth_callback,
    get_summary_history
)
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173")
router = APIRouter()


@router.get("/oauth/{provider}/login")
def oauth_login(provider: str):
    authorization_url, _ = oauth_authorization_url(provider)
    return RedirectResponse(url=authorization_url, status_code=307)


@router.get("/oauth/{provider}/callback")
def oauth_callback_route(
    provider: str,
    code: str,
    state: str,
    db: Session = Depends(get_db),
):
    session = oauth_callback(db, provider, code, state)

    params = urlencode(
        {
            "access_token": session.access_token,
            "refresh_token": session.refresh_token,
        }
    )

    return RedirectResponse(
        url=f"{FRONTEND_URL}/oauth/callback?{params}",
        status_code=302,
    )
@router.post(
    "/register",
    response_model=TokenResponse,
)
def register_route(
    req: RegisterRequest,
    db: Session = Depends(get_db),
):
    return register(db, req)


@router.post(
    "/login",
    response_model=TokenResponse,
)
def login_route(
    req: LoginRequest,
    db: Session = Depends(get_db),
):
    return login(db, req)


@router.get(
    "/me",
    response_model=UserResponse,
)
def me(
    user=Depends(get_current_user),
):
    return user
@router.get(
    "/summary-history",
    response_model=SummaryHistoryResponse,
)
def summary_history(
    user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return get_summary_history(
        db=db,
        user=user,
    )

@router.post(
    "/refresh",
    response_model=TokenResponse,
)
def refresh_route(
    req: RefreshRequest,
    db: Session = Depends(get_db),
):
    return refresh(
        db,
        req.refresh_token,
    )
@router.post("/logout")
def logout_route(
    req: RefreshRequest,
    db: Session = Depends(get_db),
):
    return logout(
        db,
        req.refresh_token,
    )


@router.post("/logout-all")
def logout_all_route(
    user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return logout_all(
        db,
        user,
    )


@router.post("/verify-email")
def verify_email_route(
    req: VerifyEmailRequest,
    db: Session = Depends(get_db),
):
    return verify_email(db, req)


@router.post("/reset-password")
def reset_password_route(
    req: ResetPasswordRequest,
    db: Session = Depends(get_db),
):
    return reset_password(db, req)


@router.post("/forgot-password")
def forgot_password_route(
    req: ForgotPasswordRequest,
    db: Session = Depends(get_db),
):
    return forgot_password(db, req)


