from datetime import datetime

from storage import upload_json


def save_output(
    summary: dict,
    video_id: str,
    title: str,
    duration: str,
) -> str:
    """
    Save the generated summary to Supabase Storage.

    Object name format:
        <video_id>_<YYYYMMDD_HHMMSS>.json

    Returns:
        The object name stored in the outputs bucket.
    """

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    filename = f"{video_id}_{timestamp}.json"

    payload = {
        "video_id": video_id,
        "title": title,
        "duration": duration,
        "generated_at": datetime.now().isoformat(),
        "summary": summary,
    }

    upload_json(
        bucket="outputs",
        path=filename,
        data=payload,
    )

    return filename