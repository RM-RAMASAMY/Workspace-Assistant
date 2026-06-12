FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install the CPU-only PyTorch wheel first so sentence-transformers reuses it
# instead of pulling the default ~2-3 GB CUDA build. Inference runs on CPU
# (embeddings/reranker) and in Ollama Cloud (LLM), so GPU libs are unused.
# Kept before COPY requirements.txt so this layer stays cached across dependency changes.
RUN pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Pre-download retrieval models to avoid runtime downloads.
RUN python -c "\
from sentence_transformers import SentenceTransformer, CrossEncoder; \
SentenceTransformer('all-MiniLM-L6-v2'); \
CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')"

COPY . .

EXPOSE 8000

CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
