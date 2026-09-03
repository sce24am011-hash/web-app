@echo off
title DeepCheck Classroom
cd /d "%~dp0"

echo =========================================================
echo       DeepCheck Classroom - Launching Application
echo =========================================================
echo.

:: Check for python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python was not found in PATH. Please install Python 3.10+
    pause
    exit /b 1
)

:: Check if frontend dist exists, if not build it
if not exist "frontend\dist\index.html" (
    echo [Setup] First time setup: building web application assets...
    cd frontend
    call npm run build
    cd ..
)

:: Launch desktop application
python desktop_app.py
