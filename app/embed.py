
from sentence_transformers import SentenceTransformer


MODEL_NAME = "all-MiniLM-L6-v2"

# Load the embedding model.
# The model is downloaded the first time this code runs.
_model = None


def get_model():
    """Load the embedding model once and reuse it."""
    global _model

    if _model is None:
        print(f"Loading embedding model: {MODEL_NAME}")
        _model = SentenceTransformer(MODEL_NAME)
        print("Embedding model loaded successfully.")

    return _model


def embed_texts(texts: list[str]) -> list[list[float]]:
    """
    Convert a list of text strings into numerical embeddings.

    Returns:
        A list of vectors, with one 384-dimensional vector per text.
    """
    if not texts:
        return []

    model = get_model()

    embeddings = model.encode(
        texts,
        batch_size=32,
        show_progress_bar=True,
        normalize_embeddings=True,
    )

    return embeddings.tolist()


def embed_query(query: str) -> list[float]:
    """Convert a single search query into an embedding."""
    if not query.strip():
        raise ValueError("Query cannot be empty.")

    model = get_model()

    embedding = model.encode(
        query,
        normalize_embeddings=True,
    )

    return embedding.tolist()


if __name__ == "__main__":
    sample_texts = [
        "The collections module provides container datatypes.",
        "The pathlib module provides object-oriented filesystem paths.",
        "Python dictionaries store key-value pairs.",
    ]

    vectors = embed_texts(sample_texts)

    print("\nEmbedding results:")
    print(f"Number of texts: {len(vectors)}")
    print(f"Vector dimensions: {len(vectors[0])}")
    print(f"First vector sample: {vectors[0][:5]}")
