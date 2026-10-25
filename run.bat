@echo off
title GoogleScanner Workstation
cd /d "%~dp0"
echo ===================================================
echo ✨ Launching GoogleScanner (Google Drive Simulation)
echo ===================================================
echo.
C:\Users\tejag\ai-file-organizer\.venv\Scripts\python.exe main.py --drive --sim
echo.
pause
