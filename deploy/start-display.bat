@echo off
rem ============================================================
rem  Gyro Repeater DISPLAY auto-launcher (fullscreen kiosk)
rem
rem  Setup (once):
rem    1. Make sure install-autostart.bat was run (backend
rem       autostarts at logon).
rem    2. Press Win+R, type:  shell:startup   , Enter
rem    3. Copy a SHORTCUT to this file into that folder.
rem  From then on: boot -> logon -> fullscreen gyro repeater.
rem ============================================================

set URL=http://localhost:8000

rem --- locate Chrome (adjust if installed elsewhere) ---
set CHROME="C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"
if not exist %CHROME% set CHROME="C:\Program Files\Google\Chrome\Application\chrome.exe"

rem --- give the backend a moment to come up after logon ---
timeout /t 10 /nobreak >nul

start "" %CHROME% --kiosk %URL%
exit
