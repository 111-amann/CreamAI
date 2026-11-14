
from pathlib import Path
import argparse
import hashlib

import chromadb

from app.chunking import load_all_chunks
from app.embed import embed_texts, embed_query


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


def get_collection(reset: bool = False):
    """Get or create the documentation collection."""

    if reset:
        try:
            client.delete_collection(
                name=COLLECTION_NAME
            )
            print("Existing collection deleted.")
        except Exception:
            pass

    collection = client.get_or_create_collection(
        name=COLLECTION_NAME,
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


def build_index(reset: bool = False):
    """
    Load documentation chunks, generate embeddings,
    and store everything in ChromaDB.
    """

    print("Loading documentation chunks...")

    chunks = load_all_chunks()

    if not chunks:
        print("No documentation chunks found.")
        return

    print(f"Total chunks loaded: {len(chunks)}")

    collection = get_collection(reset=reset)

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
    print(f"Collection: {COLLECTION_NAME}")
    print(f"Stored documents: {collection.count()}")
    print(f"Database location: {CHROMA_DIR}")


def semantic_search(query: str, n_results: int = 5):
    """Search documentation using semantic similarity."""

    if not query or not query.strip():
        raise ValueError("Search query cannot be empty.")

    if n_results < 1:
        raise ValueError("n_results must be at least 1.")

    collection = get_collection()

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
