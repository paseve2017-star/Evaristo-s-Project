# Gyro Repeater — NMEA Station Setup (Repeater PC as NTPRO Host Station)

Architecture when the Repeater PC is configured in NTconfig as an
additional Host Station with the NMEA interface assigned to it:

```
Instructor Station (.10) ── NTPRO LAN protocol ──▶ Repeater Station (.20)
                                                     NMEA interface → COM3
                                                       (com0com pair)
                                                     COM4 → serial_to_udp.py
                                                       TARGET 127.0.0.1:4001
                                                     → backend → browser
```

Everything data-critical stays on ONE machine — no UDP/firewall across the LAN;
the heading rides NTPRO's own station networking.

## Repeater PC (192.168.0.20) — all steps happen here

1. **com0com**: pair COM3 ↔ COM4 (installed already; if ports won't open,
   REBOOT once after install — known requirement).
2. **NTconfig / station config**: NMEA interface assigned to THIS station,
   port **COM3, 4800 8N1**; save configuration as default.
3. **Bridge**: `C:\gyro-bridge\serial_to_udp.py`:
   ```python
   COM_PORT = "COM4"
   BAUD = 4800
   TARGET = ("127.0.0.1", 4001)   # backend is on THIS PC
   ```
   (pyserial already installed by install_offline.bat — it includes pyserial.)
4. **Backend**: `C:\gyro-repeater\backend\run.bat`.
5. **Browser**: `http://localhost:8000` → plain card. Diagnostics: `?panel=1`.

## Startup order (daily)

1. Instructor Station: start simulator.
2. Repeater PC: NTPRO station software running (so its NMEA interface is live).
3. Repeater PC: `run_bridge.bat` → expect `OK forwarded … $HEHDT,<real heading>`.
4. Repeater PC: `run.bat` (if not autostarted) → open the browser.

## Verification

- Bridge console shows real heading sentences → page green/turning.
- `http://localhost:8000/api/health` → `"stale": false`, packets increasing.

## Fallback (Option B — NMEA stays on the NTPRO PC)

If the station-based NMEA output doesn't emit on COM3:
- On the **NTPRO PC (.10)**: NMEA interface → COM3, bridge COM_PORT=COM4,
  `TARGET = ("192.168.0.20", 4001)`.
- On the **Repeater PC (.20)**: firewall-setup.bat as admin (opens UDP 4001),
  `run.bat`, browser `http://localhost:8000`.
- This path was already proven in the single-PC test — only the UDP hop is new.
