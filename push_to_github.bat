@echo off
title Push Campus AI to GitHub
cd /d "%~dp0"

echo ========================================================
echo        Campus AI - Push to GitHub Launcher
echo ========================================================
echo.
echo [1/2] Checking remote repository:
git remote -v
echo.
echo [2/2] Pushing main branch to GitHub...
git push -u origin main

echo.
echo ========================================================
echo If push failed, make sure you created the repo on GitHub:
echo https://github.com/new (Repository name: Campus-AI)
echo ========================================================
echo.
pause
