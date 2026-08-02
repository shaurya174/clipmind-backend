import os

from ai_client import call_ai
from mindmap_manager import (
    load_mindmap,
    save_mindmap,
)
from schema import MIND_MAP_SCHEMA


PROMPTS_DIR = os.path.join(
    os.path.dirname(__file__),
    "prompts",
)


def load_prompt(filename: str) -> str:
    """
    Load a prompt from the prompts directory.
    """

    path = os.path.join(PROMPTS_DIR, filename)

    if not os.path.exists(path):
        raise FileNotFoundError(f"Prompt not found: {path}")

    with open(path, "r", encoding="utf-8") as file:
        return file.read()


def build_prompt(
    transcript_data: dict,
    summary: dict,
) -> str:
    """
    Build the AI prompt for mind map generation.
    """

    transcript = transcript_data["text"]

    overall_summary = summary["overall_summary"]

    key_takeaways = "\n".join(
        f"- {item}"
        for item in summary["key_takeaways"]
    )

    template = load_prompt("mind_map.txt")

    return template.format(
        overall_summary=overall_summary,
        key_takeaways=key_takeaways,
        transcript=transcript,
    )


def generate_mindmap(
    video_id: str,
    transcript_data: dict,
    summary: dict,
) -> dict:
    """
    Generate or load a cached mind map.
    """

    cached = load_mindmap(video_id)

    if cached is not None:
        return cached

    prompt = build_prompt(
        transcript_data=transcript_data,
        summary=summary,
    )

    mindmap = call_ai(
        prompt=prompt,
        schema=MIND_MAP_SCHEMA,
    )

    save_mindmap(
        video_id=video_id,
        mindmap=mindmap,
    )

    return mindmap