@echo off
echo ===============================================
echo  Jarvis - automatic setup for this PC
echo ===============================================
echo.

where python >nul 2>nul
if errorlevel 1 (
    echo [ERROR] Python was not found on this PC.
    echo Please install it first from https://www.python.org/downloads/
    echo ^(tick "Add Python to PATH" during install^), then run this script again.
    pause
    exit /b 1
)

where ollama >nul 2>nul
if errorlevel 1 (
    echo [WARNING] Ollama was not found on this PC.
    echo The voice brain needs it. Install it from https://ollama.com/download
    echo Then run: ollama pull llama3.2
    echo Continuing with the Python setup anyway...
    echo.
)

echo Creating Python virtual environment...
python -m venv venv

echo Installing required Python packages ^(this can take a few minutes^)...
call venv\Scripts\activate.bat
python -m pip install --upgrade pip -q
pip install -r requirements.txt

echo.
echo Pulling the local AI model ^(llama3.2, about 2GB^)...
where ollama >nul 2>nul
if not errorlevel 1 (
    ollama pull llama3.2
) else (
    echo Skipped - install Ollama first, then run: ollama pull llama3.2
)

echo.
echo ===============================================
echo  Setup finished.
echo  Double-click "Jarvis.bat" on the Desktop to start.
echo  ^(If you still need Local WP for WordPress sites,
echo   install it from https://localwp.com/^)
echo ===============================================
pause
