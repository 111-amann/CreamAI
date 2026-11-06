# PyDocsPal 🐍

### Your Python Documentation Assistant

PyDocsPal is a Python documentation assistant designed to help developers and students understand Python functions, classes, modules, signatures, and version compatibility using official Python documentation.

## 📌 Project Card

**Product:** PyDocsPal

**User:** Python developers, students, and programmers who need quick and reliable information about Python functions, modules, and classes.

**Problem:** Finding accurate information about Python APIs, understanding their usage, checking Python version compatibility, and identifying deprecated or removed features can take time. Python documentation also changes between versions.

**Solution:** PyDocsPal aims to simplify Python documentation discovery by organizing official documentation into searchable records and eventually providing AI-powered explanations.

**Data Source:** [Official Python Documentation](https://docs.python.org/3/download.html)

## ✨ Core Features

- Search Python functions, modules, and classes.
- Understand function signatures and usage.
- Check Python version compatibility.
- Identify deprecated and removed APIs.
- Provide answers with official documentation references.
- Organize documentation into structured records.

**Signature Feature:** Every answer will display a Python version compatibility badge and warnings for deprecated or removed APIs.

## 🛠️ Tech Stack

**Current Implementation**
- Python
- JSON
- Requests
- Dataclasses
- pathlib
- Regular Expressions
- Git and GitHub

**Planned Technologies**
- FastAPI
- Pandas
- Scikit-learn
- Groq / Gemini API
- Embeddings
- ChromaDB
- Retrieval-Augmented Generation (RAG)
- Streamlit

## 📂 Project Structure

```text
PyDocsPal/
│
├── app/
│   ├── __init__.py
│   ├── records.py
│   ├── cli.py
│   ├── ingest.py
│   ├── models.py
│   └── fetch.py
│
├── data/
│   ├── raw/
│   └── records.json
│
├── README.md
├── requirements.txt
└── .gitignore
```

## 📅 Development Progress

| Day | Milestone | Status |
|---|---|---|
| Day 1 | Python fundamentals and interactive CLI menu | Completed |
| Day 2 | 20 Python documentation records, searching and categorization | Completed |
| Day 3 | Documentation downloading, ingestion, cleaning and Record dataclass | Completed |
| Day 4 | FastAPI endpoints | Upcoming |

## 🚀 Running the Project

### 1. Clone the repository

```bash
git clone https://github.com/111-amann/CreamAI.git
cd CreamAI
```

### 2. Create and activate virtual environment

```bash
python -m venv .venv
```

Windows PowerShell:

```powershell
.venv\Scripts\Activate.ps1
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Run the CLI application

```bash
python -m app.cli
```

### 5. Download documentation pages

```bash
python -m app.fetch
```

### 6. Ingest documentation

```bash
python -m app.ingest
```

## 🎯 Project Goal

To build an intelligent Python documentation assistant that combines structured documentation, semantic search, and Large Language Models to deliver accurate, version-aware answers with references to official Python documentation.

## 👨‍💻 Developer

**Aman Sayyad**

[GitHub Repository](https://github.com/111-amann/CreamAI)

---

*Built as part of the Generative AI training program at Sanjivani University.*