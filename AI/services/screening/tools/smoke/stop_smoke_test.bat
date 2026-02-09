@echo off
REM Quick-and-dirty stop script (Windows).
REM It terminates python processes whose command line contains "uvicorn" or "http.server".
REM Close the LiveKit server window manually (or stop the docker container).

echo This will terminate python processes that look like uvicorn/http.server.
echo If you are running other Python servers, stop them manually.
echo.
pause

echo Killing uvicorn / http.server python processes...
wmic process where "name='python.exe' and (commandline like '%%uvicorn%%' or commandline like '%%http.server%%')" call terminate >nul 2>nul

echo Done.
