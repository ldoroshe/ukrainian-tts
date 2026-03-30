#!/usr/bin/env bash
set -euo pipefail

# Build the docker image (optionally preload models with BUILD_PRELOAD=1)
IMAGE_NAME=ukrainian-tts:dev

echo "Building Docker image $IMAGE_NAME"
docker build -t ${IMAGE_NAME} .

echo "Running integration E2E inside container"
docker run --rm -e DEVICE=cpu -v $(pwd)/cache:/cache ${IMAGE_NAME} python tests/e2e/run_e2e.py

echo "E2E finished successfully"
