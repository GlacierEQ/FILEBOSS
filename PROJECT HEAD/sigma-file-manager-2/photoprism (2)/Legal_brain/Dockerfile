# syntax=docker/dockerfile:1

FROM python:3.10-slim AS base

# Install system dependencies (Tesseract, ffmpeg, etc.)
RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr \
    ffmpeg \
    libsm6 \
    libxext6 \
    git \
    && rm -rf /var/lib/apt/lists/*

# Create a non-root user for running the app
RUN useradd -m legalbrainuser

WORKDIR /app

FROM base AS builder

# Copy requirements.txt only for better cache usage
COPY --link requirements.txt ./

ENV PIP_CACHE_DIR=/root/.cache/pip

# Create venv and install dependencies
RUN --mount=type=cache,target=$PIP_CACHE_DIR \
    python -m venv .venv && \
    .venv/bin/pip install -r requirements.txt

# Copy the rest of the application code
COPY --link . .

FROM base AS final

WORKDIR /app

# Copy venv from builder
COPY --from=builder /app/.venv /app/.venv
# Copy app code from builder
COPY --from=builder /app /app

ENV PATH="/app/.venv/bin:$PATH"

USER legalbrainuser

EXPOSE 8000

# Default command: Flask app (can be overridden)
CMD ["python", "-m", "flask", "run", "--host=0.0.0.0", "--port=8000"]
# If using FastAPI, replace with:
# CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
