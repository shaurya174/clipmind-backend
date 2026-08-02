import os

from config import MAX_CHUNK_WORDS
from embeddings import embed_text, embed_texts
from vector_store import (
    create_index,
    load_index,
    search_index,
    index_exists,
)


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
    Build transcript chunks for semantic retrieval.
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

        words = len(text.split())

        if current_start is None:
            current_start = segment["start"]

        if current_words + words > MAX_CHUNK_WORDS and current_text:

            chunks.append(
                {
                    "start": current_start,
                    "end": current_end,
                    "start_time": format_timestamp(current_start),
                    "end_time": format_timestamp(current_end),
                    "text": " ".join(current_text),
                }
            )

            current_text = []
            current_words = 0
            current_start = segment["start"]

        current_text.append(text)
        current_words += words
        current_end = segment["end"]

    if current_text:

        chunks.append(
            {
                "start": current_start,
                "end": current_end,
                "start_time": format_timestamp(current_start),
                "end_time": format_timestamp(current_end),
                "text": " ".join(current_text),
            }
        )

    return chunks


def build_vector_store(
    video_id: str,
    transcript_data: dict,
) -> None:
    """
    Build a FAISS index for a video if it doesn't already exist.
    """

    if index_exists(video_id):
        return

    segments = transcript_data.get("segments")

    if not segments:
        raise ValueError("Transcript contains no segments.")

    chunks = build_chunks(segments)

    texts = [chunk["text"] for chunk in chunks]

    embeddings = embed_texts(texts)

    create_index(
        embeddings=embeddings,
        metadata=chunks,
        video_id=video_id,
    )


def retrieve_context(
    video_id: str,
    question: str,
    top_k: int = 5,
) -> list:
    """
    Retrieve the most relevant transcript chunks for a question.
    """

    index, metadata = load_index(video_id)

    if index is None:
        raise FileNotFoundError(
            f"No vector store found for video {video_id}"
        )

    query_embedding = embed_text(question)

    return search_index(
        index=index,
        metadata=metadata,
        query_embedding=query_embedding,
        top_k=top_k,
    )