import json
import os

import requests
from dotenv import load_dotenv
from jsonschema import validate, ValidationError

from config import AI_MODEL, TEMPERATURE

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"


def call_ai(
    prompt: str,
    schema: dict,
    model: str = AI_MODEL
) -> dict:
    """
    Sends a prompt to Groq and returns validated structured JSON.
    """

    if not GROQ_API_KEY:
        raise ValueError("GROQ_API_KEY not found.")

    system_prompt = f"""
You are an expert video analysis assistant.

Your job is to respond ONLY with valid JSON.

Rules:
- Return ONLY raw JSON.
- Do NOT use markdown.
- Do NOT wrap the JSON in ``` blocks.
- Do NOT include explanations.
- Every field required by the schema MUST exist.
- Follow this JSON schema exactly.

Schema:

{json.dumps(schema, indent=2)}
"""

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": model,
        "messages": [
            {
                "role": "system",
                "content": system_prompt
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        "temperature": TEMPERATURE
    }

    try:

        response = requests.post(
            GROQ_API_URL,
            headers=headers,
            json=payload,
            timeout=120
        )

        if not response.ok:
            raise RuntimeError(
                f"Groq API Error ({response.status_code}):\n{response.text}"
            )

        data = response.json()

        content = data["choices"][0]["message"]["content"].strip()

        # Remove markdown if model accidentally adds it
        if content.startswith("```"):
            content = content.strip("`")

            if content.startswith("json"):
                content = content[4:].strip()

        result = json.loads(content)

        # Validate against supplied schema
        validate(instance=result, schema=schema)

        return result

    except json.JSONDecodeError as e:
        raise RuntimeError(
            f"Model returned invalid JSON:\n\n{content}"
        ) from e

    except ValidationError as e:
        raise RuntimeError(
            f"Returned JSON does not match schema:\n{e.message}"
        ) from e

    except requests.exceptions.RequestException as e:
        raise RuntimeError(f"Groq request failed: {e}") from e

    except KeyError as e:
        raise RuntimeError("Unexpected response format from Groq.") from e