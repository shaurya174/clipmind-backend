from datetime import datetime

from pydantic import BaseModel, Field


# ==========================================================
# REQUEST
# ==========================================================

class ReviewRequest(BaseModel):
    rating: int = Field(
        ge=1,
        le=5,
    )

    review: str = Field(
        min_length=5,
        max_length=1000,
    )


# ==========================================================
# RESPONSE
# ==========================================================

class ReviewResponse(BaseModel):
    id: str
    username: str
    avatar_url: str | None
    rating: int
    review: str
    created_at: datetime


class ReviewListResponse(BaseModel):
    average_rating: float
    total_reviews: int
    reviews: list[ReviewResponse]


class MyReviewResponse(BaseModel):
    rating: int
    review: str