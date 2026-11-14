
from app.hybrid_search import hybrid_search

QUESTIONS = [
    "What functions are available in Python collections module?",
    "What is the purpose of collections.Counter and how is it used?",
    "What is the signature of pathlib.Path.read_text?",
    "How does itertools.combinations work and what arguments does it accept?",
    "Which Python version introduced functools.cache and how does it differ from lru_cache?",
    "What are all the pathlib changes in Python 3.15 release notes?",
    "Is datetime.datetime.strptime deprecated and what do the official docs say?",
    "Show the official documentation for json.dumps.",
    "Which modules in the dataset contain file-handling functions?",
    "Where can I find regex-related functions in the Python documentation?",
]


def main():
    output = ["# Hybrid Search Evaluation", ""]

    for index, question in enumerate(QUESTIONS, start=1):
        print(f"\nEvaluating Q{index}: {question}")

        results = hybrid_search(question, limit=5)

        output.append(f"## Q{index}: {question}")
        output.append("")

        for rank, result in enumerate(results, start=1):
            metadata = result["metadata"]

            output.extend([
                f"### Rank {rank}",
                f"- Source: `{metadata['source']}`",
                f"- Section: {metadata['section']}",
                f"- Hybrid score: {result['hybrid_score']:.5f}",
                f"- Semantic rank: {result['semantic_rank']}",
                f"- Lexical rank: {result['lexical_rank']}",
                "",
                "```text",
                result["text"][:500],
                "```",
                "",
            ])

        output.extend([
            "- [ ] Relevant result found?",
            "- [ ] Correct source and section?",
            "- [ ] Sufficient context to answer?",
            "",
            "---",
            "",
        ])

    with open(
        "eval/hybrid_search_results.md",
        "w",
        encoding="utf-8",
    ) as file:
        file.write("\n".join(output))

    print("\nEvaluation saved to eval/hybrid_search_results.md")


if __name__ == "__main__":
    main()
