"""Tests for v2 features: ROT/VTG parsing + WebSocket rot/cog/sog fields."""
import asyncio
import json
import os
import socket
import time

import pytest
import requests
import websockets

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://compass-display.preview.emergentagent.com").rstrip("/")
WS_URL = BASE_URL.replace("http", "ws") + "/api/ws/heading"
UDP_PORT = 4001


def nmea_cs(body: str) -> str:
    cs = 0
    for ch in body:
        cs ^= ord(ch)
    return f"{cs:02X}"


def build(body: str) -> bytes:
    return f"${body}*{nmea_cs(body)}\r\n".encode("ascii")


def udp_send(payload: bytes):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.sendto(payload, ("127.0.0.1", UDP_PORT))
    s.close()


class TestWebSocketFields:
    """v2: rot/cog/sog appear in WS payload with simulator on."""

    @pytest.mark.asyncio
    async def test_ws_has_rot_cog_sog(self):
        async with websockets.connect(WS_URL, open_timeout=10) as ws:
            msgs = []
            start = time.time()
            while time.time() - start < 2.0 and len(msgs) < 15:
                raw = await asyncio.wait_for(ws.recv(), timeout=2)
                msgs.append(json.loads(raw))
            m = msgs[-1]
            assert "rot" in m and isinstance(m["rot"], (int, float)), m
            assert "cog" in m and isinstance(m["cog"], (int, float)), m
            assert "sog" in m and isinstance(m["sog"], (int, float)), m
            # simulator realism: |rot| <= 30 deg/min
            assert abs(m["rot"]) <= 30.001, f"ROT out of range: {m['rot']}"
            assert 0 <= m["cog"] < 360
            assert 0 <= m["sog"] < 50

    @pytest.mark.asyncio
    async def test_custom_rot_vtg_reflected_in_ws(self):
        """Burst-send $HEROT,-12.5 and $HEVTG,091.2,T,,M,10.3,N,,K; expect them in WS."""
        rot_pkt = build("HEROT,-12.5,A")
        vtg_pkt = build("HEVTG,091.2,T,,M,10.3,N,,K")
        async with websockets.connect(WS_URL, open_timeout=10) as ws:
            seen_rot = seen_cog = seen_sog = False
            deadline = time.time() + 6.0
            while time.time() < deadline and not (seen_rot and seen_cog and seen_sog):
                for _ in range(3):
                    udp_send(rot_pkt)
                    udp_send(vtg_pkt)
                try:
                    raw = await asyncio.wait_for(ws.recv(), timeout=0.5)
                except asyncio.TimeoutError:
                    continue
                m = json.loads(raw)
                if isinstance(m.get("rot"), (int, float)) and abs(m["rot"] - (-12.5)) < 0.05:
                    seen_rot = True
                if isinstance(m.get("cog"), (int, float)) and abs(m["cog"] - 91.2) < 0.05:
                    seen_cog = True
                if isinstance(m.get("sog"), (int, float)) and abs(m["sog"] - 10.3) < 0.05:
                    seen_sog = True
            assert seen_rot, "Custom ROT -12.5 never appeared in WS stream"
            assert seen_cog, "Custom COG 91.2 never appeared in WS stream"
            assert seen_sog, "Custom SOG 10.3 never appeared in WS stream"


class TestParserRejection:
    """Malformed / bad-checksum ROT & VTG should not crash and should be ignored."""

    def test_bad_checksum_rot_ignored(self):
        udp_send(b"$HEROT,-99.9,A*00\r\n")
        time.sleep(0.3)
        r = requests.get(f"{BASE_URL}/api/health", timeout=5)
        assert r.status_code == 200
        assert r.json()["status"] == "ok"

    def test_bad_checksum_vtg_ignored(self):
        udp_send(b"$HEVTG,999.9,T,,M,999.9,N,,K*00\r\n")
        time.sleep(0.3)
        r = requests.get(f"{BASE_URL}/api/health", timeout=5)
        assert r.status_code == 200

    def test_short_rot_body_ignored(self):
        # Correct checksum but too few fields
        udp_send(build("HEROT"))
        time.sleep(0.3)
        r = requests.get(f"{BASE_URL}/api/health", timeout=5)
        assert r.status_code == 200

    def test_short_vtg_body_ignored(self):
        udp_send(build("HEVTG,10,T"))  # only 3 fields (<6 required)
        time.sleep(0.3)
        r = requests.get(f"{BASE_URL}/api/health", timeout=5)
        assert r.status_code == 200

    def test_non_numeric_rot_ignored(self):
        udp_send(build("HEROT,ABC,A"))
        time.sleep(0.3)
        r = requests.get(f"{BASE_URL}/api/health", timeout=5)
        assert r.status_code == 200
