@echo off
REM KnowledgeHub Startup Script for Windows

echo 🧠 Starting KnowledgeHub...
echo.

REM Check if Ollama is installed
where ollama >nul 2>nul
if %errorlevel% neq 0 (
    echo ❌ Ollama is not installed or not in PATH
    echo Please install Ollama from https://ollama.com/download
    pause
    exit /b 1
)

REM Check Python
where python >nul 2>nul
if %errorlevel% neq 0 (
    echo ❌ Python is not installed or not in PATH
    echo Please install Python 3.8+ from https://www.python.org/downloads/
    pause
    exit /b 1
)

echo ✅ Prerequisites found
echo.

REM Check if Ollama service is running
tasklist /FI "IMAGENAME eq ollama.exe" 2>NUL | find /I /N "ollama.exe">NUL
if "%ERRORLEVEL%"=="1" (
    echo ⚠️  Ollama is not running. Please start Ollama first.
    echo You can start it from the Start menu or by running: ollama serve
    pause
    exit /b 1
)

echo ✅ Ollama is running
echo.

REM Check if model exists
ollama list | find "llama3.2" >nul
if %errorlevel% neq 0 (
    echo 📥 Llama 3.2 model not found. Pulling model...
    echo This may take a few minutes on first run...
    ollama pull llama3.2
)

echo ✅ Model ready
echo.

REM Install dependencies
echo 🔍 Checking dependencies...
python -c "import gradio" 2>nul
if %errorlevel% neq 0 (
    echo 📦 Installing dependencies...
    pip install -r requirements.txt
)

echo ✅ Dependencies ready
echo.

REM Launch application
echo 🚀 Launching KnowledgeHub...
echo The application will open in your browser at http://127.0.0.1:7860
echo.
echo Press Ctrl+C to stop the application
echo.

python app.py

pause
