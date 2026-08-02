from audio_extractor import extract_audio, delete_audio
from transcriber import (
    transcribe_audio,
    save_transcript,
    load_transcript,
)
from summarizer import generate_summary
from output_manager import save_output
from retriever import build_vector_store
from utils.youtube_id import get_video_id
from mindmap import generate_mindmap

def run_pipeline(url: str):
    # STEP 1: Identity layer
    video_id = get_video_id(url)

    print(f"\nVideo ID: {video_id}\n")

    # STEP 2: Transcript cache check
    cached = load_transcript(video_id)

    if cached is None:
        # ---------------- CACHE MISS ----------------
        print("No transcript cache found.\n")

        print("Downloading audio...\n")
        audio = extract_audio(video_id)

        title = audio["title"]
        duration = audio["duration"]

        print(f"Title: {title}")
        print(f"Duration: {duration}\n")

        print("Transcribing audio...\n")
        transcript = transcribe_audio(audio["audio_path"])

        print("Saving transcript...\n")
        path = save_transcript(
            transcript_data=transcript,
            video_id=video_id,
            title=title,
            duration=duration,
        )
        print(f"Saved: {path}\n")

        print("Cleaning audio...\n")
        delete_audio(audio["audio_path"])

    else:
        # ---------------- CACHE HIT ----------------
        print("✓ Transcript cache found.")
        print("Loading cached transcript...\n")

        title = cached["title"]
        duration = cached["duration"]
        transcript = cached["transcript"]

        print(f"Title: {title}")
        print(f"Duration: {duration}\n")

    # STEP 3: Build vector store (only created once per video)
    print("Building vector store...\n")

    build_vector_store(
        video_id=video_id,
        transcript_data=transcript,
    )

    print("Vector store ready.\n")

    # STEP 4: AI summarization
    print("Generating summary...\n")
    summary = generate_summary(transcript)
    print("Generating mind map...\n")
    mind_map = generate_mindmap(
        video_id=video_id,
        transcript_data=transcript,
        summary=summary,
    )
    print("Mind map ready.\n")
    # STEP 5: Save summary output
    output_path = save_output(
        summary=summary,
        video_id=video_id,
        title=title,
        duration=duration,
    )

    print(f"Summary saved: {output_path}")

    # STEP 6: Console output
    print("\n" + "=" * 70)
    print("FINAL SUMMARY")
    print("=" * 70)

    print("\nOverall Summary:\n")
    print(summary["overall_summary"])

    print("\nKey Takeaways:\n")
    for i, point in enumerate(summary["key_takeaways"], 1):
        print(f"{i}. {point}")

    print("\nChunk Summaries:\n")
    for chunk in summary["chunk_summaries"]:
        print(f"[{chunk['start_time']} - {chunk['end_time']}]")
        print(f"{chunk['title']}")
        print(f"{chunk['summary']}\n")

    # STEP 7: Return structured data
    return {
        "video_id": video_id,
        "title": title,
        "duration": duration,
        "output_path": output_path,
        "summary": summary,
        "mind_map": mind_map,
    }