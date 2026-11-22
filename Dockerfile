FROM python:3.12-slim

# Prevent Python from writing .pyc files and enable unbuffered logging
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install minimal system build dependencies and curl for healthcheck
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy dependency definition
COPY requirements.txt .

# Install dependencies handling the known Streamlit vs ChromaDB protobuf conflict cleanly:
# 1. Install base requirements (without streamlit)
# 2. Install streamlit with --no-deps to prevent downgrading or breaking protobuf
# 3. Ensure all required Streamlit runtime dependencies are present
RUN grep -v "^streamlit" requirements.txt > /tmp/requirements_base.txt && \
    pip install --upgrade pip && \
    pip install -r /tmp/requirements_base.txt && \
    pip install --no-deps "streamlit>=1.40.0" && \
    pip install \
        altair \
        blinker \
        cachetools \
        click \
        gitpython \
        packaging \
        pillow \
        pyarrow \
        requests \
        tenacity \
        toml \
        watchdog

# Copy application directories and required data artifacts
COPY app/ ./app/
COPY ui/ ./ui/
COPY prompts/ ./prompts/
COPY data/ ./data/

# Copy configuration files
COPY pytest.ini ruff.toml ./

# Expose FastAPI and Streamlit ports
EXPOSE 8000
EXPOSE 8501

# Default command (overridden by docker-compose)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
