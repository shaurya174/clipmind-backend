import os
from datetime import datetime

from faster_whisper import WhisperModel

from storage import upload_json, download_json

# Load model once (IMPORTANT: performance improvement)
model = WhisperModel("base", device="cpu", compute_type="float32")


def transcribe_audio(file_path: str) -> dict:
    """
    Transcribes audio into structured time-aware segments.

    Returns:
        {
            "text": full transcript string,
            "segments": [
                {
                    "start": float,
                    "end": float,
                    "text": str
                }
            ]
        }
    """

    # 1. Validate file exists
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Audio file not found at: {file_path}")

    print(f"Processing audio: {os.path.basename(file_path)}")

    # 2. Run transcription (keeps timestamps)
    segments, info = model.transcribe(file_path, beam_size=5)

    # 3. Build structured segment list
    segment_list = []
    full_text_parts = []

    for segment in segments:
        cleaned_text = segment.text.strip()

        segment_list.append(
            {
                "start": round(segment.start, 2),
                "end": round(segment.end, 2),
                "text": cleaned_text,
            }
        )

        full_text_parts.append(cleaned_text)

    # 4. Build final outputs
    full_text = " ".join(full_text_parts).strip()

    return {
        "text": full_text,
        "segments": segment_list,
    }


def save_transcript(
    transcript_data: dict,
    video_id: str,
    title: str,
    duration: str,
) -> str:
    """
    Save transcript and metadata to Supabase Storage.

    Returns:
        Object name stored in the transcripts bucket.
    """

    filename = f"{video_id}.json"

    payload = {
        "video_id": video_id,
        "title": title,
        "duration": duration,
        "created_at": datetime.now().isoformat(),
        "transcript": transcript_data,
    }

    upload_json(
        bucket="transcripts",
        path=filename,
        data=payload,
    )

    return filename


def load_transcript(video_id: str) -> dict | None:
    """
    Load cached transcript from Supabase Storage.

    Returns:
        Transcript dictionary or None if it doesn't exist.
    """

    try:
        return download_json(
            bucket="transcripts",
            path=f"{video_id}.json",
        )
    except Exception:
        return None