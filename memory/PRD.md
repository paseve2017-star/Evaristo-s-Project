# NTPRO Software Gyro Compass Repeater — PRD

## Original problem statement
Fullscreen web-based gyro compass repeater displaying live true heading from the Transas NTPRO 5000 simulator. NTPRO's UHI broadcasts NMEA `$HEHDT` over UDP on the LAN; a FastAPI backend listens, parses, and streams heading to a React frontend over WebSocket, rendering a traditional rotating analog compass rose (top-view, full 360°, usable to take bearings in any direction), fixed red lubber line, and a large digital heading readout. Runs fullscreen on a dedicated monitor.

## User choices (locked)
- UDP port: **4001**, bound to **0.0.0.0**
- Dev/testing: **built-in simulator mode** emits synthetic `$HEHDT` to 127.0.0.1:4001 at 10 Hz (SIMULATOR_MODE=true)
- Digital heading format: **tenths** (278.5°) with TRUE label
- MongoDB heading history log: **skipped** (v1)
- Top-view fullscreen rose with bearing-taking at any direction

## Architecture
```
[NTPRO / simulator] --$HEHDT UDP:4001--> [FastAPI :8001]
  asyncio UDP listener -> NMEA parser (checksum-verified) -> WebSocket /api/ws/heading (10 Hz)
                                              + /api/health (last-packet-age)
        ^                                              |
        |________ React frontend (wss, auto-reconnect, rAF smoothing) ___|
```

## Implemented (2026-09-01)
- Backend `/app/backend/server.py`: asyncio UDP listener (0.0.0.0:4001), checksum-verified HDT parser, 10 Hz WebSocket broadcaster (`/api/ws/heading`), `/api/health`, built-in simulator loop with realistic turn dynamics.
- Frontend: SVG 360° compass card (1°/5°/10° ticks, tens labels, cardinals N red-highlighted + intercardinals), unwrapped-angle rAF smoothing (no 360→0 snap), fixed red lubber line, center digital readout (tenths, JetBrains Mono, TRUE label).
- Bearing sight tool: click/drag anywhere on rose; cyan bearing line + TB/RB readouts; reset/toggle buttons.
- Connection LED: green LIVE / amber STALE (>2 s) / red NO DATA, with glow.
- Fullscreen via F key or button; shortcuts F/B/R/S; settings dialog (WS URL override persisted, UDP port, source mode, packet count, last sender); raw NMEA sentence pill in footer.
- Config in `/app/backend/.env`: UDP_PORT, UDP_HOST, SIMULATOR_MODE.

## Test status
Iteration 1 (2026-09-01): backend 6/6 pytest (`/app/backend/tests/test_gyro_repeater.py`), frontend 100%. Parser robustness verified (malformed/bad-checksum rejected, custom valid HDT accepted).

## Backlog (prioritized)
- P0: Deploy to NTPRO LAN PC; create UHI files (`gyroudp.cfg` + `gyroudp.uhs`, timer 100 ms) using NmeaPort.dll pattern; verify `uhiGyroHeading` units/scale; Wireshark/netcat validation.
- P1: Windows packaging (run.bat / service), serve frontend static build from FastAPI for `http://<backend-ip>:8000` access; configurable talker ID filter.
- P2: Rate-of-turn indicator, 60 s heading strip chart, VTG COG/SOG panel, MongoDB history log (24 h TTL), RS-422 physical repeater bridge, multi-station support.

## Session state (2026-09-02: v2 features added)
- App fully working (simulator mode ON). Deploy package complete in /app/deploy/.
- v2 (2026-09-02): ROT indicator (bar ±30°/min, PORT red/STBD green + digital), VTG panel (COG/SOG), 60 s heading strip chart (HeadingChart, unwrapped angles). Backend parses $--ROT/$--VTG (verified_body helper); simulator emits HDT+ROT+VTG at 10 Hz with realistic ±30°/min turns.
- gyrorepeater.uhs now also assigns TEROT + TEVTG; deploy/install-autostart.bat (Task Scheduler, Win7-compatible) added; INSTALL.md gained legacy-Windows section (Python 3.8, Chrome 109/FF ESR 115, or backend on newer PC + Win7 as viewer).
- Tests: 13/13 pass (test_gyro_repeater.py hardened: flood-thread pattern for custom-sentence test, longer poll for drift test; new test_rot_vtg.py).
- KEY FINDING (2026-09-02): user uploaded NmeaPort.dll v5.10.5450; string analysis shows it is SERIAL-ONLY (4800 8N1, "Port = (%s)", GetPrivateProfileSectionA; no UDP/TCP). Integration path changed: NmeaPort writes to a COM port as usual + deploy/ntpro/serial_to_udp.py bridge (pyserial, broadcasts COM lines to 192.168.0.255:4001) + run_bridge.bat on the NTPRO PC.
- Frontend production build created (2026-09-02): /app/frontend/build exists and backend now serves it at / (verified GET / → 200). Single-process deploy ready: export repo → repeater PC needs only backend/, frontend/build/, deploy/.
- User exported the project to GitHub and downloaded it (2026-09-02). Going on-site to install: bridge on NTPRO PC (COM3 placeholder, 4800 8N1 via NmeaPort window), backend+build on repeater PC. Next contact will likely be on-site results: expect LED red/green outcome, possible COM port mismatch or scale issue — INSTALL.md troubleshooting table covers known cases.

## Next tasks
1. ON-SITE ISSUE (2026-09-02): pip install of full requirements.txt failed on repeater PC ("no matching distribution for fastapi 0.110.1, from versions: none" = pip can't reach PyPI or Python too old). Fix provided: deploy/requirements-repeater.txt (minimal: fastapi, uvicorn[standard], python-dotenv — unpinned minimums) + INSTALL.md updated with upgrade-pip and offline-wheel instructions. Awaiting user's retry result (need python --version if it still fails).
2. NTPRO-side files authored (2026-09-01): deploy/ntpro/gyrorepeater.uhs (timer 100 ms, TEHDT only, mirrors OverheadDef.uhs pattern — CONFIRMED against user's full OverheadDef.uhs paste; overhead runs at 200 ms/5 Hz, repeater uses 100 ms/10 Hz) + gyroudp.cfg (broadcast 192.168.0.255:4001; [Plugins] block to be copied from user's working NmeaPort.dll config) + INSTALL.md (browser-first verification, scale check, troubleshooting).
2. On-site: user fills gyroudp.cfg [Plugins] from their working NmeaPort config, runs firewall-setup.bat + run.bat on repeater PC, verifies via status LED (green, no SIM badge) and heading scale check.
3. Optional: Windows autostart via shell:startup or NSSM; unicast fallback if broadcast is blocked.
