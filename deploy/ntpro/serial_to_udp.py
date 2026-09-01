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
COM_PORT = "COM3"            # COM port NmeaPort.dll outputs to
BAUD = 4800                  # NmeaPort.dll default: 4800 8N1
TARGET = ("192.168.0.255", 4001)  # LAN broadcast : repeater port
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
                while True:
                    line = port.readline()
                    if line.startswith(b"$"):
                        sock.sendto(line.strip() + b"\r\n", TARGET)
        except serial.SerialException as e:
            print(f"Serial error: {e} - retrying in 3 s")
            time.sleep(3)
        except KeyboardInterrupt:
            sys.exit(0)


if __name__ == "__main__":
    main()
