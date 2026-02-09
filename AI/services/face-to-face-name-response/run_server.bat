@echo off
setlocal EnableExtensions

set ENV_NAME=face_to_face_name_response
set HOST=0.0.0.0
set PORT=8005

echo =========================================
echo Running Uvicorn in conda env: %ENV_NAME%
echo HOST=%HOST% PORT=%PORT%
echo =========================================

conda run --no-capture-output -n %ENV_NAME% ^
  uvicorn app.main:app --reload --host %HOST% --port %PORT% --log-level info

pause
