"""
tests/test_day11_suite.py - Day 11 Comprehensive Pytest Suite for PyDocsPal.

Covers:
1. Records loading, lookup, counting, filtering, and model serialization (app.records, app.models).
2. Smart search and hybrid search offline with mocked semantic retrieval (app.smart_search, app.hybrid_search).
3. FastAPI endpoints via TestClient:
   - GET /health
   - GET /records (pagination and 404)
   - GET /search
   - POST /ask (mocked LLM: answered vs. abstention behavior, validation)
   - POST /agent (request validation)
4. Agent tools: stdlib_version_check and execute_rag_search (app.tools, app.agent_loop).
"""

import sys
from pathlib import Path
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.agent_loop import execute_rag_search, execute_stdlib_version_check
from app.hybrid_search import hybrid_search
from app.main import app
from app.models import Record
from app.records import count_by, get_by_id, load_records, search
from app.smart_search import smart_search
from app.tools import stdlib_version_check


@pytest.fixture(scope="module")
def client():
    """Shared FastAPI test client."""
    return TestClient(app)


# =====================================================================
# 1. Records and Model Tests
# =====================================================================

def test_record_dataclass_and_to_dict():
    """Verify Record model attributes and dictionary conversion."""
    rec = Record(
        id=101,
        module="pathlib",
        name="Path.read_text",
        kind="method",
        signature="read_text(encoding=None, errors=None)",
        summary="Open the file in text mode, read it, and close the file.",
        version_note="Added in version 3.5.",
    )
    data = rec.to_dict()
    assert data["id"] == 101
    assert data["module"] == "pathlib"
    assert data["name"] == "Path.read_text"
    assert data["kind"] == "method"
    assert "encoding=None" in data["signature"]
    assert "Open the file" in data["summary"]
    assert "3.5" in data["version_note"]


def test_records_loading_and_lookup():
    """Verify loading documentation records and finding by ID."""
    records = load_records()
    assert isinstance(records, list)
    assert len(records) > 0

    first_record = records[0]
    first_id = first_record["id"]

    found = get_by_id(records, first_id)
    assert found is not None
    assert found["id"] == first_id

    missing = get_by_id(records, -99999)
    assert missing is None


def test_records_count_by_grouping():
    """Verify grouping records by category field."""
    sample_records = [
        {"id": 1, "kind": "function", "module": "math"},
        {"id": 2, "kind": "function", "module": "math"},
        {"id": 3, "kind": "class", "module": "pathlib"},
    ]
    counts = count_by(sample_records, category="kind")
    assert counts == {"function": 2, "class": 1}

    mod_counts = count_by(sample_records, category="module")
    assert mod_counts == {"math": 2, "pathlib": 1}


def test_records_keyword_filtering():
    """Verify keyword filtering across documentation records."""
    sample_records = [
        {"id": 1, "module": "pathlib", "name": "Path.mkdir", "kind": "method", "signature": "mkdir()", "summary": "Create directory", "version_note": "3.4"},
        {"id": 2, "module": "os", "name": "listdir", "kind": "function", "signature": "listdir(path)", "summary": "Return names in directory", "version_note": ""},
        {"id": 3, "module": "math", "name": "sqrt", "kind": "function", "signature": "sqrt(x)", "summary": "Square root", "version_note": ""},
    ]
    results = search(sample_records, "directory")
    assert len(results) == 2
    assert {r["name"] for r in results} == {"Path.mkdir", "listdir"}

    empty_results = search(sample_records, "   ")
    assert empty_results == []


# =====================================================================
# 2. Search Functionality Tests
# =====================================================================

def test_smart_search_ranking():
    """Verify TF-IDF smart search scoring and ranking."""
    sample_records = [
        {"id": 1, "module": "pathlib", "name": "Path.write_text", "kind": "method", "signature": "write_text(data)", "summary": "Write data to file", "version_note": "3.5"},
        {"id": 2, "module": "pathlib", "name": "Path.read_text", "kind": "method", "signature": "read_text()", "summary": "Read file contents", "version_note": "3.5"},
        {"id": 3, "module": "math", "name": "sin", "kind": "function", "signature": "sin(x)", "summary": "Sine of x", "version_note": ""},
    ]
    results = smart_search(sample_records, "read file contents", limit=2)
    assert len(results) > 0
    assert results[0]["name"] == "Path.read_text"
    assert "score" in results[0]
    assert results[0]["score"] > 0

    assert smart_search(sample_records, "") == []
    assert smart_search([], "path") == []


def test_hybrid_search_rrf_offline():
    """Verify hybrid search RRF logic with mocked semantic and lexical retrieval."""
    mock_semantic = [
        {"id": "doc1", "text": "Path.mkdir creates directory", "metadata": {"source": "pathlib.txt", "title": "Pathlib", "section": "Path.mkdir", "page": "1"}},
        {"id": "doc2", "text": "Path.rmdir removes directory", "metadata": {"source": "pathlib.txt", "title": "Pathlib", "section": "Path.rmdir", "page": "1"}},
    ]
    mock_lexical = [
        {"id": "doc1", "text": "Path.mkdir creates directory", "metadata": {"source": "pathlib.txt", "title": "Pathlib", "section": "Path.mkdir", "page": "1"}},
        {"id": "doc3", "text": "os.mkdir creates directory", "metadata": {"source": "os.txt", "title": "OS", "section": "mkdir", "page": "1"}},
    ]

    with patch("app.hybrid_search.semantic_search", return_value=mock_semantic), \
         patch("app.hybrid_search.lexical_search", return_value=mock_lexical):
        results = hybrid_search("create directory", limit=3)
        assert len(results) == 3
        # doc1 appears in both lists, so it must have highest RRF score
        assert results[0]["id"] == "doc1"
        assert results[0]["hybrid_score"] > results[1]["hybrid_score"]
        assert "metadata" in results[0]
        assert results[0]["metadata"]["source"] == "pathlib.txt"


# =====================================================================
# 3. FastAPI Endpoint Tests
# =====================================================================

def test_health_check_endpoint(client):
    """Verify GET /health returns 200 and expected healthy message."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "PyDocsPal API" in data["message"]


def test_records_endpoints_and_404(client):
    """Verify GET /records pagination and GET /records/{id} behavior."""
    # List endpoint with limit
    res_list = client.get("/records?limit=3")
    assert res_list.status_code == 200
    list_data = res_list.json()
    assert "total" in list_data
    assert len(list_data["records"]) == 3

    first_record = list_data["records"][0]
    rec_id = first_record["id"]

    # Detail endpoint
    res_detail = client.get(f"/records/{rec_id}")
    assert res_detail.status_code == 200
    detail_data = res_detail.json()
    assert detail_data["id"] == rec_id

    # 404 for missing record
    res_missing = client.get("/records/99999999")
    assert res_missing.status_code == 404
    assert res_missing.json()["detail"] == "Record not found"


def test_search_endpoint(client):
    """Verify GET /search performs query lookup."""
    response = client.get("/search?q=pathlib")
    assert response.status_code == 200
    data = response.json()
    assert data["query"] == "pathlib"
    assert "total_results" in data
    assert isinstance(data["results"], list)


def test_ask_endpoint_answered_mocked_llm(client):
    """Verify POST /ask handles successful answered query with mocked LLM and citations."""
    mock_llm_json = '{"status": "answered", "answer": "Path.mkdir creates a new directory.", "citation_indices": [1]}'
    mock_chunks = [
        {
            "id": "c1",
            "text": "Path.mkdir(mode=0o777, parents=False, exist_ok=False) creates directory.",
            "metadata": {
                "source": "library/pathlib.txt",
                "title": "Pathlib",
                "section": "Path.mkdir",
                "page": "1",
            },
        }
    ]

    with patch("app.rag.generate_response", return_value=mock_llm_json), \
         patch("app.rag.hybrid_search", return_value=mock_chunks):
        response = client.post(
            "/ask",
            json={"question": "How to make a directory with Pathlib?", "top_k": 3, "python_version": "3.12"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["question"] == "How to make a directory with Pathlib?"
        assert data["status"] == "answered"
        assert "creates a new directory" in data["answer"]
        assert len(data["citations"]) == 1
        assert data["citations"][0]["source"] == "library/pathlib.txt"
        assert data["citations"][0]["section"] == "Path.mkdir"
        assert "compatibility" in data


def test_ask_endpoint_abstention_behavior(client):
    """Verify POST /ask abstains correctly when LLM returns insufficient evidence."""
    mock_llm_json = '{"status": "insufficient_evidence", "answer": "I don\'t know", "citation_indices": []}'
    mock_chunks = [
        {
            "id": "c1",
            "text": "Some unrelated documentation.",
            "metadata": {
                "source": "library/other.txt",
                "title": "Other",
                "section": "other",
                "page": "1",
            },
        }
    ]

    with patch("app.rag.generate_response", return_value=mock_llm_json), \
         patch("app.rag.hybrid_search", return_value=mock_chunks):
        response = client.post(
            "/ask",
            json={"question": "What is quantum teleportation?", "top_k": 3},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "insufficient_evidence"
        assert data["answer"] == "I don't know"
        assert data["citations"] == []


def test_ask_endpoint_empty_question_validation(client):
    """Verify POST /ask returns 400 when question is empty or whitespace."""
    response = client.post("/ask", json={"question": "   "})
    assert response.status_code == 400
    assert "empty" in response.json()["detail"].lower()


# =====================================================================
# 4. Agent Tools and Dispatch Tests
# =====================================================================

def test_stdlib_version_check_available_symbol():
    """Verify deterministic version check tool for introduced symbol."""
    res = stdlib_version_check(symbol="pathlib.Path.mkdir", python_version="3.8")
    assert res["status"] == "available"
    assert res["available"] is True
    assert res["symbol"] == "pathlib.Path.mkdir"
    assert res["introduced_in"] == "3.4"


def test_stdlib_version_check_not_yet_available():
    """Verify deterministic version check for symbol introduced in a later version."""
    # functools.cache was introduced in Python 3.9
    res = stdlib_version_check(symbol="functools.cache", python_version="3.8")
    assert res["status"] == "not_yet_available"
    assert res["available"] is False
    assert res["introduced_in"] == "3.9"


def test_execute_stdlib_version_check_helper():
    """Verify agent loop helper execute_stdlib_version_check."""
    res = execute_stdlib_version_check("pathlib.Path.mkdir", "3.12")
    assert isinstance(res, dict)
    assert res.get("status") == "available"
    assert res.get("available") is True


def test_execute_rag_search_helper_mocked():
    """Verify execute_rag_search helper with mocked hybrid_search."""
    mock_chunks = [
        {
            "id": "c1",
            "text": "functools.lru_cache memoizes a callable.",
            "metadata": {
                "source": "library/functools.txt",
                "title": "Functools",
                "section": "lru_cache",
                "page": "1",
            },
        }
    ]
    with patch("app.agent_loop.hybrid_search", return_value=mock_chunks):
        res = execute_rag_search(query="functools lru_cache", top_k=2)
        assert isinstance(res, dict)
        assert "results_count" in res
        assert res["results_count"] == 1
        assert len(res["citations"]) == 1
        assert res["citations"][0]["section"] == "lru_cache"
        assert len(res["chunks"]) == 1
        assert "memoizes a callable" in res["chunks"][0]["text"]


def test_agent_endpoint_empty_message_validation(client):
    """Verify POST /agent rejects empty input message."""
    response = client.post("/agent", json={"message": "   "})
    assert response.status_code == 400
    assert "empty" in response.json()["detail"].lower()
