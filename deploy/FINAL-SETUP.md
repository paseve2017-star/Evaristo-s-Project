# NTPRO Gyro Compass Repeater — FINAL WORKING SETUP (as-built, verified on-site 2026-09)

## Architecture (what's actually running)

```
[NTPRO PC 192.168.0.10]                      [Repeater PC 192.168.0.20]
 Instructor Station / simulator               NTPRO Host Station (NTconfig)
        │  NTPRO LAN protocol                        │
        ▼                                            ▼
                              NMEA interface (Config Editor) → COM3, 4800 8N1
                                                              │  com0com pair
                                                              ▼
                                                     COM4 → serial_to_udp.py
                                                     TARGET ("127.0.0.1", 4001)
                                                              │  UDP localhost
                                                              ▼
                                                     run.bat (FastAPI :8000)
                                                              │
                                                              ▼
                                                     Chrome --kiosk http://localhost:8000
                                                     (plain full-screen compass card)
```

The heading rides NTPRO's own station networking to the Repeater PC;
the local com0com pair hands it to the bridge; everything after that is localhost.

---

## ONE-TIME SETUP

### A. Repeater PC (192.168.0.20)

1. **com0com** — install v3.0.0.0 (signed), create/rename pair to **COM3 ↔ COM4**:
   ```
   setupc list
   setupc change CNCA0 PortName=COM3     (if needed)
   setupc change CNCB0 PortName=COM4     (if needed)
   ```
   Then **reboot once** (required — ports won't open before the reboot).
2. **NTconfig** — the Repeater PC is an additional Host Station; assign the
   **NMEA interface** to this station, port **COM3, 4800 8N1**. Save config,
   set as default.
3. **Python 3.8.x** (Win7/2008) or 3.10+ (Win10/11) — tick "Add to PATH".
4. **Project files** — copy from the GitHub export, keeping layout:
   ```
   C:\gyro-repeater\
     ├── backend\
     ├── frontend\build\
     └── deploy\
   C:\gyro-bridge\
     ├── serial_to_udp.py      (COM_PORT="COM4", TARGET=("127.0.0.1",4001))
     ├── run_bridge.bat
     └── list_com_ports.py     (diagnostic)
   ```
5. **Dependencies (offline)**:
   ```
   cd C:\gyro-repeater\deploy\offline
   install_offline.bat wheels-py38      rem or wheels-py312
   ```
6. **Firewall** — run `deploy\firewall-setup.bat` as Administrator (once).
7. **Autostart (optional)** — `deploy\install-autostart.bat` as admin (backend at
   logon) + shortcut to `deploy\start-display.bat` in `shell:startup`
   (kiosk display at logon).

### B. NTPRO PC (192.168.0.10)

- Nothing extra! Only its normal role: NTconfig knows the Repeater station,
  and the simulator runs here. (com0com/bridge NOT needed on this PC in this
  architecture. The old gyroudp.cfg/gyrorepeater.uhs custom-link files are
  NOT used — the built-in NMEA interface replaced them.)

---

## DAILY STARTUP (in order)

1. **NTPRO PC**: start the simulator (scenario running).
2. **Repeater PC**: NTPRO station software running (NMEA interface live).
3. **Repeater PC**: `run_bridge.bat` → expect
   `OK forwarded N sentences | last: $HEHDT,<heading>,T*..`
4. **Repeater PC**: `run.bat` (skip if autostart installed).
5. **Display**: browser → `http://localhost:8000` (plain card). Press **F** for
   fullscreen if not using the kiosk shortcut.

(With both autostarts installed, step 3–5 are automatic at boot: logon →
backend starts (Task Scheduler) → 10 s → Chrome kiosk opens.)

---

## DISPLAY MODES (change via URL, no reinstall)

| URL | What shows |
|---|---|
| `http://localhost:8000` | Plain analog card only (default) |
| `?digital=1` | + center digital readout |
| `?bearing=1` | + bearing sight tool (TB/RB, drag on card) |
| `?hud=1` | + top/bottom status bars (LED, NMEA feed, settings) |
| `?panel=1` | everything (diagnostic mode) |
| combos | `?digital=1&bearing=1` etc. |

Keyboard (both modes): **F** fullscreen, **S** settings (WS override if ever needed).

---

## VERIFICATION

| Check | Where | Expected |
|---|---|---|
| Bridge receiving | bridge console | `OK forwarded … $HEHDT,<real heading>` |
| Backend receiving | `http://localhost:8000/api/health` | `"stale": false`, packets increasing |
| Display | repeater screen | card tracks instructor gyro (~1 Hz) |
| COM ports exist | `python list_com_ports.py` | COM3 + COM4 listed |

## TROUBLESHOOTING

| Symptom | Cause | Fix |
|---|---|---|
| Bridge: `could not open port COM4` | com0com not installed/renamed, or no reboot after install | setupc list / change / install, then REBOOT |
| Bridge: `port SILENT` | NMEA interface not assigned to this station or sim/station not running | NTconfig assignment, COM3 in interface config, sim running |
| Page loads, card frozen + red LED (panel mode) | bridge not running or TARGET wrong | start run_bridge.bat; TARGET must be 127.0.0.1 |
| "frontend build not found" | frontend\build missing or not next to backend\ | copy build folder, restart run.bat |
| `?panel=1` all dashes | WS override leftover | Settings (S) → Reset default |
