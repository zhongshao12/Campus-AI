@echo off
title Campus AI Launcher
cd /d "%~dp0"

echo ========================================================
echo        Campus AI - AI Galgame Launcher
echo ========================================================
echo.
echo [1/2] Launching Backend Server (FastAPI on Port 8000)...
start "CampusAI-Backend" cmd /k "cd /d "%~dp0backend" && python run.py"

echo [2/2] Launching Frontend Server (Vite on Port 5173)...
start "CampusAI-Frontend" cmd /k "cd /d "%~dp0frontend" && npx vite --open"

echo.
echo ========================================================
echo All services launched!
echo - Web Game URL: http://127.0.0.1:5173
echo - Backend API Docs: http://127.0.0.1:8000/docs
echo ========================================================
echo.
pause
