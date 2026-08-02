from sentence_transformers import SentenceTransformer
import numpy as np

# Load model once (IMPORTANT: performance improvement)
model = SentenceTransformer("all-MiniLM-L6-v2")


def embed_text(text: str) -> np.ndarray:
    """
    Generate an embedding for a single text.

    Returns:
        numpy.ndarray of shape (384,)
    """

    if not text or not text.strip():
        raise ValueError("Text cannot be empty.")

    embedding = model.encode(
        text,
        convert_to_numpy=True,
        normalize_embeddings=True
    )

    return embedding.astype("float32")


def embed_texts(texts: list[str]) -> np.ndarray:
    """
    Generate embeddings for multiple texts.

    Returns:
        numpy.ndarray of shape (N, 384)
    """

    if not texts:
        raise ValueError("Text list cannot be empty.")

    embeddings = model.encode(
        texts,
        convert_to_numpy=True,
        normalize_embeddings=True
    )

    return embeddings.astype("float32")