@echo off
setlocal
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
    where py >nul 2>nul
    if not errorlevel 1 (py -3.13 -m venv .venv) else (python -m venv .venv)
    if errorlevel 1 goto fail
)
".venv\Scripts\python.exe" -m pip install -r requirements-dev.txt
if errorlevel 1 goto fail
".venv\Scripts\python.exe" -c "import PySide6, edge_tts, PyInstaller, pytest; print('Development environment ready.')"
if errorlevel 1 goto fail
exit /b 0
:fail
echo Development setup failed. Install Python 3.13 x64 and check your connection.
exit /b 1
