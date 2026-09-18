@echo off
setlocal
cd /d "%~dp0"
call setup_dev.bat
if errorlevel 1 exit /b 1
".venv\Scripts\python.exe" -m pytest -q
if errorlevel 1 exit /b 1
".venv\Scripts\python.exe" tools\build.py
if errorlevel 1 exit /b 1
echo Installer and portable ZIP are in dist.
