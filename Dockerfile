FROM python:3.10-slim

ENV DEBIAN_FRONTEND=noninteractive

# System deps for soundfile, espnet, and building wheels.
# gcc/g++/gfortran/libopenblas-dev/liblapack-dev/pkg-config/python3-dev are
# required by scipy and espnet when building from source (as per scipy docs).
# libsndfile1 is required by soundfile.
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential git ffmpeg \
    libsndfile1 libsndfile1-dev \
    ca-certificates wget \
    libopenblas-dev liblapack-dev gfortran \
    cmake pkg-config python3-dev && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy project
COPY . /app

# Upgrade pip/setuptools/wheel first.
# setuptools must be pinned <70: in setuptools>=70 pkg_resources is no longer
# available as a top-level module, which breaks pyworld (used by espnet2).
RUN pip install --upgrade pip "setuptools<70" wheel

# Install PyTorch CPU-only first (much smaller, always has amd64 binary wheels).
# Using the official PyTorch CPU index avoids downloading CUDA binaries.
# Pin to 2.2.x which is compatible with espnet==202301.
RUN pip install --prefer-binary \
    torch==2.2.2 \
    torchaudio==2.2.2 \
    --index-url https://download.pytorch.org/whl/cpu

# Install remaining dependencies.
# typeguard<3 is required by espnet==202301.
# scipy<1.12.0 is pinned for espnet compatibility.
# We skip torch from requirements.txt (already installed above) to avoid
# pulling the CUDA variant.
RUN pip install --prefer-binary \
    "typeguard<3" \
    "scipy<1.12.0" \
    soundfile \
    "git+https://github.com/savoirfairelinux/num2words.git@3e39091d052829fc9e65c18176ce7b7ff6169772" \
    "ukrainian-word-stress==1.1.0" \
    "git+https://github.com/egorsmkv/ukrainian-accentor.git@5b7971c4e135e3ff3283336962e63fc0b1c80f4c" \
    huggingface_hub

# Install espnet after torch/scipy are settled (espnet needs both)
RUN pip install --prefer-binary "espnet==202301"

# Install package in editable mode
RUN pip install -e .

# Default cache folder
ENV UK_TTS_CACHE=/cache
RUN mkdir -p /cache

CMD ["python", "scripts/generate_sample.py"]
