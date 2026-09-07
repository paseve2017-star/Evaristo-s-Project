# ============================================================
#  COM pair isolation test - NTPRO Gyro Repeater
#  Writes a valid $HEHDT sentence to COM3 once per second.
#
#  PURPOSE: prove the com0com pair + bridge work WITHOUT NmeaPort.
#  Run this WHILE run_bridge.bat is running:
#     - Bridge prints "OK forwarded..."  -> pair+bridge OK.
#       The silence fault is on the NmeaPort/UHI side.
#     - Bridge stays "port SILENT"       -> com0com pair wrong
#       (wrong port names / driver issue), NmeaPort is not the problem.
#
#  Requires: pyserial.  Set WRITE_PORT to the port NmeaPort WOULD use.
# ============================================================
import time

import serial

WRITE_PORT = "COM3"   # the end NmeaPort writes to (bridge reads the other end)
BAUD = 4800


def nmea(sentence_body: str) -> bytes:
    cs = 0
    for ch in sentence_body:
        cs ^= ord(ch)
    return f"${sentence_body}*{cs:02X}\r\n".encode("ascii")


def main():
    heading = 123.4
    with serial.Serial(WRITE_PORT, BAUD, bytesize=8, parity="N",
                       stopbits=1, timeout=1) as port:
        print(f"Writing test $HEHDT to {WRITE_PORT} @{BAUD} 8N1, 1 Hz. Ctrl+C to stop.")
        while True:
            sentence = nmea(f"HEHDT,{heading:.1f},T")
            port.write(sentence)
            print("sent:", sentence.decode().strip())
            heading = (heading + 0.5) % 360
            time.sleep(1)


if __name__ == "__main__":
    main()
