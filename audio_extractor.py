import os
import time
import tempfile
import yt_dlp


def format_duration(seconds: int) -> str:
    """
    Converts seconds into a human-readable string format.
    Only shows non-zero units.
    """
    if seconds <= 0:
        return "0 seconds"

    days, remainder = divmod(seconds, 86400)
    hours, remainder = divmod(remainder, 3600)
    minutes, secs = divmod(remainder, 60)

    parts = []

    if days > 0:
        parts.append(f"{days} day" if days == 1 else f"{days} days")

    if hours > 0:
        parts.append(f"{hours} hour" if hours == 1 else f"{hours} hours")

    if minutes > 0:
        parts.append(f"{minutes} min")

    if secs > 0 and days == 0 and hours == 0:
        parts.append(f"{secs} sec" if minutes > 0 else f"{secs} seconds")
    elif secs > 0 and (days > 0 or hours > 0):
        pass
    elif not parts:
        parts.append(f"{secs} seconds")

    return " ".join(parts)


def extract_audio(video_id: str, output_dir: str = ".") -> dict:
    """
    Extracts video metadata, downloads the best audio, converts it to MP3,
    and returns a structured dictionary with audio path, title, and formatted duration.
    """

    timestamp = int(time.time())
    base_name = f"audio_{timestamp}"
    url = f"https://www.youtube.com/watch?v={video_id}"

    os.makedirs(output_dir, exist_ok=True)

    output_template = os.path.join(output_dir, base_name)

    cookie_file = None

    try:
        # Read YouTube cookies from environment variable.
        # This is primarily used on Azure.
        youtube_cookies = os.getenv("YOUTUBE_COOKIES")

        if youtube_cookies:
            cookie_file = tempfile.NamedTemporaryFile(
                mode="w",
                suffix=".txt",
                delete=False,
                encoding="utf-8",
            )

            cookie_file.write(youtube_cookies)
            cookie_file.close()

            print("YouTube cookies loaded from environment.")

        ydl_opts = {
            "format": "bestaudio/best",
            "outtmpl": output_template,
            "quiet": True,
            "no_warnings": True,

            # Use cookies when available.
            **({"cookiefile": cookie_file.name} if cookie_file else {}),

            # Improve compatibility with YouTube extraction.
            "extractor_args": {
                "youtube": {
                    "player_client": ["android", "web"]
                }
            },

            "postprocessors": [
                {
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                    "preferredquality": "192",
                }
            ],
        }

        print(f"Processing video_id: {video_id}...")

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(url, download=True)

            title = info_dict.get("title", "Unknown Title")
            raw_duration_seconds = int(info_dict.get("duration", 0))

        final_mp3_path = os.path.abspath(f"{output_template}.mp3")
        formatted_time = format_duration(raw_duration_seconds)

        if os.path.exists(final_mp3_path):
            print(f"Success! Audio saved to: {final_mp3_path}")

            return {
                "audio_path": final_mp3_path,
                "title": title,
                "duration": formatted_time,
            }
        else:
            raise FileNotFoundError(
                f"Expected MP3 file not found at: {final_mp3_path}"
            )

    finally:
        # Always remove the temporary cookie file.
        if cookie_file and os.path.exists(cookie_file.name):
            os.remove(cookie_file.name)


def delete_audio(audio_path: str):
    if os.path.exists(audio_path):
        os.remove(audio_path)
