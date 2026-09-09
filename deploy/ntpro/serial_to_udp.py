# ============================================================
#  NTPRO Gyro Repeater - Serial (NmeaPort.dll) -> UDP bridge
#  Runs on the NTPRO PC. Reads NMEA sentences from the COM port
#  that NmeaPort.dll writes to and broadcasts them on the LAN.
#
#  Requires: pip install pyserial
#  (Windows 7 / Server 2008: use Python 3.8 + pyserial 3.5)
# ============================================================
import socket
import sys
import time

import serial  # pyserial

# ----- CONFIGURE THESE -----
# com0com pair: NmeaPort (or com_test_writer.py) WRITES to COM3,
# this bridge READS from the OTHER end = COM4.
COM_PORT = "COM4"            # READ end of the pair (NOT the port NmeaPort uses!)
BAUD = 4800                  # NmeaPort.dll default: 4800 8N1
# TARGET examples (your LAN):
#   same-PC test        -> ("127.0.0.1", 4001)
#   two-PC (UNICAST, recommended): NTPRO PC=192.168.0.10, repeater PC=192.168.0.20
#                       -> ("192.168.0.20", 4001)
#   whole-LAN broadcast -> ("192.168.0.255", 4001)  (needs /24 mask; skip if LAN restricted)
TARGET = ("192.168.0.20", 4001)
# ----------------------------


def main():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    print(f"Bridge: {COM_PORT} @{BAUD} 8N1 -> UDP {TARGET[0]}:{TARGET[1]} (broadcast)")
    while True:
        try:
            with serial.Serial(COM_PORT, BAUD, bytesize=8, parity="N",
                               stopbits=1, timeout=1) as port:
                print("Port open. Forwarding NMEA...")
                count = 0
                last_line = None
                last_report = time.time()
                while True:
                    line = port.readline()
                    if line.startswith(b"$"):
                        sock.sendto(line.strip() + b"\r\n", TARGET)
                        count += 1
                        last_line = line.strip().decode("ascii", "ignore")
                    now = time.time()
                    if now - last_report >= 2:
                        if count:
                            print(f"OK  forwarded {count} sentences | last: {last_line}")
                        else:
                            print("... port SILENT (no NMEA) - check: Nmea.exe link running? "
                                  "NmeaPort window -> COM3, this script reads the OTHER end (COM4)? "
                                  "simulator running?")
                        count = 0
                        last_report = now
        except serial.SerialException as e:
            print(f"Serial error: {e} - retrying in 3 s")
            time.sleep(3)
        except KeyboardInterrupt:
            sys.exit(0)


if __name__ == "__main__":
    main()
