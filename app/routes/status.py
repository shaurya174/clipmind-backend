from fastapi import APIRouter, Depends, HTTPException
from app.services.job_manager import get_job
from app.auth.dependencies import get_current_user_optional

router = APIRouter()


@router.get("/status/{job_id}")
def status(job_id: str, user=Depends(get_current_user_optional)):
    user_id = user.id if user else None

    job = get_job(job_id, user_id=user_id)

    if not job:
        raise HTTPException(status_code=404, detail="job not found")

    return {
        "job_id": job_id,
        "status": job["status"],
    }