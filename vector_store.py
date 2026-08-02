import faiss
import numpy as np

from storage import (
    upload_binary,
    download_binary,
    upload_json,
    download_json,
)


def create_index(
    embeddings: np.ndarray,
    metadata: list,
    video_id: str,
) -> None:
    """
    Create and upload a FAISS index for one video.
    """

    if len(embeddings) == 0:
        raise ValueError("Embeddings cannot be empty.")

    dimension = embeddings.shape[1]

    index = faiss.IndexFlatIP(dimension)

    index.add(embeddings)

    # Serialize FAISS index into memory
    serialized_index = faiss.serialize_index(index)

    upload_binary(
        bucket="vector_store",
        path=f"{video_id}.index",
        data=serialized_index,
    )

    upload_json(
        bucket="vector_store",
        path=f"{video_id}_metadata.json",
        data=metadata,
    )


def load_index(video_id: str):
    """
    Load a FAISS index and its metadata from Supabase Storage.

    Returns:
        (index, metadata)

    or

        (None, None)
    """

    try:
        index_bytes = download_binary(
            bucket="vector_store",
            path=f"{video_id}.index",
        )

        metadata = download_json(
            bucket="vector_store",
            path=f"{video_id}_metadata.json",
        )

        index = faiss.deserialize_index(
            np.frombuffer(index_bytes, dtype=np.uint8)
        )

        return index, metadata

    except Exception:
        return None, None


def search_index(
    index,
    metadata: list,
    query_embedding: np.ndarray,
    top_k: int = 5,
) -> list:
    """
    Search the FAISS index.

    Returns the top-k transcript chunks with similarity scores.
    """

    if query_embedding.ndim == 1:
        query_embedding = query_embedding.reshape(1, -1)

    scores, indices = index.search(query_embedding, top_k)

    results = []

    for score, idx in zip(scores[0], indices[0]):

        if idx == -1:
            continue

        item = metadata[idx].copy()

        item["score"] = float(score)

        results.append(item)

    return results


def index_exists(video_id: str) -> bool:
    """
    Returns True if the vector store exists.
    """

    try:
        download_binary(
            bucket="vector_store",
            path=f"{video_id}.index",
        )

        download_json(
            bucket="vector_store",
            path=f"{video_id}_metadata.json",
        )

        return True

    except Exception:
        return False