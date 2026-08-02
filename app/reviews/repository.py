from sqlalchemy import func
from sqlalchemy.orm import Session

from app.auth.models import User
from app.reviews.models import Review


# ==========================================================
# Queries
# ==========================================================

def get_review_by_user(
    db: Session,
    user_id: str,
) -> Review | None:
    return (
        db.query(Review)
        .filter(Review.user_id == user_id)
        .first()
    )


def get_all_reviews(
    db: Session,
):
    return (
        db.query(Review)
        .join(User)
        .order_by(Review.created_at.desc())
        .all()
    )


def get_average_rating(
    db: Session,
) -> float:
    avg = db.query(func.avg(Review.rating)).scalar()

    if avg is None:
        return 0.0

    return round(float(avg), 1)


def get_total_reviews(
    db: Session,
) -> int:
    return db.query(func.count(Review.id)).scalar()


# ==========================================================
# Mutations
# ==========================================================

def create_review(
    db: Session,
    **kwargs,
) -> Review:
    review = Review(**kwargs)

    db.add(review)
    db.commit()
    db.refresh(review)

    return review


def update_review(
    db: Session,
    review: Review,
    **kwargs,
) -> Review:
    for key, value in kwargs.items():
        setattr(review, key, value)

    db.commit()
    db.refresh(review)

    return review