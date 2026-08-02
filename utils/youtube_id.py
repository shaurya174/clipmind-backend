from urllib.parse import urlparse, parse_qs
import re


def get_video_id(url: str) -> str:
    """
    Extract YouTube video ID from any valid URL.
    """

    parsed = urlparse(url)

    # standard YouTube URL
    if parsed.hostname in ["www.youtube.com", "youtube.com"]:
        if parsed.path == "/watch":
            # Safe default prevents IndexError if 'v' parameter is missing
            video_id = parse_qs(parsed.query).get("v", [""])[0]
            if video_id:
                return video_id

        if parsed.path.startswith("/shorts/"):
            return parsed.path.split("/")[2]

    # short URL
    if parsed.hostname == "youtu.be":
        return parsed.path.lstrip("/")

    # fallback regex
    match = re.search(r"(?:v=|youtu\.be/|shorts/)([a-zA-Z0-9_-]{11})", url)
    if match:
        return match.group(1)

    raise ValueError("Invalid YouTube URL")