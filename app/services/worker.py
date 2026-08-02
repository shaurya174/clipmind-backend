from __future__ import annotations

import os

from database import SessionLocal
from app.auth.repository import record_user_video_history, upsert_video
from app.services.pipeline import run_pipeline
from app.services.job_manager import update_job


def run_job(job_id: str, url: str, user_id: str | None = None):
    try:
        # Mark job as processing
        update_job(job_id, status="processing")

        # Run the full pipeline
        result = run_pipeline(url)

        if user_id:
            db = SessionLocal()

            try:
                video = upsert_video(
                    db,
                    youtube_video_id=result["video_id"],
                    title=result["title"],
                    duration=result["duration"],
                    transcript_path=os.path.join("transcripts", f"{result['video_id']}.json"),
                    summary_output_path=result["output_path"],
                    mindmap_path=os.path.join("mindmaps", f"{result['video_id']}.json"),
                )

                record_user_video_history(
                    db,
                    user_id=user_id,
                    video_id=video.id,
                )

            finally:
                db.close()

        # Mark job as completed and store output location
        update_job(
            job_id,
            status="done",
            output_path=result["output_path"],
        )

    except Exception as e:
        update_job(
            job_id,
            status="failed",
            error=str(e),
        )