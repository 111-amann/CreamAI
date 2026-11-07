from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


def get_search_text(record):
    """Combine searchable fields into one text string."""

    fields = [
        record.get("module", ""),
        record.get("name", ""),
        record.get("kind", ""),
        record.get("signature", ""),
        record.get("summary", ""),
        record.get("version_note", "")
    ]

    return " ".join(str(field) for field in fields)


def smart_search(records, query, limit=10):

    if not records or not query.strip():
        return []

    documents = [get_search_text(record) for record in records]

    vectorizer = TfidfVectorizer()

    try:
        document_vectors = vectorizer.fit_transform(documents)
        query_vector = vectorizer.transform([query])

        scores = cosine_similarity(
            query_vector,
            document_vectors
        ).flatten()

    except ValueError:
        return []

    results = []

    for index, score in enumerate(scores):
        if score > 0:
            result = records[index].copy()
            result["score"] = round(float(score), 4)
            results.append(result)

    results.sort(
        key=lambda item: item["score"],
        reverse=True
    )

    return results[:limit]