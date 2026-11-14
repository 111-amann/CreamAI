
from pathlib import Path

from app.vectorstore import semantic_search


QUESTIONS = [
    "What functions are available in the Python collections module?",
    "What is the purpose of collections.Counter, and how is it used?",
    "What is the function signature of pathlib.Path.read_text()?",
    "How does itertools.combinations() work, and what arguments does it accept?",
    "Which Python version introduced functools.cache, and how does it differ from functools.lru_cache?",
    "What were all the changes made to the pathlib module in Python 3.15, according to its official release notes?",
    "Is datetime.datetime.strptime() deprecated in Python, and where can I find its official documentation?",
    "Where can I find the official Python documentation for json.dumps()?",
    "Which Python modules in the current PyDocsPal dataset contain file-handling functions?",
    "Can I find Python functions related to regular expressions using PyDocsPal?",
]

PROJECT_ROOT = Path(__file__).resolve().parent.parent
OUTPUT_FILE = PROJECT_ROOT / "eval" / "search_results.md"

TOP_K = 5


def run_evaluation():
    """Run semantic search for all 10 assignment questions."""

    report = [
        "# PyDocsPal - Semantic Search Evaluation",
        "",
        "## Configuration",
        "",
        "- Embedding model: all-MiniLM-L6-v2",
        "- Vector database: ChromaDB",
        "- Similarity metric: Cosine distance",
        "- Results per question: 5",
        "- Total questions: 10",
        "",
        "Lower cosine distance indicates greater vector similarity.",
        "Distance is not a confidence percentage.",
        "",
        "## Search Results",
        "",
    ]

    for number, question in enumerate(QUESTIONS, start=1):
        print(f"\nEvaluating Q{number}: {question}")

        results = semantic_search(
            query=question,
            n_results=TOP_K,
        )

        report.extend([
            f"### Q{number}. {question}",
            "",
        ])

        if not results:
            report.extend([
                "No results retrieved.",
                "",
            ])
            continue

        for rank, result in enumerate(results, start=1):
            metadata = result["metadata"]

            source = metadata.get("source", "unknown")
            title = metadata.get("title", "unknown")
            section = metadata.get("section", "unknown")
            page = metadata.get("page", "unknown")
            distance = result["distance"]

            # Keep the report readable.
            preview = result["text"][:500].strip()
            preview = preview.replace("\n", " ")

            report.extend([
                f"#### Result {rank}",
                "",
                f"- **Source:** `{source}`",
                f"- **Title:** {title}",
                f"- **Section:** {section}",
                f"- **Page:** {page}",
                f"- **Cosine distance:** {distance:.4f}",
                f"- **Relevance:** To be manually evaluated",
                "",
                "**Retrieved text:**",
                "",
                f"> {preview}",
                "",
            ])

        report.extend([
            "**Manual evaluation:**",
            "",
            "- [ ] Relevant",
            "- [ ] Partially relevant",
            "- [ ] Not relevant",
            "",
            "**Notes:**",
            "",
            "",
            "---",
            "",
        ])

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    OUTPUT_FILE.write_text(
        "\n".join(report),
        encoding="utf-8",
    )

    print("\nEvaluation completed.")
    print(f"Report saved to: {OUTPUT_FILE}")


if __name__ == "__main__":
    run_evaluation()
