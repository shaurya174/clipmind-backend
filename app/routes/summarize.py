from threading import Thread

from fastapi import APIRouter, Depends

from app.auth.dependencies import get_current_user_optional
from app.models import SummarizeRequest
from app.services.job_manager import create_job
from app.services.worker import run_job

router = APIRouter()


@router.post("/summarize")
def summarize(
    req: SummarizeRequest,
    user=Depends(get_current_user_optional),
):
    user_id = user.id if user else None

    job_id = create_job(user_id=user_id)

    thread = Thread(
        target=run_job,
        args=(job_id, req.url, user_id),
    )
    thread.start()

    return {
        "job_id": job_id,
        "status": "queued",
    }