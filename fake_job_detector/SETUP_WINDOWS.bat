@echo off
setlocal
cd /d "%~dp0"
echo Veritas - first-time setup
where py >nul 2>nul
if errorlevel 1 goto usepython
py -3 -c "import sys; assert (3,11) <= sys.version_info[:2] < (3,14), 'Use Python 3.11, 3.12 or 3.13'"
if errorlevel 1 goto failed
py -3 -m venv .venv
if errorlevel 1 goto failed
goto install
:usepython
python -c "import sys; assert (3,11) <= sys.version_info[:2] < (3,14), 'Use Python 3.11, 3.12 or 3.13'"
if errorlevel 1 goto failed
python -m venv .venv
if errorlevel 1 goto failed
:install
".venv\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 goto failed
echo.
echo Setup complete. Double-click START_WINDOWS.bat.
pause
exit /b 0
:failed
echo.
echo Setup failed. Read the error above. Install Python 3.12 with Add Python to PATH.
echo Internet is needed during setup. See README.md for manual steps.
pause
exit /b 1
