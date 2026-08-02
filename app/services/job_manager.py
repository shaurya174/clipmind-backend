from database import SessionLocal
from models import Job

ALLOWED_FIELDS = {"status", "output_path", "error"}


def create_job(user_id: str | None = None) -> str:
    """
    Create a new processing job.

    Returns:
        job_id (UUID string)
    """

    db = SessionLocal()

    try:
        job = Job(
            status="queued",
            user_id=user_id,
            output_path=None,
            error=None,
        )

        db.add(job)
        db.commit()
        db.refresh(job)

        return job.id

    finally:
        db.close()


def update_job(job_id: str, **kwargs) -> None:
    """
    Update one or more allowed job fields.
    """

    db = SessionLocal()

    try:
        job = db.query(Job).filter(Job.id == job_id).first()

        if job is None:
            return

        for key, value in kwargs.items():
            if key in ALLOWED_FIELDS:
                setattr(job, key, value)

        db.commit()
        db.refresh(job)

    finally:
        db.close()


def get_job(job_id: str, user_id: str | None = None) -> dict | None:
    """
    Retrieve job information.

    Returns:
        {
            "id": ...,
            "status": ...,
            "user_id": ...,
            "output_path": ...,
            "error": ...
        }

        or None
    """

    db = SessionLocal()

    try:
        query = db.query(Job).filter(Job.id == job_id)

        if user_id is not None:
            query = query.filter(Job.user_id == user_id)

        job = query.first()

        if job is None:
            return None

        return {
            "id": job.id,
            "status": job.status,
            "user_id": job.user_id,
            "output_path": job.output_path,
            "error": job.error,
        }

    finally:
        db.close()