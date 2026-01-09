#!/usr/bin/env bash
set -euo pipefail

# Build a test image (includes pytest from requirements.txt) and run tests
IMG_NAME=infracalendar:test

echo "Building docker image ${IMG_NAME}..."
docker build -t ${IMG_NAME} .

echo "Running pytest inside container..."
# Override ENTRYPOINT to run pytest module
docker run --rm --entrypoint python ${IMG_NAME} -m pytest -q

echo "Tests completed."
