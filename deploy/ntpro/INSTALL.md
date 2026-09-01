# Gyro Repeater — NTPRO Integration & On-Site Install Guide

## A. NTPRO PC (simulator station)

1. Copy `gyrorepeater.uhs` and `gyroudp.cfg` into the NTPRO UHI folder
   (same folder that holds `OVERHEAD.CFG` / `OverheadDef.uhs`).
2. **NmeaPort.dll is serial-only** (confirmed from the DLL itself: 4800 8N1,
   COM-port transport, no UDP). So the NTPRO side needs a tiny bridge:
   - Copy the `NmeaPort.dll` plugin block from your working NMEA configuration
     into `gyroudp.cfg` **unchanged** — serial output to a COM port, exactly
     like the overhead panel link. Use a free physical port or a virtual pair
     (com0com) if none is free.
   - The COM port/baud are NOT set in the .cfg: NmeaPort.dll has its own
     settings window (`NmeaPortWindow`). In Nmea.exe, open the NmeaPort window
     for this link and select **COM3 (placeholder — use your free port),
     4800 baud, 8N1** — matching the bridge defaults.
   - On the NTPRO PC: `pip install pyserial`, edit `COM_PORT`/`TARGET` at the
     top of `serial_to_udp.py`, then run `run_bridge.bat`. It forwards every
     `$...` sentence from the COM port to UDP broadcast 192.168.0.255:4001.
   Note: `gyrorepeater.uhs` uses script ID `MBSEN "|3"` (your existing links use
   1 and 2). If your `[SerialToAddress]` section routes by Script_ID, map 3 to
   the chosen COM port — otherwise leave it empty as in `OVERHEAD.CFG`.
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
6. Optional autostart: run `deploy\install-autostart.bat` once as Administrator
   (Task Scheduler, starts at logon) — or use NSSM for a true service.

## B2. Older Windows (7 / Server 2008)

- Install **Python 3.8.x** (last version supporting Win7/2008) — the backend is 3.8-compatible.
- Use **Chrome 109** or **Firefox ESR 115** (last Win7 builds) — the repeater UI works there.
- Alternative: run the backend on a newer PC and simply open
  `http://<backend-pc-ip>:8000` from the Win7 station's browser — any number of
  stations can view the same repeater simultaneously.

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
