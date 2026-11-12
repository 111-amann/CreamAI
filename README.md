# PyDocsPal 🐍

### Your Python Documentation Assistant

PyDocsPal is a Python documentation assistant designed to help developers and students understand Python functions, classes, modules, signatures, and version compatibility using official Python documentation.

## 📌 Project Card

**Product:** PyDocsPal

**User:** Python developers, students, and programmers who need quick and reliable information about Python functions, modules, and classes.

**Problem:** Finding accurate information about Python APIs, understanding their usage, checking Python version compatibility, and identifying deprecated or removed features can take time. Python documentation also changes between versions.

**Solution:** PyDocsPal simplifies Python documentation discovery by organizing official documentation into searchable records and providing relevant results through a FastAPI service.

**Data Source:** [Official Python Documentation](https://docs.python.org/3/)

## ✨ Core Features

- Search Python functions, modules, and classes.
- Understand function signatures and usage.
- Check Python version compatibility.
- Identify deprecated and removed APIs.
- Retrieve relevant documentation records.
- Organize documentation into structured JSON records.
- Search documentation using TF-IDF and cosine similarity.
- Access documentation through REST API endpoints.
- Analyze documentation records using Pandas.

**Signature Feature:** Every answer is intended to display a Python version compatibility badge and warnings for deprecated or removed APIs.

## 🛠️ Tech Stack

### Current Implementation

- Python
- FastAPI
- Uvicorn
- Pandas
- Scikit-learn
- TF-IDF
- Cosine Similarity
- JSON
- Requests
- Dataclasses
- pathlib
- Regular Expressions
- Git and GitHub

### Planned Technologies

- Groq / Gemini API
- Embeddings
- ChromaDB
- Retrieval-Augmented Generation (RAG)
- Streamlit
- Large Language Models (LLMs)

## 📂 Project Structure

```text
PyDocsPal/
│
├── analysis/
│   ├── __init__.py
│   └── explore.py
│
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── records.py
│   ├── smart_search.py
│   ├── cli.py
│   ├── ingest.py
│   ├── models.py
│   └── fetch.py
│
├── data/
│   ├── raw/
│   └── records.json
│
├── docs/
│   ├── how_llms_work.md
│   └── user_questions.md
│
├── day01_intro.py
├── day01_menu.py
├── README.md
├── requirements.txt
└── .gitignore
```

## 🚀 How to Run

### 1. Clone the repository

```bash
git clone https://github.com/111-amann/CreamAI.git
cd CreamAI
```

### 2. Create a virtual environment

```bash
python -m venv .venv
```

### 3. Activate the virtual environment

Windows PowerShell:

```powershell
.venv\Scripts\Activate.ps1
```

### 4. Install dependencies

```bash
pip install -r requirements.txt
```

### 5. Run the CLI application

```bash
python -m app.cli
```

### 6. Download documentation pages

```bash
python -m app.fetch
```

### 7. Ingest documentation

```bash
python -m app.ingest
```

### 8. Run data analysis

```bash
python -m analysis.explore
```

### 9. Start the FastAPI server

```bash
uvicorn app.main:app --reload
```

The API will be available at:

http://127.0.0.1:8000

### 10. Explore API documentation

Open the interactive Swagger UI:

http://127.0.0.1:8000/docs

## 🔗 API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | `/health` | Check API health |
| GET | `/records?limit=10` | Retrieve documentation records |
| GET | `/records/{id}` | Retrieve a record by ID |
| GET | `/search?q=python` | Search documentation using TF-IDF |
| POST | `/questions` | Submit a documentation question and retrieve relevant records |

### Example API Request

**POST `/questions`**

Request body:

```json
{
    "question": "How do I read a text file in Python?"
}
```

## 📊 Data Analysis and Smart Search

PyDocsPal uses Pandas to explore and analyze its documentation records.

The smart search module uses:

- **TF-IDF:** Converts documentation text into numerical vectors based on word importance.
- **Cosine Similarity:** Measures similarity between the user's query and documentation records.
- **Ranking:** Returns the most relevant documentation records first.

## 🧠 LLM Concepts and Documentation

The project includes documentation covering Large Language Models and their working principles.

- Understanding Large Language Models.
- Tokenization and embeddings.
- Transformer architecture and attention mechanisms.
- Next-token prediction and response generation.
- Prompt engineering.
- LLM limitations and hallucinations.
- Potential LLM integration with PyDocsPal.

See: [`docs/how_llms_work.md`](docs/how_llms_work.md)

## ❓ PyDocsPal User Questions

A collection of 10 realistic questions that potential PyDocsPal users may ask.

These questions cover:

- Python functions and modules.
- Function signatures and usage.
- Python version compatibility.
- Deprecation and documentation references.
- Current dataset limitations.

See: [`docs/user_questions.md`](docs/user_questions.md)

## 📅 Development Progress

| Day | Milestone | Status |
|---|---|---|
| Day 1 | Python fundamentals and interactive CLI menu | Completed |
| Day 2 | 20 Python documentation records, searching and categorization | Completed |
| Day 3 | Documentation downloading, ingestion, cleaning and Record dataclass | Completed |
| Day 4 | FastAPI service, Pandas analysis and TF-IDF smart search | Completed |
| Day 5 | LLM working documentation, user questions and Checkpoint 1 | In Progress |

## 🎯 Project Goal

To build an intelligent Python documentation assistant that combines structured documentation, intelligent search, and Large Language Models to deliver accurate, version-aware answers with references to official Python documentation.

## 👨‍💻 Developer

**Aman Sayyad**

[GitHub Repository](https://github.com/111-amann/CreamAI)

---

*Built as part of the Generative AI training program at Sanjivani University.*