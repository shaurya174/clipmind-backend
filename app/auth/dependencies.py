from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError
from sqlalchemy.orm import Session

from database import get_db
from app.auth.jwt import decode_token
from app.auth.repository import get_user_by_id

security = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
):
    """
    Validate access token and return the authenticated user.
    """

    if credentials is None:
        raise HTTPException(
            status_code=401,
            detail="Authentication required.",
        )

    token = credentials.credentials

    try:
        payload = decode_token(token)

    except JWTError:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired token.",
        )

    if payload.get("type") != "access":
        raise HTTPException(
            status_code=401,
            detail="Invalid access token.",
        )

    user = get_user_by_id(
        db,
        payload["sub"],
    )

    if user is None:
        raise HTTPException(
            status_code=401,
            detail="User not found.",
        )

    return user


def get_current_user_optional(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
):
    """
    Return the authenticated user if a valid access token is provided.
    Otherwise return None.
    """

    if credentials is None:
        return None

    token = credentials.credentials

    try:
        payload = decode_token(token)

    except JWTError:
        return None

    if payload.get("type") != "access":
        return None

    return get_user_by_id(
        db,
        payload["sub"],
    )