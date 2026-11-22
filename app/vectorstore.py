
import argparse
import hashlib
from pathlib import Path

import chromadb

from app.chunking import load_all_chunks
from app.embed import embed_query, embed_texts

# Persistent ChromaDB storage
PROJECT_ROOT = Path(__file__).resolve().parent.parent
CHROMA_DIR = PROJECT_ROOT / "data" / "chroma_db"

COLLECTION_NAME = "pydocspal_docs"

# Process a limited number of chunks at a time.
BATCH_SIZE = 128

# Initialize persistent ChromaDB client.
client = chromadb.PersistentClient(
    path=str(CHROMA_DIR)
)


def get_collection(collection_name: str = COLLECTION_NAME, reset: bool = False):
    """Get or create the documentation collection."""

    if reset:
        try:
            client.delete_collection(
                name=collection_name
            )
            print(f"Existing collection '{collection_name}' deleted.")
        except Exception:
            pass

    collection = client.get_or_create_collection(
        name=collection_name,
        metadata={
            "description": "Python documentation embeddings",
            "hnsw:space": "cosine",
        },
    )

    return collection


def create_unique_id(chunk: dict) -> str:
    """Create a deterministic ID using source path and chunk index."""

    source = chunk["source"]
    chunk_index = chunk["chunk_index"]

    source_hash = hashlib.sha1(
        source.encode("utf-8")
    ).hexdigest()[:12]

    return f"{source_hash}_{chunk_index}"


def build_index(
    collection_name: str = COLLECTION_NAME,
    chunks: list[dict] = None,
    reset: bool = False,
):
    """
    Load documentation chunks, generate embeddings,
    and store everything in ChromaDB.
    """

    print(f"Loading documentation chunks for {collection_name}...")

    if chunks is None:
        chunks = load_all_chunks()

    if not chunks:
        print("No documentation chunks found.")
        return

    print(f"Total chunks loaded: {len(chunks)}")

    collection = get_collection(collection_name=collection_name, reset=reset)

    print("\nStarting vector indexing...")

    total_chunks = len(chunks)

    for start in range(0, total_chunks, BATCH_SIZE):
        batch = chunks[start:start + BATCH_SIZE]

        texts = [
            chunk["text"]
            for chunk in batch
        ]

        # Generate embeddings for this batch.
        embeddings = embed_texts(texts)

        # Generate unique IDs.
        ids = [
            create_unique_id(chunk)
            for chunk in batch
        ]

        # ChromaDB metadata must contain supported scalar values.
        metadatas = [
            {
                "source": str(chunk["source"]),
                "page": str(chunk["page"]),
                "title": str(chunk["title"]),
                "section": str(chunk["section"]),
                "chunk_index": int(chunk["chunk_index"]),
            }
            for chunk in batch
        ]

        # Insert or update records.
        collection.upsert(
            ids=ids,
            embeddings=embeddings,
            documents=texts,
            metadatas=metadatas,
        )

        processed = min(
            start + len(batch),
            total_chunks,
        )

        print(
            f"Indexed {processed}/{total_chunks} chunks"
        )

    print("\nIndexing completed.")
    print(f"Collection: {collection_name}")
    print(f"Stored documents: {collection.count()}")
    print(f"Database location: {CHROMA_DIR}")

    try:
        from app.tools import build_stdlib_versions_csv
        print("Ensuring standard library version metadata CSV is up to date...")
        count = build_stdlib_versions_csv()
        print(f"Version metadata ready: {count} records in data/stdlib_versions.csv")
    except Exception as exc:
        print(f"Notice: Version extraction skipped during vector indexing: {exc}")


def semantic_search(
    query: str,
    n_results: int = 5,
    collection_name: str = COLLECTION_NAME,
):
    """Search documentation using semantic similarity."""

    if not query or not query.strip():
        raise ValueError("Search query cannot be empty.")

    if n_results < 1:
        raise ValueError("n_results must be at least 1.")

    collection = get_collection(collection_name=collection_name)

    total_documents = collection.count()

    if total_documents == 0:
        return []

    # Convert the search query into a vector.
    query_embedding = embed_query(query)

    # Avoid requesting more results than the collection contains.
    result_count = min(n_results, total_documents)

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=result_count,
        include=[
            "documents",
            "metadatas",
            "distances",
        ],
    )

    matches = []

    for index in range(len(results["ids"][0])):
        matches.append(
            {
                "id": results["ids"][0][index],
                "text": results["documents"][0][index],
                "metadata": results["metadatas"][0][index],
                "distance": results["distances"][0][index],
            }
        )

    return matches


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Build the PyDocsPal ChromaDB vector index."
    )

    parser.add_argument(
        "--reset",
        action="store_true",
        help="Delete the existing collection before rebuilding.",
    )

    args = parser.parse_args()

    build_index(reset=args.reset)
