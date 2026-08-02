from sqlalchemy.orm import Session

from app.auth.models import User
from app.reviews import repository
from app.reviews.schemas import (
    MyReviewResponse,
    ReviewListResponse,
    ReviewRequest,
    ReviewResponse,
)


# ==========================================================
# Create / Update Review
# ==========================================================

def save_review(
    db: Session,
    user: User,
    data: ReviewRequest,
):
    existing = repository.get_review_by_user(
        db,
        user.id,
    )

    if existing is None:
        repository.create_review(
            db,
            user_id=user.id,
            rating=data.rating,
            review=data.review,
        )
    else:
        repository.update_review(
            db,
            existing,
            rating=data.rating,
            review=data.review,
        )


# ==========================================================
# Current User Review
# ==========================================================

def get_my_review(
    db: Session,
    user: User,
):
    review = repository.get_review_by_user(
        db,
        user.id,
    )

    if review is None:
        return None

    return MyReviewResponse(
        rating=review.rating,
        review=review.review,
    )


# ==========================================================
# Public Reviews
# ==========================================================

def get_reviews(
    db: Session,
):
    reviews = repository.get_all_reviews(db)

    items = [
        ReviewResponse(
            id=r.id,
            username=r.user.username,
            avatar_url=r.user.avatar_url,
            rating=r.rating,
            review=r.review,
            created_at=r.created_at,
        )
        for r in reviews
    ]

    return ReviewListResponse(
        average_rating=repository.get_average_rating(db),
        total_reviews=repository.get_total_reviews(db),
        reviews=items,
    )