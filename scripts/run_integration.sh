#!/usr/bin/env bash
set -euo pipefail

# Build the docker image (optionally preload models with BUILD_PRELOAD=1)
IMAGE_NAME=ukrainian-tts:dev

echo "Building Docker image $IMAGE_NAME for linux/amd64 (uses buildx)"
# Use buildx to target linux/amd64 so prebuilt wheels for many packages are available.
# --load loads the built image into the local docker images list (requires buildx supported).
docker buildx build --platform=linux/amd64 -t ${IMAGE_NAME} --load .

echo "Running integration E2E inside container"
mkdir -p "$(pwd)/cache"
docker run --rm --platform linux/amd64 -e DEVICE=cpu -v "$(pwd)/cache:/cache" ${IMAGE_NAME} python tests/e2e/run_e2e.py

echo "E2E finished successfully"
