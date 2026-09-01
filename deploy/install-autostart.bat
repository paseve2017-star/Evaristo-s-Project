@echo off
rem ============================================================
rem  Registers the Gyro Repeater backend to start automatically
rem  at user logon via Task Scheduler. Run as Administrator ONCE.
rem  Works on Windows 7 / 2008 / 10 / 11 (schtasks is built-in).
rem ============================================================
schtasks /create /tn "NTPRO Gyro Repeater" /tr "\"%~dp0run.bat\"" /sc onlogon /rl highest /f
echo.
echo Task created. The repeater will start automatically at logon.
echo To remove later:  schtasks /delete /tn "NTPRO Gyro Repeater" /f
pause
