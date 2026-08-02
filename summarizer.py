import os

from ai_client import call_ai
from config import MAX_CHUNK_WORDS
from schema import CHUNK_SUMMARY_SCHEMA, FINAL_SUMMARY_SCHEMA


PROMPTS_DIR = os.path.join(os.path.dirname(__file__), "prompts")


def load_prompt(filename: str) -> str:
    """
    Load a prompt from the prompts directory.
    """

    path = os.path.join(PROMPTS_DIR, filename)

    if not os.path.exists(path):
        raise FileNotFoundError(f"Prompt not found: {path}")

    with open(path, "r", encoding="utf-8") as file:
        return file.read()


def format_timestamp(seconds: float) -> str:
    """
    Convert seconds into HH:MM:SS or MM:SS.
    """

    seconds = int(seconds)

    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60

    if hours > 0:
        return f"{hours:02}:{minutes:02}:{secs:02}"

    return f"{minutes:02}:{secs:02}"


def build_chunks(segments: list) -> list:
    """
    Split transcript into dynamic chunks.
    """

    chunks = []

    current_text = []
    current_words = 0

    current_start = None
    current_end = None

    for segment in segments:

        text = segment["text"].strip()

        if not text:
            continue

        word_count = len(text.split())

        if current_start is None:
            current_start = segment["start"]

        if current_words + word_count > MAX_CHUNK_WORDS and current_text:

            chunks.append({
                "start": current_start,
                "end": current_end,
                "start_time": format_timestamp(current_start),
                "end_time": format_timestamp(current_end),
                "text": " ".join(current_text)
            })

            current_text = []
            current_words = 0
            current_start = segment["start"]

        current_text.append(text)
        current_words += word_count
        current_end = segment["end"]

    if current_text:

        chunks.append({
            "start": current_start,
            "end": current_end,
            "start_time": format_timestamp(current_start),
            "end_time": format_timestamp(current_end),
            "text": " ".join(current_text)
        })

    return chunks


def summarize_chunk(chunk: dict) -> dict:
    """
    Generate AI summary for one transcript chunk.
    """

    prompt_template = load_prompt("chunk_summary.txt")

    prompt = prompt_template.format(
        start_time=chunk["start_time"],
        end_time=chunk["end_time"],
        text=chunk["text"]
    )

    summary = call_ai(
        prompt=prompt,
        schema=CHUNK_SUMMARY_SCHEMA
    )

    return {
        "start": chunk["start"],
        "end": chunk["end"],
        "start_time": chunk["start_time"],
        "end_time": chunk["end_time"],
        "title": summary["title"],
        "summary": summary["summary"],
        "key_points": summary["key_points"]
    }


def summarize_video(chunk_summaries: list) -> dict:
    """
    Generate the final overall summary.
    """

    prompt_template = load_prompt("final_summary.txt")

    combined = []

    for index, chunk in enumerate(chunk_summaries, start=1):

        combined.append(
            f"""
Chunk {index}

Time:
{chunk["start_time"]} - {chunk["end_time"]}

Title:
{chunk["title"]}

Summary:
{chunk["summary"]}

Key Points:
{chr(10).join("- " + point for point in chunk["key_points"])}
"""
        )

    prompt = prompt_template.format(
        chunk_summaries="\n\n".join(combined)
    )

    return call_ai(
        prompt=prompt,
        schema=FINAL_SUMMARY_SCHEMA
    )


def generate_summary(transcript_data: dict) -> dict:
    """
    Complete summarization pipeline.

    Transcript
        ↓
    Build Chunks
        ↓
    Summarize Each Chunk
        ↓
    Generate Final Summary
    """

    if not transcript_data:
        raise ValueError("Transcript data is empty.")

    segments = transcript_data.get("segments")

    if not segments:
        raise ValueError("No transcript segments found.")

    chunks = build_chunks(segments)

    print(f"\nCreated {len(chunks)} chunk(s).\n")

    chunk_summaries = []

    for index, chunk in enumerate(chunks, start=1):

        print(f"Summarizing chunk {index}/{len(chunks)}...")

        chunk_summary = summarize_chunk(chunk)

        chunk_summaries.append(chunk_summary)

    print("\nGenerating final summary...\n")

    final_summary = summarize_video(chunk_summaries)

    return {
        "overall_summary": final_summary["overall_summary"],
        "key_takeaways": final_summary["key_takeaways"],
        "chunk_summaries": chunk_summaries
    }