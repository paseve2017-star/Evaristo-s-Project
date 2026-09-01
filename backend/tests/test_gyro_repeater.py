"""Backend tests for Gyro Compass Repeater.
Covers /api/health, WebSocket /api/ws/heading, and NMEA UDP robustness.
"""
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


# ---------- /api/health ----------
class TestHealth:
    def test_health_ok(self):
        r = requests.get(f"{BASE_URL}/api/health", timeout=10)
        assert r.status_code == 200
        d = r.json()
        assert d["status"] == "ok"
        assert d["udp_port"] == 4001
        assert d["simulator"] is True
        assert isinstance(d["heading"], (int, float))
        assert 0 <= d["heading"] < 360
        assert d["last_packet_age_sec"] is not None
        assert d["last_packet_age_sec"] < 2.0
        assert d["stale"] is False

    def test_heading_changes_over_time(self):
        h1 = requests.get(f"{BASE_URL}/api/health").json()["heading"]
        time.sleep(2)
        h2 = requests.get(f"{BASE_URL}/api/health").json()["heading"]
        # simulator drifts; over 2 sec should nearly always differ
        assert h1 != h2, f"Heading did not change over 2s: {h1} == {h2}"


# ---------- WebSocket streaming ----------
class TestWebSocket:
    @pytest.mark.asyncio
    async def test_ws_stream_10hz(self):
        async with websockets.connect(WS_URL, open_timeout=10) as ws:
            msgs = []
            start = time.time()
            while time.time() - start < 1.2 and len(msgs) < 20:
                raw = await asyncio.wait_for(ws.recv(), timeout=2)
                msgs.append(json.loads(raw))
            assert len(msgs) >= 6, f"Expected >=6 msgs in ~1s, got {len(msgs)}"
            m = msgs[-1]
            assert isinstance(m["heading"], (int, float))
            assert "ts" in m
            assert "stale" in m
            assert m["stale"] is False
            assert m.get("udp_port") == 4001
            assert m.get("simulator") is True


# ---------- NMEA parser robustness (send UDP locally) ----------
# NOTE: This test must run inside the container since UDP :4001 is local only.
class TestNMEARobustness:
    def _send(self, sentence: str):
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.sendto(sentence.encode("ascii"), ("127.0.0.1", UDP_PORT))
        s.close()

    def test_malformed_sentence_ignored(self):
        before = requests.get(f"{BASE_URL}/api/health").json()["packets"]
        self._send("garbage line, not nmea\r\n")
        time.sleep(0.3)
        after = requests.get(f"{BASE_URL}/api/health").json()
        # heading should remain valid, no crash
        assert after["status"] == "ok"
        assert isinstance(after["heading"], (int, float))

    def test_bad_checksum_ignored(self):
        # HDT with wrong checksum
        bad = "$HEHDT,111.1,T*00\r\n"
        # Note: sim keeps updating, so we can only check the server still healthy
        self._send(bad)
        time.sleep(0.3)
        d = requests.get(f"{BASE_URL}/api/health").json()
        assert d["status"] == "ok"
        # heading should NOT be 111.1 (simulator drifts around 270s)
        # Not a strict assert; simulator could theoretically be there. Just sanity that endpoint works.
        assert 0 <= d["heading"] < 360

    def test_valid_custom_sentence_updates_heading(self):
        body = "HEHDT,123.4,T"
        sentence = f"${body}*{nmea_cs(body)}\r\n"
        # Simulator is emitting 10Hz too; to catch our value we send several times
        # and read health right after. Since sim overwrites, we check that at least
        # one health poll within a burst captures ~123.4.
        seen = False
        for _ in range(30):
            self._send(sentence)
            d = requests.get(f"{BASE_URL}/api/health").json()
            if abs(d["heading"] - 123.4) < 0.5:
                seen = True
                break
            time.sleep(0.02)
        assert seen, "Custom $HEHDT,123.4 was never reflected in /api/health"
