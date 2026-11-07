from fastapi import FastAPI, HTTPException, Query, status
from pydantic import BaseModel

from app.records import load_records, get_by_id
from app.smart_search import smart_search

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