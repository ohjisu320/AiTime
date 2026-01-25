#!/usr/bin/env bash
set -euo pipefail

ENV_NAME="face_to_face_name_response"
HOST="0.0.0.0"
PORT="8005"

echo "========================================="
echo "Running Uvicorn in conda env: ${ENV_NAME}"
echo "HOST=${HOST} PORT=${PORT}"
echo "========================================="

conda run --no-capture-output -n "${ENV_NAME}" \
  uvicorn app.main:app --reload --host "${HOST}" --port "${PORT}" --log-level info

# HOW TO RUN THIS CODE IN LINUX
# chmod +x run_server.sh
# ./run_server.sh