@echo off
rem ============================================================
rem  NTPRO Gyro Compass Repeater - backend launcher
rem  Double-click to start. Repeater UI: http://<this-pc-ip>:8000
rem ============================================================
cd /d %~dp0

set SIMULATOR_MODE=false
set UDP_HOST=0.0.0.0
set UDP_PORT=4001

echo Starting Gyro Repeater backend (UDP listen :%UDP_PORT%, HTTP :8000)...
python -m uvicorn server:app --host 0.0.0.0 --port 8000
pause
