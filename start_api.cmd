@echo off
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
    echo Project Python not found: .venv\Scripts\python.exe
    exit /b 1
)
".venv\Scripts\python.exe" -m uvicorn api.api_main:app --host 127.0.0.1 --port 8000 %*
