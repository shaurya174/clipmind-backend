from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from database import get_db
from app.auth.dependencies import get_current_user
from app.auth.models import User
from app.reviews.schemas import (
    ReviewListResponse,
    ReviewRequest,
    MyReviewResponse,
)
from app.reviews.service import (
    get_my_review,
    get_reviews,
    save_review,
)

router = APIRouter(
    prefix="/reviews",
    tags=["Reviews"],
)


@router.get(
    "",
    response_model=ReviewListResponse,
)
def list_reviews(
    db: Session = Depends(get_db),
):
    return get_reviews(db)


@router.get(
    "/me",
    response_model=MyReviewResponse | None,
)
def my_review(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return get_my_review(
        db,
        user,
    )


@router.post("")
def submit_review(
    payload: ReviewRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    save_review(
        db,
        user,
        payload,
    )

    return {
        "message": "Review saved successfully."
    }