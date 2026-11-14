
import re
from functools import lru_cache

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from app.chunking import load_all_chunks
from app.vectorstore import semantic_search, create_unique_id


# Number of results retrieved from each search method.
RETRIEVAL_LIMIT = 10

# RRF constant.
RRF_K = 60

# Supported Python documentation modules.
SUPPORTED_MODULES = (
    "pathlib",
    "collections",
    "itertools",
    "functools",
)


@lru_cache(maxsize=1)
def load_lexical_index():
    """Load documentation chunks and build a cached TF-IDF index."""

    print("Building lexical search index...")

    chunks = load_all_chunks()

    if not chunks:
        return [], None, None

    documents = [chunk["text"] for chunk in chunks]

    vectorizer = TfidfVectorizer(
        stop_words="english",
        ngram_range=(1, 2),
        sublinear_tf=True,
    )

    document_vectors = vectorizer.fit_transform(documents)

    print(f"Lexical index ready: {len(chunks)} chunks")

    return chunks, vectorizer, document_vectors


def extract_api_name(query: str) -> str:
    """Extract an API name such as pathlib.Path.read_text."""

    module_pattern = "|".join(SUPPORTED_MODULES)

    pattern = (
        rf"\b(?:{module_pattern})\."
        r"([A-Za-z_]\w*(?:\.[A-Za-z_]\w*)?)"
    )

    match = re.search(pattern, query, re.IGNORECASE)

    return match.group(1) if match else ""


def lexical_search(query: str, limit: int = RETRIEVAL_LIMIT):
    """Search documentation using TF-IDF and API signature boosting."""

    if not query or not query.strip():
        raise ValueError("Search query cannot be empty.")

    if limit < 1:
        raise ValueError("Limit must be at least 1.")

    chunks, vectorizer, document_vectors = load_lexical_index()

    if not chunks:
        return []

    try:
        query_vector = vectorizer.transform([query])

        scores = cosine_similarity(
            query_vector,
            document_vectors,
        ).flatten()

    except ValueError:
        return []

    api_name = extract_api_name(query)

    # Match the API name followed by its signature parentheses.
    signature_pattern = (
        re.escape(api_name) + r"\s*\([^)]*\)"
        if api_name
        else None
    )

    results = []

    for index, score in enumerate(scores):

        score = float(score)
        chunk = chunks[index]

        if signature_pattern and re.search(
            signature_pattern,
            chunk["text"],
            re.IGNORECASE,
        ):
            score *= 5.0

        if score <= 0:
            continue

        results.append({
            "id": create_unique_id(chunk),
            "text": chunk["text"],
            "metadata": {
                "source": str(chunk["source"]),
                "page": str(chunk["page"]),
                "title": str(chunk["title"]),
                "section": str(chunk["section"]),
                "chunk_index": int(chunk["chunk_index"]),
            },
            "lexical_score": round(score, 4),
        })

    results.sort(
        key=lambda item: item["lexical_score"],
        reverse=True,
    )

    return results[:limit]


def reciprocal_rank_fusion(
    semantic_results: list,
    lexical_results: list,
    limit: int = 10,
):
    """Combine semantic and lexical rankings using RRF."""

    combined = {}

    search_groups = [
        ("semantic", semantic_results),
        ("lexical", lexical_results),
    ]

    for search_type, results in search_groups:

        for rank, result in enumerate(results, start=1):

            result_id = result["id"]

            if result_id not in combined:
                combined[result_id] = {
                    **result,
                    "hybrid_score": 0.0,
                    "semantic_rank": None,
                    "lexical_rank": None,
                }

            combined[result_id]["hybrid_score"] += (
                1 / (RRF_K + rank)
            )

            combined[result_id][f"{search_type}_rank"] = rank

            if search_type == "semantic":
                combined[result_id]["distance"] = result.get(
                    "distance"
                )

            if search_type == "lexical":
                combined[result_id]["lexical_score"] = result.get(
                    "lexical_score"
                )

    ranked_results = sorted(
        combined.values(),
        key=lambda item: item["hybrid_score"],
        reverse=True,
    )

    return ranked_results[:limit]


def hybrid_search(query: str, limit: int = 5):
    """Search documentation using semantic and lexical retrieval."""

    if not query or not query.strip():
        raise ValueError("Search query cannot be empty.")

    if limit < 1:
        raise ValueError("Limit must be at least 1.")

    semantic_results = semantic_search(
        query,
        n_results=RETRIEVAL_LIMIT,
    )

    lexical_results = lexical_search(
        query,
        limit=RETRIEVAL_LIMIT,
    )

    return reciprocal_rank_fusion(
        semantic_results,
        lexical_results,
        limit=limit,
    )


if __name__ == "__main__":

    query = "What is the signature of pathlib.Path.read_text?"

    print(f"\nQuery: {query}")

    results = hybrid_search(query, limit=5)

    for rank, result in enumerate(results, start=1):

        print(f"\nRank: {rank}")
        print(f"Source: {result['metadata']['source']}")
        print(f"Section: {result['metadata']['section']}")
        print(f"Hybrid score: {result['hybrid_score']:.5f}")
        print(f"Semantic rank: {result['semantic_rank']}")
        print(f"Lexical rank: {result['lexical_rank']}")
        print(f"Text: {result['text'][:300]}")
