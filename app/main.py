import json
import logging
import os
import time
import uuid
from pathlib import Path
from typing import Any, Optional

from fastapi import FastAPI, Header, HTTPException, Query, Request, status
from pydantic import BaseModel, Field

from app.cache import query_cache
from app.graph import resume_langgraph_agent, run_langgraph_agent
from app.hybrid_search import hybrid_search
from app.llm import generate_response, get_last_llm_metrics
from app.rag import GenerationError, run_rag_pipeline
from app.records import get_by_id, load_records
from app.smart_search import smart_search

# Low-memory defaults to prevent OOM on memory-constrained hosting (e.g. Render 512Mi limit)
os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")
os.environ.setdefault("PYTORCH_NO_CUDA_MEMORY_CACHING", "1")

logger = logging.getLogger("pydocspal.api")

app = FastAPI(
    title="PyDocsPal API",
    description="Python Documentation Assistant API with Observability and Caching",
    version="1.0.0",
)


@app.middleware("http")
async def telemetry_middleware(request: Request, call_next):
    """Log per-request telemetry including endpoint, method, status, latency_ms, and tokens."""
    start_time = time.perf_counter()
    response = await call_next(request)
    duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
    llm_metrics = get_last_llm_metrics()
    total_tokens = llm_metrics.get("total_tokens", 0) if llm_metrics else 0

    logger.info(
        "Request telemetry | method=%s | path=%s | status=%d | latency_ms=%.2f | total_tokens=%d",
        request.method,
        request.url.path,
        response.status_code,
        duration_ms,
        total_tokens,
    )
    response.headers["X-Process-Time-Ms"] = str(duration_ms)
    return response


# Documented input limits
MAX_QUESTION_LENGTH = 2000
MAX_AGENT_MESSAGE_LENGTH = 2000
MAX_SEARCH_QUERY_LENGTH = 500


class QuestionRequest(BaseModel):
    question: str = Field(min_length=1, max_length=MAX_QUESTION_LENGTH)


@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "message": "PyDocsPal API is running",
    }


@app.get("/records")
def get_records(limit: int = Query(default=10, ge=1, le=100)):
    records = load_records()
    return {
        "total": len(records),
        "records": records[:limit],
    }


@app.get("/records/{record_id}")
def get_record(record_id: int):
    records = load_records()
    record = get_by_id(records, record_id)

    if record is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Record not found",
        )

    return record


@app.get("/search")
def search_records(q: str = Query(min_length=1, max_length=MAX_SEARCH_QUERY_LENGTH)):
    if len(q) > MAX_SEARCH_QUERY_LENGTH:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Search query exceeds maximum allowed length of {MAX_SEARCH_QUERY_LENGTH} characters",
        )
    query = q.strip()
    if not query:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Search query cannot be empty",
        )

    records = load_records()
    results = smart_search(records, query)

    return {
        "query": query,
        "total_results": len(results),
        "results": results,
    }


@app.post("/questions")
def ask_question(request: QuestionRequest):
    if len(request.question) > MAX_QUESTION_LENGTH:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Question exceeds maximum allowed length of {MAX_QUESTION_LENGTH} characters",
        )
    question = request.question.strip()

    if not question:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Question cannot be empty",
        )

    records = load_records()
    results = smart_search(records, question, limit=5)

    return {
        "question": question,
        "answer": (
            "Relevant documentation records found."
            if results
            else "No relevant documentation found."
        ),
        "results": results,
    }


BASE_DIR = Path(__file__).resolve().parents[1]
PROMPT_DIR = BASE_DIR / "prompts"


class ChatRequest(BaseModel):
    question: str = Field(min_length=1, max_length=MAX_QUESTION_LENGTH)
    task: str = "explain"


class ChatResponse(BaseModel):
    answer: str
    confidence: float = Field(ge=0, le=1)
    follow_up: str


def read_prompt(filename: str) -> str:
    prompt_path = PROMPT_DIR / filename
    return prompt_path.read_text(encoding="utf-8")


@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    if len(request.question) > MAX_QUESTION_LENGTH:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Question exceeds maximum allowed length of {MAX_QUESTION_LENGTH} characters",
        )
    question = request.question.strip()

    if not question:
        raise HTTPException(
            status_code=400,
            detail="Question cannot be empty",
        )

    # Select task prompt
    task_prompts = {
        "explain": "task_explain.txt",
        "compare": "task_compare.txt",
    }

    prompt_file = task_prompts.get(request.task)

    if prompt_file is None:
        raise HTTPException(
            status_code=400,
            detail="Task must be 'explain' or 'compare'",
        )

    # Retrieve relevant documentation
    records = load_records()
    results = smart_search(records, question, limit=5)

    context = json.dumps(
        results,
        indent=2,
        ensure_ascii=False,
    )

    # Load prompts
    system_prompt = read_prompt("system.txt")
    task_prompt = read_prompt(prompt_file)

    user_prompt = (
        task_prompt
        .replace("{question}", question)
        .replace("{context}", context)
    )

    try:
        raw_response = generate_response(
            system_prompt,
            user_prompt,
        )

        data = json.loads(raw_response)

        return ChatResponse(
            answer=data["answer"],
            confidence=data["confidence"],
            follow_up=data["follow_up"],
        )

    except (KeyError, ValueError, TypeError):
        raise HTTPException(
            status_code=502,
            detail="LLM returned an invalid response",
        )

    except RuntimeError as error:
        raise HTTPException(
            status_code=503,
            detail=str(error),
        )

    except Exception as exc:
        print(f"LLM ERROR: {type(exc).__name__}: {exc}")
        raise HTTPException(
            status_code=502,
            detail="LLM provider request failed",
        )


@app.get("/search/semantic")
def semantic_search_endpoint(
    q: str = Query(min_length=1, max_length=MAX_SEARCH_QUERY_LENGTH),
    limit: int = Query(default=5, ge=1, le=20),
    bypass_cache: bool = Query(default=False),
):
    if len(q) > MAX_SEARCH_QUERY_LENGTH:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Search query exceeds maximum allowed length of {MAX_SEARCH_QUERY_LENGTH} characters",
        )
    query = q.strip()

    if not query:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Search query cannot be empty",
        )

    cache_key = query_cache.generate_key("semantic_search", q=query, limit=limit)
    if not bypass_cache and os.getenv("PYDOCSPAL_DISABLE_CACHE") != "1":
        cached_result = query_cache.get(cache_key)
        if cached_result is not None:
            return cached_result

    results = hybrid_search(query, limit=limit)

    response_payload = {
        "query": query,
        "search_type": "hybrid",
        "total_results": len(results),
        "results": [
            {
                "id": result["id"],
                "text": result["text"],
                "source": result["metadata"]["source"],
                "title": result["metadata"]["title"],
                "section": result["metadata"]["section"],
                "page": result["metadata"]["page"],
                "hybrid_score": result["hybrid_score"],
                "semantic_rank": result["semantic_rank"],
                "lexical_rank": result["lexical_rank"],
            }
            for result in results
        ],
    }

    if not bypass_cache and os.getenv("PYDOCSPAL_DISABLE_CACHE") != "1":
        query_cache.set(cache_key, response_payload)

    return response_payload


class Citation(BaseModel):
    source: str
    title: str
    section: str
    page: str


class AskRequest(BaseModel):
    question: str = Field(min_length=1, max_length=MAX_QUESTION_LENGTH)
    top_k: int = Field(default=5, ge=1, le=20)
    python_version: Optional[str] = Field(default="3.12", max_length=20, description="Target Python version for compatibility checks")
    bypass_cache: Optional[bool] = Field(default=False, description="Bypass in-memory response cache")


class AskResponse(BaseModel):
    question: str
    answer: str
    status: str
    citations: list[Citation]
    compatibility: Optional[dict[str, Any]] = None


@app.post("/ask", response_model=AskResponse)
def ask(
    request: AskRequest,
    x_bypass_cache: Optional[str] = Header(default=None),
):
    if len(request.question) > MAX_QUESTION_LENGTH:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Question exceeds maximum allowed length of {MAX_QUESTION_LENGTH} characters",
        )
    question = request.question.strip()
    if not question:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Question cannot be empty",
        )

    bypass = bool(request.bypass_cache) or bool(
        x_bypass_cache and x_bypass_cache.strip().lower() in ("true", "1")
    )
    cache_key = query_cache.generate_key(
        "ask",
        question=question,
        top_k=request.top_k,
        python_version=request.python_version or "3.12",
    )

    if not bypass and os.getenv("PYDOCSPAL_DISABLE_CACHE") != "1":
        cached_result = query_cache.get(cache_key)
        if cached_result is not None:
            return AskResponse(**cached_result)

    try:
        result = run_rag_pipeline(
            question=question,
            top_k=request.top_k,
            python_version=request.python_version or "3.12",
        )
        response_dict = {
            "question": result["question"],
            "answer": result["answer"],
            "status": result["status"],
            "citations": [Citation(**c).model_dump() for c in result["citations"]],
            "compatibility": result.get("compatibility"),
        }

        if not bypass and os.getenv("PYDOCSPAL_DISABLE_CACHE") != "1":
            query_cache.set(cache_key, response_dict)

        return AskResponse(
            question=response_dict["question"],
            answer=response_dict["answer"],
            status=response_dict["status"],
            citations=[Citation(**c) for c in response_dict["citations"]],
            compatibility=response_dict["compatibility"],
        )
    except GenerationError as err:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(err),
        )
    except ValueError as err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(err),
        )
    except Exception as err:
        print(f"RAG ERROR: {type(err).__name__}: {err}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal error during RAG processing",
        )


class AgentToolCall(BaseModel):
    tool: str
    args: dict[str, Any] = {}
    result: Any = None


class AgentCitation(BaseModel):
    source: str
    title: str = "unknown"
    section: str = "unknown"
    page: str = "unknown"


class AgentRequest(BaseModel):
    message: Optional[str] = Field(default=None, max_length=MAX_AGENT_MESSAGE_LENGTH, description="User prompt or question")
    thread_id: Optional[str] = Field(default=None, max_length=128, description="Conversation thread identifier")
    action: Optional[str] = Field(default=None, max_length=32, description="Optional action: 'approve', 'reject', or 'resume'")
    approved: Optional[bool] = Field(default=None, description="Boolean approval decision when resuming")


class AgentResponse(BaseModel):
    thread_id: str
    status: str
    approval_required: bool
    proposed_response: Optional[str] = None
    response: Optional[str] = None
    tool_calls: list[AgentToolCall] = []
    citations: list[AgentCitation] = []
    error: Optional[str] = None


@app.post("/agent", response_model=AgentResponse)
def agent_endpoint(request: AgentRequest):
    """
    Day 9 LangGraph Agent Endpoint with Human Approval.
    Supports:
    1. Starting a new agent conversation thread.
    2. Continuing an existing thread.
    3. Resuming an interrupted approval node with approve/reject decision.
    Stateful conversations and approvals are never cached.
    """
    thread_id = request.thread_id.strip() if request.thread_id and request.thread_id.strip() else str(uuid.uuid4())

    # Check if this is an approval resume request
    is_resume = (
        request.approved is not None
        or (request.action and request.action.strip().lower() in ("approve", "approved", "reject", "rejected", "resume"))
    )

    if is_resume:
        if request.approved is not None:
            is_approved = bool(request.approved)
        elif request.action:
            is_approved = request.action.strip().lower() in ("approve", "approved", "yes", "true")
        else:
            is_approved = False

        try:
            result = resume_langgraph_agent(thread_id=thread_id, approved=is_approved)
            if result.get("error"):
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Agent resume failed: {result['error']}",
                )
            return AgentResponse(
                thread_id=result["thread_id"],
                status=result["status"],
                approval_required=result["approval_required"],
                proposed_response=result.get("proposed_response"),
                response=result.get("response"),
                tool_calls=[AgentToolCall(**tc) for tc in result.get("tool_calls", [])],
                citations=[AgentCitation(**c) for c in result.get("citations", [])],
                error=result.get("error"),
            )
        except ValueError as err:
            logger.warning(
                "Agent resume validation error | thread_id=%s | error=%s",
                thread_id,
                err,
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(err),
            )
        except HTTPException:
            raise
        except Exception as err:
            logger.error(
                "Agent resume failed | thread_id=%s | error_type=%s | error=%s",
                thread_id,
                type(err).__name__,
                err,
                exc_info=True,
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Agent resume failed: {err}",
            )

    # Standard conversation start or continuation
    if request.message and len(request.message) > MAX_AGENT_MESSAGE_LENGTH:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Message exceeds maximum allowed length of {MAX_AGENT_MESSAGE_LENGTH} characters.",
        )

    clean_message = (request.message or "").strip()
    if not clean_message:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Message cannot be empty when starting or continuing a conversation.",
        )

    try:
        result = run_langgraph_agent(message=clean_message, thread_id=thread_id)
        if result.get("error"):
            logger.error(
                "Agent workflow returned error | thread_id=%s | error=%s",
                thread_id,
                result["error"],
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Agent workflow failed: {result['error']}",
            )
        return AgentResponse(
            thread_id=result["thread_id"],
            status=result["status"],
            approval_required=result["approval_required"],
            proposed_response=result.get("proposed_response"),
            response=result.get("response"),
            tool_calls=[AgentToolCall(**tc) for tc in result.get("tool_calls", [])],
            citations=[AgentCitation(**c) for c in result.get("citations", [])],
            error=result.get("error"),
        )
    except ValueError as err:
        logger.warning(
            "Agent workflow validation error | thread_id=%s | error=%s",
            thread_id,
            err,
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(err),
        )
    except HTTPException:
        raise
    except Exception as err:
        logger.error(
            "Agent workflow failed | thread_id=%s | error_type=%s | error=%s",
            thread_id,
            type(err).__name__,
            err,
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Agent workflow failed: {err}",
        )


# =====================================================================
# Observability & Cache Management Endpoints
# =====================================================================

@app.get("/cache/stats")
def get_cache_stats():
    """Return in-memory query cache metrics and hit/miss telemetry."""
    return query_cache.stats()


@app.post("/cache/clear")
def clear_cache():
    """Clear in-memory query cache entries and reset counters."""
    query_cache.clear()
    return {"status": "cleared", "message": "Query cache successfully cleared"}


@app.get("/telemetry")
def get_telemetry():
    """Return the most recent LLM invocation telemetry and cache statistics."""
    return {
        "llm": get_last_llm_metrics(),
        "cache": query_cache.stats(),
    }


if __name__ == "__main__":
    import uvicorn

    server_port = int(os.environ.get("PORT", 8000))
    uvicorn.run("app.main:app", host="0.0.0.0", port=server_port)
