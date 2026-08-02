import os
import json
from dotenv import load_dotenv
from supabase import Client, create_client

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

if not SUPABASE_URL:
    raise ValueError("SUPABASE_URL is missing.")

if not SUPABASE_SERVICE_ROLE_KEY:
    raise ValueError("SUPABASE_SERVICE_ROLE_KEY is missing.")

supabase: Client = create_client(
    SUPABASE_URL,
    SUPABASE_SERVICE_ROLE_KEY,
)
def upload_json(
    bucket: str,
    path: str,
    data: dict,
) -> None:
    """
    Upload a JSON object to a Supabase Storage bucket.
    """

    payload = json.dumps(
        data,
        ensure_ascii=False,
        indent=2,
    ).encode("utf-8")

    supabase.storage.from_(bucket).upload(
        path=path,
        file=payload,
        file_options={
            "content-type": "application/json",
            "upsert": "true",
        },
    )

def download_json(
    bucket: str,
    path: str,
) -> dict:
    """
    Download a JSON file from Supabase Storage.
    """

    response = supabase.storage.from_(bucket).download(path)

    return json.loads(response.decode("utf-8"))


def upload_binary(
    bucket: str,
    path: str,
    data,
    content_type: str = "application/octet-stream",
) -> None:
    """
    Upload binary data to Supabase Storage.
    """

    if hasattr(data, "tobytes"):
        data = data.tobytes()

    supabase.storage.from_(bucket).upload(
        path=path,
        file=data,
        file_options={
            "content-type": content_type,
            "upsert": "true",
        },
    )

def download_binary(
    bucket: str,
    path: str,
):
    """
    Download binary data from Supabase Storage.
    """

    return supabase.storage.from_(bucket).download(path)


def delete_file(
    bucket: str,
    path: str,
) -> None:
    """
    Delete a file from Supabase Storage.
    """

    supabase.storage.from_(bucket).remove([path])



