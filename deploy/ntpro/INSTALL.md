# Gyro Repeater — NTPRO Integration & On-Site Install Guide

## A. NTPRO PC (simulator station)

1. Copy `gyrorepeater.uhs` and `gyroudp.cfg` into the NTPRO UHI folder
   (same folder that holds `OVERHEAD.CFG` / `OverheadDef.uhs`).
2. Open `gyroudp.cfg` and fill the `[Plugins]` section: copy the `NmeaPort.dll`
   block from your working NMEA configuration and set its output to
   **UDP → 192.168.0.255 : 4001**. Do not change anything else.
   Note: `gyrorepeater.uhs` uses script ID `MBSEN "|3"` (your existing links use
   1 and 2). If your `[SerialToAddress]` section routes by Script_ID, map 3 to
   the UDP output — otherwise leave it empty as in `OVERHEAD.CFG`.
3. Register the new link file the same way `OVERHEAD.CFG` is registered
   (add `gyroudp.cfg` to `uhi.cfg`, or start it via `Nmea.exe` alongside the
   overhead panel link).
4. Start the simulator and confirm Nmea.exe shows the new script running.

## B. Repeater PC (any Windows PC on the same LAN)

1. Install Python 3.10+ (python.org, tick "Add to PATH").
2. Copy the `backend/` folder and the frontend `build/` folder to e.g. `C:\gyro-repeater\`.
   - Build the frontend once: `cd frontend && yarn build` (do this before copying,
     or copy a pre-built `build/` folder).
3. `pip install -r requirements.txt`
4. Run `deploy\firewall-setup.bat` **once as Administrator** (allows inbound UDP 4001).
5. Run `deploy\run.bat` — console shows the backend listening on UDP 4001 / HTTP 8000.
   (run.bat already sets `SIMULATOR_MODE=false`.)
6. Optional autostart: put a shortcut to `run.bat` in
   `shell:startup`, or use NSSM/Task Scheduler to run it as a service.

## C. Verify (browser-first, no packet sniffing)

1. On any LAN PC open `http://<repeater-pc-ip>:8000`, press **F**.
2. Status LED (top right):
   - **Green LIVE** + no **SIM** badge → real NTPRO data flowing. Done.
   - **Red NO DATA** → NTPRO side isn't sending or firewall blocks it
     (re-check step A2/A3 and B4).
   - **SIM badge visible** → run.bat didn't apply; SIMULATOR_MODE is still true.
3. Change heading on the Instructor Station → card follows within ~200 ms.
4. **Scale check**: compare the digital readout with the instructor's gyro.
   - Matches (e.g. 278.5° vs 278.5°) → nothing to do.
   - Off by 10x or rounded to whole degrees → `uhiGyroHeading` format differs;
     adjust the assign line in `gyrorepeater.uhs` (e.g. divide by 10) and restart
     the UHI link.

## D. Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| Red NO DATA, Nmea.exe shows script running | Windows firewall on repeater PC | Re-run firewall-setup.bat as Admin |
| Red NO DATA, other LAN PCs work | NTPRO PC firewall blocks outbound broadcast | Allow Nmea.exe outbound UDP, or switch gyroudp.cfg to unicast to the repeater PC IP |
| LED green but heading frozen | Sim paused / heading static in scenario | Normal — LED stays green while packets arrive |
| Checksum errors in backend log | Plugin already appends `T*cs` differently | Parser ignores bad frames; check the sentence in the footer pill |
| Broadcast not allowed on LAN | Network policy | Change 192.168.0.255 to the repeater PC's IP (unicast) in gyroudp.cfg |
