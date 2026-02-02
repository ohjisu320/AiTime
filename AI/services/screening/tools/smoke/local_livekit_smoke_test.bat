@echo off
setlocal EnableExtensions

REM =========================
REM Resolve repo root (absolute)
REM =========================
for %%I in ("%~dp0..\..") do set "ROOT=%%~fI"
pushd "%ROOT%"

REM =========================
REM Config
REM =========================
set "LIVEKIT_URL=ws://127.0.0.1:7880"
set "BACKEND_URL=http://127.0.0.1:8080"
set "LIVEKIT_API_KEY=devkey"
set "LIVEKIT_API_SECRET=secret"

REM Timestamp
for /f %%i in ('powershell -NoProfile -Command "Get-Date -Format yyyyMMdd_HHmmss"') do set "TS=%%i"
set "ROOM=smoke_%TS%"

if not exist "artifacts\smoke" mkdir "artifacts\smoke" >nul 2>nul
set "TOKENS_FILE=artifacts\smoke\tokens_%TS%.json"

echo.
echo =========================
echo LiveKit Smoke Test
echo =========================
echo ROOT=%ROOT%
echo ROOM=%ROOM%
echo TOKENS_FILE=%TOKENS_FILE%
echo.

echo [0] Checking Docker...
where docker >nul 2>nul
if errorlevel 1 goto :NO_DOCKER

docker info >nul 2>nul
if errorlevel 1 goto :NO_DAEMON

REM =========================
REM 1) LiveKit
REM =========================
echo [1] Checking LiveKit port 7880...
netstat -ano | findstr ":7880" >nul
if not errorlevel 1 goto :LIVEKIT_UP

echo [1] Starting LiveKit via Docker (new window)
set "LK_DOCKER_CMD=docker run --name lk_smoke --rm -p 7880:7880 -p 7881:7881 -p 7882:7882/udp livekit/livekit-server:latest --dev --bind 0.0.0.0 --node-ip 127.0.0.1"
start "LiveKit Server (Docker)" /D "%ROOT%" cmd /k "%LK_DOCKER_CMD%"

timeout /t 2 >nul
:LIVEKIT_UP

REM =========================
REM 2) Fake backend (optional)
REM =========================
echo [2] Starting fake backend on :8080 (new window)
start "Fake Backend" /D "%ROOT%" cmd /k "python -m uvicorn tools.smoke.fake_backend:app --host 0.0.0.0 --port 8080"

timeout /t 2 >nul

REM =========================
REM 3) AI server
REM =========================
echo [3] Starting AI server on :8000 (new window)
start "AI Server" /D "%ROOT%" cmd /k "set LIVEKIT_URL=%LIVEKIT_URL% & set BACKEND_URL=%BACKEND_URL% & python -m uvicorn src.serving.app:app --host 0.0.0.0 --port 8000"

timeout /t 2 >nul

REM =========================
REM 4) Static server
REM =========================
echo [4] Starting static server on :5173 (new window)
start "Static Server" /D "%ROOT%" cmd /k "python -m http.server 5173"

timeout /t 2 >nul

REM =========================
REM 5) Generate tokens
REM =========================
echo [5] Generating LiveKit tokens...
python tools\gen_tokens.py --room "%ROOM%" --livekit-url "%LIVEKIT_URL%" --api-key "%LIVEKIT_API_KEY%" --api-secret "%LIVEKIT_API_SECRET%" --out "%TOKENS_FILE%"
if errorlevel 1 goto :TOKEN_FAIL

for /f "usebackq delims=" %%i in (`
  python -c "import json;print(json.load(open(r'%TOKENS_FILE%','r',encoding='utf-8'))['user_token'])"
`) do set "USER_TOKEN=%%i"

REM =========================
REM 6) Trigger analysis start
REM =========================
echo [6] Calling AI /api/v1/analysis/start ...
python tools\call_analysis_start.py --tokens "%TOKENS_FILE%" --ai-url "http://127.0.0.1:8000"
if errorlevel 1 goto :CALL_FAIL

REM =========================
REM 7) Open browser client
REM =========================
echo [7] Opening browser client...
start "" "http://127.0.0.1:5173/tools/smoke/client.html?room=%ROOM%&token=%USER_TOKEN%&url=%LIVEKIT_URL%"

echo.
echo =========================
echo What to check
echo =========================
echo  - AI Server: track_subscribed / Sent guide logs
echo  - Browser: data_received logs
echo  - Fake Backend: screening_complete payload
echo.
pause
goto :EOF

:NO_DOCKER
echo [0] ERROR: docker command not found. Install Docker Desktop.
pause
goto :EOF

:NO_DAEMON
echo [0] ERROR: Docker daemon not running. Start Docker Desktop.
pause
goto :EOF

:TOKEN_FAIL
echo [5] ERROR: token generation failed. Check python deps (livekit-api etc).
pause
goto :EOF

:CALL_FAIL
echo [6] ERROR: analysis start call failed. Check AI server logs.
pause
goto :EOF
