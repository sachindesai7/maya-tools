@echo off
echo ================================================
echo   Figma Asset Exporter - Setup
echo ================================================
echo.

:: Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found.
    echo Download Python 3.8+ from https://www.python.org/downloads/
    echo Make sure to check "Add Python to PATH" during install.
    pause
    exit /b 1
)

echo Python found. Installing dependencies...
python -m pip install --upgrade pip --quiet
python -m pip install -r requirements.txt

echo.
echo ================================================
echo   Setup complete! Run the app with: run.bat
echo ================================================
pause
