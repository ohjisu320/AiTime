@echo off
setlocal EnableExtensions

set ENV_NAME=face_to_face_name_response
set YML=environment.yml
set REQ=requirements.txt

echo =========================================
echo [1/4] Check conda
echo =========================================
where conda >nul 2>&1
if errorlevel 1 (
  echo [ERROR] conda command not found.
  echo - Run this in "Anaconda Prompt" or "Miniforge Prompt"
  echo - Or run: conda init
  exit /b 1
)

echo =========================================
echo [2/4] Create / Update conda env: %ENV_NAME%
echo =========================================
conda env list | findstr /R /C:"^%ENV_NAME% " >nul 2>&1
if %errorlevel%==0 (
  echo Environment exists. Updating...
  conda env update -n %ENV_NAME% -f %YML% --prune
) else (
  echo Environment not found. Creating...
  conda env create -f %YML%
)

echo =========================================
echo [3/4] Upgrade pip tools
echo =========================================
conda run -n %ENV_NAME% python -m pip install -U pip setuptools wheel

echo =========================================
echo [4/4] Install pip requirements
echo =========================================
conda run -n %ENV_NAME% python -m pip install -r %REQ%

echo =========================================
echo Done! Quick import test
echo =========================================
conda run -n %ENV_NAME% python -c "import torch, cv2, mediapipe, fastapi; print('OK', torch.__version__)"
echo =========================================
echo Finished.
pause
