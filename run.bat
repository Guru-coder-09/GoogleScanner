@echo off
title GoogleScanner Workstation - Dual Studio
cd /d "%~dp0"
echo ===================================================
echo ✨ Launching GoogleScanner Workstation Web UI
echo ===================================================
echo.
echo Starting local API server at http://127.0.0.1:8000 ...
start "" "http://127.0.0.1:8000"
C:\Users\tejag\ai-file-organizer\.venv\Scripts\python.exe -m uvicorn neatworkspace.api:app --host 127.0.0.1 --port 8000
pause
