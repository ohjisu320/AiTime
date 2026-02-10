#!/usr/bin/env bash
set -euo pipefail

ENV_NAME="face_to_face_name_response"
YML="environment.yml"
REQ="requirements.txt"

echo "========================================="
echo "[1/4] Check conda"
echo "========================================="
if ! command -v conda >/dev/null 2>&1; then
  echo "[ERROR] conda command not found."
  echo "- Install Miniconda/Miniforge and try again."
  exit 1
fi

echo "========================================="
echo "[2/4] Create / Update conda env: ${ENV_NAME}"
echo "========================================="
if conda env list | awk '{print $1}' | grep -qx "${ENV_NAME}"; then
  echo "Environment exists. Updating..."
  conda env update -n "${ENV_NAME}" -f "${YML}" --prune
else
  echo "Environment not found. Creating..."
  conda env create -f "${YML}"
fi

echo "========================================="
echo "[3/4] Upgrade pip tools"
echo "========================================="
conda run -n "${ENV_NAME}" python -m pip install -U pip setuptools wheel

echo "========================================="
echo "[4/4] Install pip requirements"
echo "========================================="
conda run -n "${ENV_NAME}" python -m pip install -r "${REQ}"

echo "========================================="
echo "Done! Quick import test"
echo "========================================="
conda run -n "${ENV_NAME}" python -c "import torch, cv2, mediapipe, fastapi; print('OK', torch.__version__)"
echo "========================================="
echo "Finished."

# HOW TO RUN THIS CODE
# this is for you
# need execute permission
# chmod +x setup_face_to_face_name_response.sh
# ./setup_face_to_face_name_response.sh
