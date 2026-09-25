@echo off
REM Start Frontend (Windows)
REM Run this from the PROJECT ROOT (judicial-ai/) folder

echo 🎨 Starting Judicial AI Frontend...
echo.

REM Check if node_modules exist
if not exist "judicial-ai-react\node_modules" (
    echo 📦 Installing dependencies...
    cd judicial-ai-react
    npm install
    cd ..
    echo.
)

echo 🌐 Starting React dev server on http://localhost:5173
echo.

cd judicial-ai-react
npm run dev