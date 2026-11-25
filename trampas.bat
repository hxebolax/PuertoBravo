@echo off
chcp 65001 >nul
cd /d "%~dp0"
if not exist ".venv\Scripts\pythonw.exe" (
    echo No existe el entorno. Ejecuta primero entorno.bat
    pause
    exit /b 1
)
start "" ".venv\Scripts\pythonw.exe" trampas_gui.py
