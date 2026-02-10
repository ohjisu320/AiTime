@echo off
setlocal EnableExtensions

REM =========================
REM Resolve script directory
REM =========================
set "ROOT=%~dp0"
pushd "%ROOT%"

REM =========================
REM Config (safe quoting)
REM =========================
set "ENV_NAME=face_to_face_name_response"
set "YML=%ROOT%environment.yml"
set "REQ=%ROOT%requirements.txt"
set "LOG=%ROOT%setup_install.log"

REM Keep last error code for cleanup/exit
set "LAST_RC=0"

REM =========================
REM Init log
REM =========================
> "%LOG%" echo Setup started at %DATE% %TIME%
>> "%LOG%" echo ROOT=%ROOT%
>> "%LOG%" echo ENV_NAME=%ENV_NAME%
>> "%LOG%" echo YML=%YML%
>> "%LOG%" echo REQ=%REQ%

REM =========================
REM Helper: Run command, tee to log, preserve exit code
REM Usage: call :run "Step name" "command line"
REM =========================
goto :prechecks

:run
set "STEP_NAME=%~1"
set "CMDLINE=%~2"

echo.
echo ---------- %STEP_NAME% ----------
>> "%LOG%" echo.
>> "%LOG%" echo ---------- %STEP_NAME% ----------
>> "%LOG%" echo [%DATE% %TIME%] %CMDLINE%

REM Pass command via env vars to reduce quoting pitfalls
set "RUN_LOG=%LOG%"
set "RUN_CMD=%CMDLINE%"

powershell -NoProfile -ExecutionPolicy Bypass ^
  -Command ^
  "$ErrorActionPreference='Continue';" ^
  "$log=$env:RUN_LOG;" ^
  "$cmd=$env:RUN_CMD;" ^
  "Write-Host $cmd;" ^
  "& cmd.exe /d /v:off /c $cmd 2^>^&1 | Tee-Object -FilePath $log -Append;" ^
  "exit $LASTEXITCODE"

set "RC=%ERRORLEVEL%"
if not "%RC%"=="0" (
  echo [ERROR] Step failed: %STEP_NAME% (exit=%RC%)
  >> "%LOG%" echo [ERROR] Step failed: %STEP_NAME% (exit=%RC%)
)
exit /b %RC%

:prechecks
REM =========================
REM Pre-check files
REM =========================
if not exist "%YML%" (
  echo [ERROR] Missing file: %YML%
  >> "%LOG%" echo [ERROR] Missing file: %YML%
  set "LAST_RC=1"
  goto :cleanup
)
if not exist "%REQ%" (
  echo [ERROR] Missing file: %REQ%
  >> "%LOG%" echo [ERROR] Missing file: %REQ%
  set "LAST_RC=1"
  goto :cleanup
)

echo =========================================
echo [1/4] Check conda
echo =========================================
where conda >nul 2>&1
if errorlevel 1 (
  echo [ERROR] conda command not found.
  echo - Run this in "Anaconda Prompt" or "Miniforge Prompt"
  echo - Or run: conda init
  >> "%LOG%" echo [ERROR] conda command not found.
  set "LAST_RC=1"
  goto :cleanup
)
>> "%LOG%" echo Conda found.

REM PowerShell check (for tee logging)
where powershell >nul 2>&1
if errorlevel 1 (
  echo [ERROR] powershell not found. (Needed for tee logging)
  >> "%LOG%" echo [ERROR] powershell not found.
  set "LAST_RC=1"
  goto :cleanup
)

REM =========================
REM (Optional) log versions early
REM =========================
call :run "Conda version" "conda --version"
if not "%ERRORLEVEL%"=="0" ( set "LAST_RC=%ERRORLEVEL%" & goto :cleanup )

call :run "Conda info (brief)" "conda info"
if not "%ERRORLEVEL%"=="0" ( set "LAST_RC=%ERRORLEVEL%" & goto :cleanup )

echo =========================================
echo [2/4] Create / Update conda env: %ENV_NAME%
echo =========================================

REM Robust env existence check (env name + at least one space)
call conda env list | findstr /R /C:"^%ENV_NAME%[ ][ ]*" >nul 2>&1
if not errorlevel 1 (
  echo Environment exists. Updating...
  call :run "Conda env update" "conda env update -n ""%ENV_NAME%"" -f ""%YML%"" --prune"
  if not "%ERRORLEVEL%"=="0" ( set "LAST_RC=%ERRORLEVEL%" & goto :cleanup )
) else (
  echo Environment not found. Creating...
  REM Force env name so it doesn't depend on environment.yml name:
  call :run "Conda env create" "conda env create -n ""%ENV_NAME%"" -f ""%YML%"""
  if not "%ERRORLEVEL%"=="0" ( set "LAST_RC=%ERRORLEVEL%" & goto :cleanup )
)

echo =========================================
echo [3/4] Upgrade pip tools
echo =========================================
call :run "Pip upgrade tools" "conda run -n ""%ENV_NAME%"" python -m pip install -U pip setuptools wheel"
if not "%ERRORLEVEL%"=="0" ( set "LAST_RC=%ERRORLEVEL%" & goto :cleanup )

echo =========================================
echo [4/4] Install pip requirements
echo =========================================
call :run "Pip install requirements" "conda run -n ""%ENV_NAME%"" python -m pip install -r ""%REQ%"""
if not "%ERRORLEVEL%"=="0" ( set "LAST_RC=%ERRORLEVEL%" & goto :cleanup )

echo =========================================
echo Done! Quick import test
echo =========================================
call :run "Quick import test" "conda run -n ""%ENV_NAME%"" python -c ""import torch, cv2, mediapipe, fastapi; print('OK', torch.__version__)"""
if not "%ERRORLEVEL%"=="0" ( set "LAST_RC=%ERRORLEVEL%" & goto :cleanup )

echo =========================================
echo Finished successfully. Setup log saved to %LOG%
echo =========================================
set "LAST_RC=0"
goto :cleanup

:cleanup
echo.
echo =========================================
if "%LAST_RC%"=="0" (
  echo Finished. (SUCCESS)
  >> "%LOG%" echo Finished. (SUCCESS)
) else (
  echo Finished. (FAILED) exit=%LAST_RC%
  >> "%LOG%" echo Finished. (FAILED) exit=%LAST_RC%
)
echo Log: %LOG%
echo =========================================

popd
pause
exit /b %LAST_RC%
