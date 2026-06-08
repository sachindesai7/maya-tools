@echo off
:: Figma Asset Exporter launcher
:: Auto-installs missing dependencies then starts the app.

python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found. Run setup.bat first.
    pause
    exit /b 1
)

:: Silently ensure requests is installed
python -m pip install requests --quiet >nul 2>&1

:: Launch app
python figma_exporter.py
