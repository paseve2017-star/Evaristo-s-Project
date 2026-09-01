@echo off
rem ============================================================
rem  Serial -> UDP bridge for the NTPRO PC.
rem  Edit COM_PORT / TARGET inside serial_to_udp.py first.
rem  Requires: pip install pyserial
rem ============================================================
cd /d %~dp0
python serial_to_udp.py
pause
