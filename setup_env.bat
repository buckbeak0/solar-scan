@echo off
echo ===================================================
echo [SOLARSCAN] Setting up Python Virtual Environment
echo ===================================================

:: Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python was not found in your system PATH.
    echo Please install Python 3.10+ and try again.
    pause
    exit /b 1
)

:: Create virtual environment if it does not exist
if not exist .venv (
    echo Creating .venv directory...
    python -m venv .venv
    if %errorlevel% neq 0 (
        echo [ERROR] Failed to create virtual environment.
        pause
        exit /b 1
    )
) else (
    echo .venv already exists.
)

:: Upgrade pip and install requirements
echo.
echo Upgrading pip inside virtual environment...
.venv\Scripts\python -m pip install --upgrade pip

echo.
echo Installing dependencies from requirements.txt...
.venv\Scripts\pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo [ERROR] Failed to install dependencies.
    pause
    exit /b 1
)

echo.
echo ===================================================
echo Environment Setup Complete!
echo You can now launch the application by running run.bat
echo ===================================================
pause
