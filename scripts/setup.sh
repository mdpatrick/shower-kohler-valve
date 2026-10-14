#!/bin/sh
set -eu
cd "$(dirname "$0")/.."
mkdir -p build
PROJECT_PYTHON=${PROJECT_PYTHON:-python3.12}
UV_CACHE_DIR="$PWD/build/uv-cache" uv venv --python "$PROJECT_PYTHON" .venv
UV_CACHE_DIR="$PWD/build/uv-cache" uv pip install --python .venv/bin/python --only-binary=:all: -r environment/requirements.lock
./project doctor
