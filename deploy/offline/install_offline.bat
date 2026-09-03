@echo off
rem ============================================================
rem  OFFLINE installer - no internet needed on the repeater PC.
rem  Run in Command Prompt from the deploy\offline folder:
rem
rem    install_offline.bat wheels-py38     (Python 3.8 - Win7/2008)
rem    install_offline.bat wheels-py312    (Python 3.10-3.12 - Win10/11)
rem ============================================================
if "%~1"=="" (
  echo Usage:  install_offline.bat wheels-py38     for Python 3.8 ^(Windows 7 / 2008^)
  echo         install_offline.bat wheels-py312    for Python 3.10-3.12 ^(Windows 10 / 11^)
  pause
  exit /b 1
)
python -m pip install --no-index --find-links "%~dp0%~1" fastapi uvicorn websockets python-dotenv pyserial
echo.
echo Done. If no errors above, run run.bat in the backend folder.
pause
