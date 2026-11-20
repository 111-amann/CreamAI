import json
import time
from pathlib import Path
from typing import Any

from app.hybrid_search import hybrid_search
from app.llm import generate_response
from app.tools import detect_compatibility_info

BASE_DIR = Path(__file__).resolve().parents[1]
PROMPTS_DIR = BASE_DIR / "prompts"


class GenerationError(Exception):
    """Raised when the LLM provider fails, times out, or returns invalid output."""
    pass


def read_prompt(filename: str) -> str:
    path = PROMPTS_DIR / filename
    return path.read_text(encoding="utf-8")


def format_context(chunks: list[dict]) -> str:
    """Format retrieved documentation chunks into numbered context blocks."""
    if not chunks:
        return "No documentation chunks retrieved."

    context_blocks = []
    for index, chunk in enumerate(chunks, start=1):
        metadata = chunk.get("metadata", {})
        source = metadata.get("source", "unknown")
        title = metadata.get("title", "unknown")
        section = metadata.get("section", "unknown")
        text = chunk.get("text", "").strip()

        block = (
            f"[Document {index}]\n"
            f"Title: {title}\n"
            f"Section: {section}\n"
            f"Source: {source}\n\n"
            f"{text}"
        )
        context_blocks.append(block)

    return "\n\n" + ("=" * 40) + "\n\n".join(context_blocks)


def run_rag_pipeline(
    question: str,
    top_k: int = 5,
    collection_name: str = "pydocspal_docs",
    chunk_size: int = 1800,
    chunk_overlap: int = 250,
    python_version: str = "3.12",
) -> dict[str, Any]:
    """
    Execute the RAG pipeline:
    1. Retrieve relevant chunks using hybrid search.
    2. Format grounded context.
    3. Generate LLM response using strict prompt.
    4. Validate evidence, abstention, and citations.
    """
    clean_question = question.strip()
    if not clean_question:
        raise ValueError("Question cannot be empty.")

    start_total_time = time.perf_counter()

    # 1. Retrieval
    start_retrieval_time = time.perf_counter()
    chunks = hybrid_search(
        clean_question,
        limit=top_k,
        collection_name=collection_name,
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
    )
    retrieval_latency = time.perf_counter() - start_retrieval_time

    # If no chunks were retrieved at all, evidence is immediately insufficient.
    if not chunks:
        total_latency = time.perf_counter() - start_total_time
        return {
            "question": clean_question,
            "answer": "I don't know",
            "status": "insufficient_evidence",
            "citations": [],
            "compatibility": None,
            "retrieval_latency": round(retrieval_latency, 4),
            "total_latency": round(total_latency, 4),
            "retrieved_chunks": [],
        }

    # 2. Context formatting
    context_str = format_context(chunks)

    # 3. Prompt construction
    system_prompt = read_prompt("system_rag.txt")
    task_prompt = read_prompt("task_rag.txt")
    user_prompt = task_prompt.replace("{question}", clean_question).replace("{context}", context_str)

    # 4. LLM Generation
    try:
        raw_response = generate_response(system_prompt, user_prompt)
    except Exception as exc:
        raise GenerationError(f"LLM generation failed: {type(exc).__name__}: {exc}") from exc

    # 5. Parse and Validate LLM Response
    try:
        data = json.loads(raw_response)
        if not isinstance(data, dict):
            raise ValueError("LLM response is not a JSON object")
    except Exception as exc:
        raise GenerationError(f"Malformed LLM JSON output: {raw_response}") from exc

    raw_status = str(data.get("status", "")).strip().lower()
    raw_answer = str(data.get("answer", "")).strip()
    raw_citations = data.get("citation_indices", [])

    if not isinstance(raw_citations, list):
        raw_citations = []

    # Evidence-based abstention detection:
    is_abstention = (
        raw_status == "insufficient_evidence"
        or raw_answer.lower() in ["i don't know", "i don't know.", "i do not know", "i do not know."]
        or ("i don't know" in raw_answer.lower() and len(raw_answer) < 40)
    )

    # Validate citation indices against available chunks
    valid_citation_indices = []
    for idx in raw_citations:
        try:
            int_idx = int(idx)
            if 1 <= int_idx <= len(chunks) and int_idx not in valid_citation_indices:
                valid_citation_indices.append(int_idx)
        except (ValueError, TypeError):
            continue

    total_latency = time.perf_counter() - start_total_time

    # If abstaining, or if status is not answered, or if answered with zero valid citations
    if is_abstention or raw_status != "answered" or not valid_citation_indices:
        return {
            "question": clean_question,
            "answer": "I don't know",
            "status": "insufficient_evidence",
            "citations": [],
            "compatibility": None,
            "retrieval_latency": round(retrieval_latency, 4),
            "total_latency": round(total_latency, 4),
            "retrieved_chunks": chunks,
        }

    # Construct verified citations from the validated chunk indices
    citations = []
    for idx in valid_citation_indices:
        chunk_meta = chunks[idx - 1]["metadata"]
        citations.append({
            "source": chunk_meta.get("source", "unknown"),
            "title": chunk_meta.get("title", "unknown"),
            "section": chunk_meta.get("section", "unknown"),
            "page": chunk_meta.get("page", "unknown"),
        })

    compatibility = detect_compatibility_info(
        question=clean_question,
        answer=raw_answer,
        python_version=python_version,
        citations=citations,
    )

    return {
        "question": clean_question,
        "answer": raw_answer,
        "status": "answered",
        "citations": citations,
        "compatibility": compatibility,
        "retrieval_latency": round(retrieval_latency, 4),
        "total_latency": round(total_latency, 4),
        "retrieved_chunks": chunks,
    }
