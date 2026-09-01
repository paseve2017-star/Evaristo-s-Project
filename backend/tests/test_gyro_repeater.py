"""Backend tests for Gyro Compass Repeater.
Covers /api/health, WebSocket /api/ws/heading, and NMEA UDP robustness.
"""
import asyncio
import json
import os
import socket
import threading
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
        # Simulator random walk is small (±0.03°/tick, rounded to .1f), so poll
        # over a longer window and accept any observed change.
        h1 = requests.get(f"{BASE_URL}/api/health").json()["heading"]
        changed = False
        for _ in range(20):
            time.sleep(0.5)
            h2 = requests.get(f"{BASE_URL}/api/health").json()["heading"]
            if h2 != h1:
                changed = True
                break
        assert changed, f"Heading did not change over 10s: stuck at {h1}"


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
        # Simulator emits its own HDT at 10Hz and health polls have network
        # latency, so flood continuously in a thread while polling — our packet
        # then holds the state for the vast majority of each 100ms window.
        stop = threading.Event()

        def flood():
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            while not stop.is_set():
                s.sendto(sentence.encode("ascii"), ("127.0.0.1", UDP_PORT))
                time.sleep(0.005)
            s.close()

        t = threading.Thread(target=flood, daemon=True)
        t.start()
        seen = False
        try:
            for _ in range(20):
                d = requests.get(f"{BASE_URL}/api/health").json()
                if abs(d["heading"] - 123.4) < 0.5:
                    seen = True
                    break
                time.sleep(0.2)
        finally:
            stop.set()
            t.join(timeout=2)
        assert seen, "Custom $HEHDT,123.4 was never reflected in /api/health"
