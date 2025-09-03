@echo off
REM Brutally Honest AI - Unified Startup Script for Windows
REM This script starts both the backend API server and frontend web server

echo 🚀 Starting Brutally Honest AI Application...
echo ==================================================

REM Check if virtual environment exists
if not exist "venv" (
    echo ❌ Virtual environment not found. Please run: python -m venv venv
    pause
    exit /b 1
)

REM Check if node_modules exists in frontend
if not exist "frontend\node_modules" (
    echo 📦 Installing frontend dependencies...
    cd frontend
    npm install
    cd ..
)

echo 🔍 Starting services...

REM Start backend in new window
echo 🔌 Starting backend API server...
start "Backend API Server" cmd /k "venv\Scripts\activate && python api_server.py"

REM Wait a moment
timeout /t 3 /nobreak >nul

REM Start frontend in new window
echo 🌐 Starting frontend web server...
start "Frontend Web Server" cmd /k "cd frontend && npm start"

echo.
echo 🎉 Brutally Honest AI is starting up!
echo ==================================================
echo 📡 Backend API: http://localhost:8000
echo 🌐 Frontend Web: http://localhost:3001
echo 📚 API Docs: http://localhost:8000/docs
echo 🔌 WebSocket: ws://localhost:8000/ws
echo.
echo 💡 Close the terminal windows to stop the services
echo.
pause
