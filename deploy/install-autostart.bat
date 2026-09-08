@echo off
rem ============================================================
rem  Registers the Gyro Repeater backend to start automatically
rem  at user logon via Task Scheduler. Run as Administrator ONCE.
rem  Works on Windows 7 / 2008 / 10 / 11 (schtasks is built-in).
rem
rem  Place this file NEXT TO run.bat (or in deploy\ one level
rem  above backend\run.bat) before running.
rem ============================================================

set "TARGET=%~dp0run.bat"
if not exist "%TARGET%" set "TARGET=%~dp0..\backend\run.bat"
if not exist "%TARGET%" (
  echo ERROR: could not find run.bat next to this script or in ..\backend\
  pause
  exit /b 1
)

schtasks /create /tn "NTPRO Gyro Repeater" /tr "\"%TARGET%\"" /sc onlogon /rl highest /f
echo.
echo Task created. The repeater will start automatically at logon.
echo Registered target: %TARGET%
echo To remove later:  schtasks /delete /tn "NTPRO Gyro Repeater" /f
pause
