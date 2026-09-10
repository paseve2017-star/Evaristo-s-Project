# ============================================================
#  Lists all COM ports Windows currently sees.
#  Run:  python list_com_ports.py
#  Use it to confirm the com0com pair (COM3/COM4) really exists
#  BEFORE starting run_bridge.bat.
# ============================================================
import serial.tools.list_ports

ports = list(serial.tools.list_ports.comports())
if not ports:
    print("NO COM ports found on this PC.")
else:
    print("COM ports found:")
    for p in ports:
        print(f"  {p.device}  -  {p.description}")
