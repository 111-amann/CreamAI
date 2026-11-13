from fastapi import FastAPI, HTTPException, Query, status
from pydantic import BaseModel

from app.records import load_records, get_by_id
from app.smart_search import smart_search

import json
from pathlib import Path

from pydantic import BaseModel, Field
from fastapi import HTTPException
from app.llm import generate_response

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

    except Exception:
        raise HTTPException(
            status_code=502,
            detail="LLM provider request failed"
        )