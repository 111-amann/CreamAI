import json
from pathlib import Path
from typing import Any, Optional

from app.rag import run_rag_pipeline, GenerationError
from fastapi import FastAPI, HTTPException, Query, status
from pydantic import BaseModel, Field

from app.records import load_records, get_by_id
from app.smart_search import smart_search
from app.llm import generate_response
from app.hybrid_search import hybrid_search

app = FastAPI(
    title="PyDocsPal API",
    description="Python Documentation Assistant API",
    version="1.0.0"
)


class QuestionRequest(BaseModel):
    question: str


@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "message": "PyDocsPal API is running"
    }


@app.get("/records")
def get_records(limit: int = Query(default=10, ge=1, le=100)):
    records = load_records()
    return {
        "total": len(records),
        "records": records[:limit]
    }


@app.get("/records/{record_id}")
def get_record(record_id: int):
    records = load_records()
    record = get_by_id(records, record_id)

    if record is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Record not found"
        )

    return record


@app.get("/search")
def search_records(q: str = Query(min_length=1)):
    records = load_records()
    results = smart_search(records, q)

    return {
        "query": q,
        "total_results": len(results),
        "results": results
    }


@app.post("/questions")
def ask_question(request: QuestionRequest):
    question = request.question.strip()

    if not question:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Question cannot be empty"
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
        "results": results
    }

BASE_DIR = Path(__file__).resolve().parents[1]
PROMPT_DIR = BASE_DIR / "prompts"


class ChatRequest(BaseModel):
    question: str = Field(min_length=1, max_length=2000)
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

    question = request.question.strip()

    if not question:
        raise HTTPException(
            status_code=400,
            detail="Question cannot be empty"
        )

    # Select task prompt
    task_prompts = {
        "explain": "task_explain.txt",
        "compare": "task_compare.txt"
    }

    prompt_file = task_prompts.get(request.task)

    if prompt_file is None:
        raise HTTPException(
            status_code=400,
            detail="Task must be 'explain' or 'compare'"
        )

    # Retrieve relevant documentation
    records = load_records()
    results = smart_search(records, question, limit=5)

    context = json.dumps(
        results,
        indent=2,
        ensure_ascii=False
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
            user_prompt
        )

        data = json.loads(raw_response)

        return ChatResponse(
            answer=data["answer"],
            confidence=data["confidence"],
            follow_up=data["follow_up"]
        )

    except (KeyError, ValueError, TypeError):
        raise HTTPException(
            status_code=502,
            detail="LLM returned an invalid response"
        )

    except RuntimeError as error:
        raise HTTPException(
            status_code=503,
            detail=str(error)
        )

    # except Exception:
    #     raise HTTPException(
    #         status_code=502,
    #         detail="LLM provider request failed"
    #     )

    except Exception as exc:
        print(f"LLM ERROR: {type(exc).__name__}: {exc}")
        raise HTTPException(
            status_code=502,
            detail="LLM provider request failed"
    )

@app.get("/search/semantic")
def semantic_search_endpoint(
    q: str = Query(min_length=1, max_length=500),
    limit: int = Query(default=5, ge=1, le=20)
):
    query = q.strip()

    if not query:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Search query cannot be empty"
        )

    results = hybrid_search(query, limit=limit)

    return {
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
                "lexical_rank": result["lexical_rank"]
            }
            for result in results
        ]
    }

class Citation(BaseModel):
    source: str
    title: str
    section: str
    page: str


class AskRequest(BaseModel):
    question: str = Field(min_length=1, max_length=2000)
    top_k: int = Field(default=5, ge=1, le=20)
    python_version: Optional[str] = Field(default="3.12", description="Target Python version for compatibility checks")


class AskResponse(BaseModel):
    question: str
    answer: str
    status: str
    citations: list[Citation]
    compatibility: Optional[dict[str, Any]] = None


@app.post("/ask", response_model=AskResponse)
def ask(request: AskRequest):
    question = request.question.strip()
    if not question:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Question cannot be empty"
        )

    try:
        result = run_rag_pipeline(
            question=question,
            top_k=request.top_k,
            python_version=request.python_version or "3.12",
        )
        return AskResponse(
            question=result["question"],
            answer=result["answer"],
            status=result["status"],
            citations=[Citation(**c) for c in result["citations"]],
            compatibility=result.get("compatibility"),
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


import uuid
from typing import Any, Optional
from app.graph import run_langgraph_agent, resume_langgraph_agent


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
    message: Optional[str] = Field(default=None, description="User prompt or question")
    thread_id: Optional[str] = Field(default=None, description="Conversation thread identifier")
    action: Optional[str] = Field(default=None, description="Optional action: 'approve', 'reject', or 'resume'")
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
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(err),
            )
        except HTTPException:
            raise
        except Exception as err:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Agent resume failed: {err}",
            )

    # Standard conversation start or continuation
    clean_message = (request.message or "").strip()
    if not clean_message:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Message cannot be empty when starting or continuing a conversation.",
        )

    try:
        result = run_langgraph_agent(message=clean_message, thread_id=thread_id)
        if result.get("error"):
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
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(err),
        )
    except HTTPException:
        raise
    except Exception as err:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Agent workflow failed: {err}",
        )
