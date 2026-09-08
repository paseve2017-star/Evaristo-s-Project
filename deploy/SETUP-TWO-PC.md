# Gyro Repeater — Two-PC Setup Procedure (Final)

Machines:
- **NTPRO PC** (192.168.0.1, Windows 2008 Server, runs Instructor Station / simulator)
- **Repeater Station PC** (192.168.0.10, dedicated gyro display, 800×800 monitor)

---

## PART 1 — NTPRO PC (192.168.0.1) — one-time setup

### 1.1 Virtual COM pair (com0com)
1. Install com0com v3.0.0.0 (signed): `com0com-3.0.0.0-i386-and-x64-signed.zip` from SourceForge.
2. Open the com0com **Setup Command Prompt** and rename the pair:
   ```
   change CNCA0 PortName=COM3
   change CNCB0 PortName=COM4
   ```
3. Verify COM3 + COM4 appear in Device Manager → Ports.

### 1.2 NMEA output from the simulator (built-in feature — no UHI files needed)
1. Open **Instructor Station → Configuration Editor**.
2. Add/enable the **NMEA interface** (e.g. `NMEA_LOG_GYRO_ARPA`).
3. Assign it to **COM3**, **4800 baud, 8N1** (default was COM2 — change it).
4. **File → Configuration → Save As**, then **set as default** (required for persistence).

### 1.3 Bridge (serial → network)
1. Install Python 3.8.x (last for Win2008) — tick "Add to PATH".
2. Create `C:\gyro-bridge\` and copy from the project: `serial_to_udp.py`, `run_bridge.bat` (from `deploy\ntpro\`).
3. Install pyserial offline (from the project's `deploy\offline\` bundle):
   ```
   cd C:\gyro-bridge
   python -m pip install --no-index --find-links <path-to>\deploy\offline\wheels-py38 pyserial
   ```
4. Edit `serial_to_udp.py`:
   ```python
   COM_PORT = "COM4"                      # READ end of the pair (NMEA interface writes COM3)
   BAUD = 4800
   TARGET = ("192.168.0.10", 4001)        # the Repeater Station PC
   ```

---

## PART 2 — Repeater Station PC (192.168.0.10) — one-time setup

### 2.1 Software
1. Install Python 3.8.x (Win7/2008) or 3.10+ (Win10/11) — tick "Add to PATH".
2. Create `C:\gyro-repeater\` and copy from the project export, keeping this layout:
   ```
   C:\gyro-repeater\
     ├── backend\          (server.py, requirements.txt …)
     ├── frontend\build\   (index.html, static\ …)
     └── deploy\           (run.bat, firewall-setup.bat, offline\ …)
   ```
3. Install dependencies offline:
   ```
   cd C:\gyro-repeater\deploy\offline
   install_offline.bat wheels-py38      rem Python 3.8  (Win7/2008)
   install_offline.bat wheels-py312     rem Python 3.10–3.12 (Win10/11)
   ```

### 2.2 Firewall (once, as Administrator)
- Right-click `deploy\firewall-setup.bat` → **Run as administrator**
  (opens inbound UDP 4001 + TCP 4002).

### 2.3 Autostart (optional, as Administrator)
- Run `deploy\install-autostart.bat` → backend starts at every logon.

---

## PART 3 — Every-day operation

**On the NTPRO PC:**
1. Start the simulator (Instructor Station).
2. Double-click `run_bridge.bat` — expect:
   `Port open. Forwarding NMEA...` then `OK forwarded N sentences | last: $HEHDT,...`

**On the Repeater Station PC:**
1. Run `run.bat` (in `backend\`, or autostart) — console shows UDP :4001 / HTTP :8000.
2. Open the display:
   - Browser → `http://192.168.0.10:8000` → press **F** (fullscreen), or
   - Dedicated kiosk shortcut:
     `"C:\...\chrome.exe" --kiosk http://192.168.0.10:8000`
3. You get the **plain full-screen gyro card** (default). 
   For diagnostics (digital readout, bearing tool, status LED, settings) use
   `http://192.168.0.10:8000/?panel=1`.

---

## PART 4 — Verification & quick troubleshooting

| Check | Where | Expected |
|---|---|---|
| Bridge forwarding | NTPRO PC bridge console | `OK forwarded … $HEHDT,<heading>,T*…` |
| Backend receiving | any browser → `http://192.168.0.10:8000/api/health` | `"simulator": false`, `"stale": false`, heading numeric |
| Display live | repeater screen | card rotates with the Instructor Station gyro (~1 Hz) |

| Symptom | Fix |
|---|---|
| Bridge "port SILENT" | NMEA interface not on COM3 / not saved as default / sim not running |
| Bridge "Serial error" | wrong COM_PORT in serial_to_udp.py (must be COM4, the read end) |
| Page opens but nothing moves (panel mode: red NO DATA) | firewall rule missing on 192.168.0.10 → run firewall-setup.bat as admin |
| Page "frontend build not found" | `frontend\build` must sit NEXT TO `backend\`; restart run.bat after copying |
| Other LAN PCs can't open the page | use `http://192.168.0.10:8000` (not localhost); check Windows firewall HTTP 8000 |
