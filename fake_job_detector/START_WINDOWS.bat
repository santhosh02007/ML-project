@echo off
setlocal
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
 echo First run SETUP_WINDOWS.bat.
 pause
 exit /b 1
)
echo Keep this window open. Open http://127.0.0.1:8000 after Models ready.
".venv\Scripts\python.exe" run.py
pause
