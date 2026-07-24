@echo off
echo =========================================================
echo 🚀 SolarScan Webots Drone Mission Control (FastAPI Server)
echo =========================================================

:: Check if virtual environment exists
if not exist .venv (
    echo [INFO] Virtual environment (.venv) not found. Running environment setup...
    call setup_env.bat
)

echo Starting FastAPI Web Server at http://localhost:8000 ...
echo =========================================================

:: Webots Environment Variables setup
set WEBOTS_HOME=C:\Program Files\Webots
set PYTHONPATH=%WEBOTS_HOME%\lib\controller\python;%PYTHONPATH%
set PATH=%WEBOTS_HOME%\lib\controller;%PATH%

:: Run the FastAPI application
.venv\Scripts\python main.py
pause
