# USB Joystick via UHI — Refresher Guide (NTPRO)

Based on YOUR OWN working uhi.cfg (the one used for VRConsole/joystick before).

## The pattern (from your working file)

```ini
[Default]
vrconsole.uhs            ; script that maps hid* -> uhi* variables
;trace_hid.uhs           ; <-- UNCOMMENT THIS to discover port numbers!

[Plugins]

[Variables]
; Analog axes:  ain\unit#N\port#M  wrapped in calibrate(...)
hidRudder = calibrate(ain\unit#1\port#4, 0, -35, 2100, 0, 2300, 0, 4095, +35)
hidTeleL  = calibrate(ain\unit#1\port#6, 0, -10, 2100, 0, 2200, 0, 4095, +10)
hidTeleR  = calibrate(ain\unit#1\port#7, 0, -10, 2100, 0, 2200, 0, 4095, +10)

; Buttons:      din\unit#N\port#M  (digital in, no calibrate needed)
hidBtn1 = din\unit#1\port#1
hidBtn2 = din\unit#1\port#2
; ... hidBtn3..hidBtn12 same pattern

[HardwareGroups]
hwgroup.cfg
```

## Step-by-step

### 1. Windows side
- Plug in the joystick. Open `joy.cpl` (Start → Run → joy.cpl) →
  confirm the device appears and axes/buttons move in the test window.
- If multiple HID devices: `unit#1` = first device, `unit#2` = second, etc.

### 2. Discover which port each axis/button is on
- In your link cfg, **comment out** `vrconsole.uhs` and **uncomment** `trace_hid.uhs`:
  ```ini
  [Default]
  ;vrconsole.uhs
  trace_hid.uhs
  ```
- Start the UHI link (Nmea.exe / UhiProcessor as usual).
- Move each axis and press each button — the trace shows which
  `port#N` fires. Write them down (e.g. rudder axis = port#4).

### 3. Map the variables
- Restore `vrconsole.uhs` as [Default], comment `trace_hid.uhs` again.
- In `[Variables]`, put the discovered port numbers into the
  `calibrate(ain\unit#1\port#N, ...)` lines (axes) and
  `din\unit#1\port#N` lines (buttons).
- **Reuse your old calibrate numbers as-is** — they already match your
  hardware's raw range (0..4095) and desired output (-35..+35 deg rudder,
  -10..+10 telegraph). Only change the port# if the axis moved.
- Axis reversed? Swap the output sign (e.g. -35 <-> +35) or the raw endpoints.

### 4. How it flows
```
USB joystick → Windows HID → UHI (ain/din addresses)
  → [Variables] calibrate() → hid* variables
  → vrconsole.uhs (assign) → uhi* variables → simulator
```

### 5. Test
- Start the link, run the simulator, move the stick.
- Rudder/telegraph should respond on the own-ship controls.
- No response? Check: (a) link actually started, (b) unit# correct,
  (c) port# from trace step, (d) vrconsole.uhs assigns the uhi* vars.

## calibrate() quick reference (from your working lines)

```
calibrate(ain\unit#1\port#4, 0, -35, 2100, 0, 2300, 0, 4095, +35)
          └─ source           └──────────────────────────────┘
            raw->output mapping incl. center deadzone
            (raw 0 → -35°, raw ~2100-2300 → 0° deadzone, raw 4095 → +35°)
```

Raw range 0..4095 = 12-bit analog input. Keep your proven numbers;
only adjust port# (and endpoints if you swap joystick model).
