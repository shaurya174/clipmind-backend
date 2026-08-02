from fastapi import APIRouter, Depends, HTTPException

from transcriber import load_transcript
from database import get_db
from app.auth.dependencies import get_current_user_optional
from app.auth.repository import user_has_video_access

router = APIRouter()


@router.get("/transcript/{video_id}")
def get_transcript(
    video_id: str,
    user=Depends(get_current_user_optional),
    db=Depends(get_db),
):
    """
    Return the cached transcript for a processed video.
    """

    # Only enforce ownership for authenticated users.
    if user is not None:
        if not user_has_video_access(db, user.id, video_id):
            raise HTTPException(
                status_code=403,
                detail="Not authorized to access this transcript.",
            )

    transcript = load_transcript(video_id)

    if transcript is None:
        raise HTTPException(
            status_code=404,
            detail="Transcript not found.",
        )

    return {
        "video_id": transcript["video_id"],
        "title": transcript["title"],
        "duration": transcript["duration"],
        "text": transcript["transcript"]["text"],
        "segments": transcript["transcript"]["segments"],
    }