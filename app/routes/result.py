from fastapi import APIRouter, Depends, HTTPException

from app.auth.dependencies import get_current_user_optional
from app.services.job_manager import get_job
from storage import download_json

router = APIRouter()


@router.get("/result/{job_id}")
def result(job_id: str, user=Depends(get_current_user_optional)):
    user_id = user.id if user else None

    job = get_job(job_id, user_id=user_id)

    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")

    if job["status"] != "done":
        return {
            "status": job["status"],
            "message": "Result not ready yet",
        }

    output_filename = job["output_path"]

    if not output_filename:
        raise HTTPException(
            status_code=500,
            detail="Output filename missing",
        )

    try:
        return download_json(
            bucket="outputs",
            path=output_filename,
        )
    except Exception:
        raise HTTPException(
            status_code=404,
            detail="Output file not found",
        )