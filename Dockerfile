FROM python:3.10-slim

ENV DEBIAN_FRONTEND=noninteractive

# System deps for soundfile, espnet, and building wheels
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential git ffmpeg libsndfile1 libsndfile1-dev ca-certificates \
    libatlas-base-dev wget && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy project
COPY . /app

# Upgrade pip and install Python deps
RUN pip install --upgrade pip setuptools wheel && \
    pip install -r requirements.txt || true

# Install package in editable mode
RUN pip install -e . || true

# Default cache folder
ENV UK_TTS_CACHE=/cache
RUN mkdir -p /cache

COPY scripts /app/scripts

ENTRYPOINT ["python", "scripts/generate_sample.py"]
