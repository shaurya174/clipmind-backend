from storage import download_json, upload_json


def save_mindmap(
    video_id: str,
    mindmap: dict,
) -> str:
    """
    Save a generated mind map to Supabase Storage.

    Returns:
        Object name stored in the mindmaps bucket.
    """

    filename = f"{video_id}.json"

    upload_json(
        bucket="mindmaps",
        path=filename,
        data=mindmap,
    )

    return filename


def load_mindmap(video_id: str) -> dict | None:
    """
    Load a previously generated mind map.

    Returns:
        Mind map dictionary or None if it doesn't exist.
    """

    try:
        return download_json(
            bucket="mindmaps",
            path=f"{video_id}.json",
        )
    except Exception:
        return None


def mindmap_exists(video_id: str) -> bool:
    """
    Returns True if a mind map already exists.
    """

    try:
        download_json(
            bucket="mindmaps",
            path=f"{video_id}.json",
        )
        return True
    except Exception:
        return False