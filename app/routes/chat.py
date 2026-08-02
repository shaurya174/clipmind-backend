from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from database import get_db
from app.auth.dependencies import get_current_user_optional
from app.auth.repository import user_has_video_access
from rag import answer_question

router = APIRouter()


class ChatRequest(BaseModel):
    video_id: str
    question: str


@router.post("/chat")
def chat(
    req: ChatRequest,
    user=Depends(get_current_user_optional),
    db=Depends(get_db),
):
    """
    Chat with a processed YouTube video using RAG.
    """

    if user is None:
        raise HTTPException(
            status_code=401,
            detail="Please sign in to chat with this video.",
        )

    if not user_has_video_access(db, user.id, req.video_id):
        raise HTTPException(
            status_code=403,
            detail="Not authorized to access this video.",
        )

    return answer_question(
        video_id=req.video_id,
        question=req.question,
    )