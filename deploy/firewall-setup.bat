@echo off
rem ============================================================
rem  One-time Windows firewall rule: allow inbound NMEA $HEHDT
rem  UDP broadcasts on port 4001. Run as Administrator ONCE.
rem ============================================================
netsh advfirewall firewall add rule name="NTPRO Gyro Repeater UDP 4001" dir=in action=allow protocol=UDP localport=4001
echo Done. Inbound UDP 4001 is now allowed.
pause
