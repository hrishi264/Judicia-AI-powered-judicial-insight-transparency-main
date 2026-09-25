@echo off
REM Start Backend Server (Windows)
REM Run this from the PROJECT ROOT (judicial-ai/) folder

echo 🚀 Starting Judicial AI Backend Server...
echo.

REM Activate virtual environment if it exists
if exist "venv\Scripts\activate.bat" (
    echo ✅ Activating virtual environment...
    call venv\Scripts\activate.bat
) else (
    echo ⚠️  Virtual environment not found. Using system Python.
)

echo.
echo 🌐 Starting FastAPI server on http://localhost:8000
echo    API Docs: http://localhost:8000/docs
echo    Health Check: http://localhost:8000/health
echo.

cd backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000