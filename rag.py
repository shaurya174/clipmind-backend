import os
from typing import List

from ai_client import call_ai
from retriever import retrieve_context
from schema import CHAT_RESPONSE_SCHEMA


PROMPTS_DIR = os.path.join(os.path.dirname(__file__), "prompts")


def load_prompt(filename: str) -> str:
    """
    Load prompt file from prompts directory.
    """

    path = os.path.join(PROMPTS_DIR, filename)

    if not os.path.exists(path):
        raise FileNotFoundError(f"Prompt not found: {path}")

    with open(path, "r", encoding="utf-8") as file:
        return file.read()


def format_context(chunks: List[dict]) -> str:
    """
    Convert retrieved transcript chunks into a prompt-friendly format.
    """

    sections = []

    for index, chunk in enumerate(chunks, start=1):

        sections.append(
            f"""
Chunk {index}

Timestamp:
{chunk["start_time"]} - {chunk["end_time"]}

Transcript:
{chunk["text"]}
"""
        )

    return "\n\n".join(sections)


def build_prompt(question: str, chunks: List[dict]) -> str:
    """
    Build the final RAG prompt.
    """

    prompt_template = load_prompt("chat_with_video.txt")

    return prompt_template.format(
        context=format_context(chunks),
        question=question,
    )


def build_sources(chunks: List[dict]) -> list:
    """
    Convert retrieved chunks into source timestamps.
    """

    sources = []

    seen = set()

    for chunk in chunks:

        key = (
            chunk["start_time"],
            chunk["end_time"],
        )

        if key in seen:
            continue

        seen.add(key)

        sources.append(
            {
                "start_time": chunk["start_time"],
                "end_time": chunk["end_time"],
            }
        )

    return sources


def answer_question(
    video_id: str,
    question: str,
    top_k: int = 5,
) -> dict:
    """
    Main RAG pipeline.

    Flow

    Question
        ↓
    Retrieve
        ↓
    Prompt
        ↓
    LLM
        ↓
    Structured Answer
    """

    if not question.strip():
        raise ValueError("Question cannot be empty.")

    retrieved_chunks = retrieve_context(
        video_id=video_id,
        question=question,
        top_k=top_k,
    )

    if not retrieved_chunks:

        return {
            "answer": (
                "I couldn't find any relevant information "
                "from this video's transcript."
            ),
            "used_transcript": False,
            "related_topic": False,
            "sources": [],
        }

    prompt = build_prompt(
        question=question,
        chunks=retrieved_chunks,
    )

    response = call_ai(
        prompt=prompt,
        schema=CHAT_RESPONSE_SCHEMA,
    )
    return {
        "answer": response["answer"],
        "used_transcript": response["used_transcript"],
        "related_topic": response["related_topic"],
        "sources": build_sources(retrieved_chunks),
    }