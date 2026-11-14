# PyDocsPal

### Your Python Documentation Assistant

PyDocsPal is a Python documentation assistant designed to help developers and students discover and understand Python modules, functions, classes, signatures, usage examples, and version compatibility using official Python documentation.

## Project Overview

**Problem:** Finding accurate Python API information, understanding function usage, checking version compatibility, and identifying deprecated features can take time.

**Solution:** PyDocsPal collects and organizes Python documentation into searchable records and text chunks. It provides keyword-based, semantic, and hybrid search through a FastAPI service, with an LLM-powered explanation endpoint.

**Primary Data Source:** [Official Python Documentation](https://docs.python.org/3/)

## Core Features

- Search Python functions, modules, and classes.
- Retrieve API signatures and usage examples.
- Search structured documentation records using TF-IDF.
- Split documentation into manageable text chunks.
- Generate embeddings using Sentence Transformers.
- Store and retrieve document embeddings using ChromaDB.
- Perform semantic search across documentation chunks.
- Combine semantic and lexical search using Reciprocal Rank Fusion (RRF).
- Generate explanations using an LLM provider.
- Access functionality through REST API endpoints.
- Analyze structured documentation records using Pandas.

## Tech Stack

| Category | Technologies |
|---|---|
| Language | Python |
| API | FastAPI, Uvicorn |
| Data Processing | Pandas |
| Keyword Search | Scikit-learn, TF-IDF |
| Semantic Search | Sentence Transformers |
| Embedding Model | all-MiniLM-L6-v2 |
| Vector Database | ChromaDB |
| Ranking | Cosine Similarity, Reciprocal Rank Fusion |
| LLM Integration | Groq / Gemini provider wrapper |
| Data Storage | JSON, Text Files |
| Environment Management | python-dotenv, venv |
| Version Control | Git, GitHub |

## Project Structure

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
│   ├── chunking.py
│   ├── embed.py
│   ├── vectorstore.py
│   ├── hybrid_search.py
│   ├── llm.py
│   ├── cli.py
│   ├── ingest.py
│   ├── models.py
│   └── fetch.py
│
├── data/
│   ├── raw/
│   │   ├── extracted/
│   │   └── fetched/
│   ├── chroma_db/
│   └── records.json
│
├── docs/
│   ├── how_llms_work.md
│   └── user_questions.md
│
├── prompts/
│   ├── system.txt
│   ├── task_explain.txt
│   └── task_compare.txt
│
├── eval/
│   ├── run_search_eval.py
│   ├── run_hybrid_eval.py
│   ├── search_results.md
│   └── hybrid_search_results.md
│
├── day01_intro.py
├── day01_menu.py
├── README.md
├── requirements.txt
├── .env.example
└── .gitignore
```

*Note: Generated files and local environment files may not be included in the Git repository.*

## Installation and Setup

### 1. Clone the repository

```bash
git clone https://github.com/111-amann/CreamAI.git
cd CreamAI
```

### 2. Create a virtual environment

```bash
python -m venv .venv
```

### 3. Activate the environment

Windows PowerShell:

```powershell
.venv\Scripts\Activate.ps1
```

### 4. Install dependencies

```bash
pip install -r requirements.txt
```

### 5. Configure environment variables

Create a `.env` file in the project root.

Example Groq configuration:

```env
LLM_PROVIDER=groq
GROQ_API_KEY=your_groq_api_key
GROQ_MODEL=openai/gpt-oss-120b
```

Use your own API key. Never commit `.env` or expose API credentials in GitHub.

### 6. Run the CLI application

```bash
python -m app.cli
```

### 7. Start the FastAPI server

```bash
uvicorn app.main:app --reload
```

The API will be available at:

`http://127.0.0.1:8000`

Interactive Swagger documentation:

`http://127.0.0.1:8000/docs`

## Documentation Processing and Indexing

PyDocsPal uses documentation text files as its retrieval corpus.

The processing pipeline includes:

1. Fetching documentation pages.
2. Extracting documentation text.
3. Splitting documents into chunks while retaining source and section metadata.
4. Generating embeddings with Sentence Transformers.
5. Storing embeddings and metadata in a persistent ChromaDB collection.

To fetch the configured documentation pages:

```bash
python -m app.fetch
```

To run the structured-record ingestion process:

```bash
python -m app.ingest
```

To build or rebuild the ChromaDB index:

```bash
python -m app.vectorstore
```

The persistent ChromaDB database is stored locally in:

`data/chroma_db/`

The first embedding-model load may require an internet connection to download the model.

## Search Architecture

PyDocsPal currently provides three different retrieval approaches.

### 1. Structured Record Search

The `smart_search.py` module uses:

- **TF-IDF:** Converts text into numerical representations based on word importance.
- **Cosine Similarity:** Measures similarity between the query and documentation records.
- **Ranking:** Returns the highest-scoring records.

This search operates on the structured records in `data/records.json`.

### 2. Semantic Search

The semantic retrieval pipeline uses:

- **Chunking:** Divides documentation into smaller text segments.
- **Sentence Transformers:** Generates 384-dimensional embeddings using `all-MiniLM-L6-v2`.
- **ChromaDB:** Stores and retrieves document embeddings.
- **Similarity Search:** Retrieves chunks based on semantic similarity.

### 3. Hybrid Search

The hybrid search module combines:

- Semantic retrieval from ChromaDB.
- Lexical retrieval using TF-IDF.
- Reciprocal Rank Fusion (RRF) to combine the two rankings.

This approach aims to improve retrieval by considering both meaning and exact terminology.

**Important:** Hybrid retrieval improves the available search signals, but it does not guarantee that every query will retrieve complete or correct documentation.

## LLM Integration

PyDocsPal includes an LLM provider wrapper that supports configured providers such as Groq and Gemini.

The `/chat` endpoint:

1. Accepts a user question.
2. Retrieves relevant structured documentation records.
3. Loads the system and task prompts.
4. Sends the prompt and retrieved context to the configured LLM.
5. Returns a structured response containing an answer, confidence value, and follow-up question.

The confidence value is model-reported and is not a calibrated probability.

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | `/health` | Check API health |
| GET | `/records?limit=10` | Retrieve structured records |
| GET | `/records/{id}` | Retrieve a record by ID |
| GET | `/search?q=python` | Search structured records using TF-IDF |
| GET | `/search/semantic?q=python` | Search documentation chunks using hybrid retrieval |
| POST | `/questions` | Retrieve relevant structured records for a question |
| POST | `/chat` | Generate an LLM-powered response using structured-record context |

### Example: Hybrid Search

**GET**

```http
/search/semantic?q=pathlib.Path.read_text%20signature&limit=5
```

Example response structure:

```json
{
  "query": "pathlib.Path.read_text signature",
  "search_type": "hybrid",
  "total_results": 5,
  "results": [
    {
      "id": "document_chunk_id",
      "text": "Relevant documentation text...",
      "source": "path/to/document.txt",
      "title": "Pathlib",
      "section": "Reading and writing files",
      "page": "unknown",
      "hybrid_score": 0.031,
      "semantic_rank": 4,
      "lexical_rank": 2
    }
  ]
}
```

*The values above illustrate the response structure, not a fixed search result.*

### Example: Chat

**POST `/chat`**

Request body:

```json
{
  "question": "Explain pathlib.Path.read_text",
  "task": "explain"
}
```

The response contains:

- `answer`
- `confidence`
- `follow_up`

## Evaluation

PyDocsPal includes evaluation scripts for comparing semantic and hybrid retrieval.

Run semantic search evaluation:

```bash
python -m eval.run_search_eval
```

Run hybrid search evaluation:

```bash
python -m eval.run_hybrid_eval
```

Evaluation reports:

- `eval/search_results.md`
- `eval/hybrid_search_results.md`

The current manual evaluation identified successful, partial, and failed retrieval cases. Some queries still require improvements, particularly complete API listings, version-specific changes, and dataset-wide inventory questions.

## LLM Concepts and Learning Documentation

The project also includes learning material covering:

- Large Language Models.
- Tokenization and embeddings.
- Transformer architecture and attention.
- Next-token prediction.
- Prompt engineering.
- LLM limitations and hallucinations.
- Retrieval-Augmented Generation concepts.

See [`docs/how_llms_work.md`](docs/how_llms_work.md).

## Developer

**Aman Sayyad**

[GitHub Profile](https://github.com/111-amann)

---

*Built as part of the Generative AI training program at Sanjivani University.*
