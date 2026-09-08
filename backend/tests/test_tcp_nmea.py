"""Tests for direct NMEA-over-TCP input (iteration 9)."""
import asyncio
import json
import os
import socket
import time

import pytest
import requests
import websockets

def _load_frontend_env():
    p = "/app/frontend/.env"
    if os.path.exists(p):
        for line in open(p):
            if line.startswith("REACT_APP_BACKEND_URL="):
                return line.split("=", 1)[1].strip()
    return None

BASE_URL = (os.environ.get("REACT_APP_BACKEND_URL") or _load_frontend_env()).rstrip("/")
TCP_HOST = "127.0.0.1"
TCP_PORT = int(os.environ.get("NMEA_TCP_PORT", "4002"))


def nmea_cs(body: str) -> str:
    cs = 0
    for ch in body:
        cs ^= ord(ch)
    return f"{cs:02X}"


def build_hdt(deg: float) -> bytes:
    body = f"HEHDT,{deg:.1f},T"
    return f"${body}*{nmea_cs(body)}\r\n".encode("ascii")


def tcp_send(payload: bytes, host=TCP_HOST, port=TCP_PORT, hold=0.2):
    s = socket.create_connection((host, port), timeout=3)
    try:
        s.sendall(payload)
        time.sleep(hold)
    finally:
        s.close()


# --- basic connectivity ---
def test_tcp_port_accepts_connection():
    s = socket.create_connection((TCP_HOST, TCP_PORT), timeout=3)
    s.close()


def test_health_ok():
    r = requests.get(f"{BASE_URL}/api/health", timeout=5)
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


# --- valid HDT via TCP is accepted: verify via WebSocket seeing our unique value ---
@pytest.mark.asyncio
async def test_tcp_valid_hdt_updates_heading_via_ws():
    # Unique heading unlikely to be produced by simulator drift near 278.5
    target = 123.4
    payload = build_hdt(target)
    ws_url = BASE_URL.replace("http", "ws") + "/api/ws/heading"

    async with websockets.connect(ws_url) as ws:
        # flood TCP for a short window while listening on WS
        stop = asyncio.Event()

        async def flooder():
            while not stop.is_set():
                try:
                    reader, writer = await asyncio.open_connection(TCP_HOST, TCP_PORT)
                    writer.write(payload)
                    await writer.drain()
                    await asyncio.sleep(0.02)
                    writer.close()
                except Exception:
                    pass
                await asyncio.sleep(0.01)

        task = asyncio.create_task(flooder())
        seen = False
        deadline = time.time() + 5
        try:
            while time.time() < deadline:
                raw = await asyncio.wait_for(ws.recv(), timeout=2)
                data = json.loads(raw)
                h = data.get("heading")
                if h is not None and abs(h - target) < 0.05:
                    seen = True
                    break
        finally:
            stop.set()
            task.cancel()
        assert seen, "Expected heading from TCP HDT to appear on WS stream"


# --- bad checksum rejected ---
@pytest.mark.asyncio
async def test_tcp_bad_checksum_rejected_via_ws():
    """Send only bad-checksum sentences for a period; the unique heading value must never appear."""
    target = 47.7
    bad = f"$HEHDT,{target:.1f},T*00\r\n".encode("ascii")  # wrong checksum
    ws_url = BASE_URL.replace("http", "ws") + "/api/ws/heading"

    async with websockets.connect(ws_url) as ws:
        stop = asyncio.Event()

        async def flooder():
            while not stop.is_set():
                try:
                    reader, writer = await asyncio.open_connection(TCP_HOST, TCP_PORT)
                    writer.write(bad)
                    await writer.drain()
                    await asyncio.sleep(0.02)
                    writer.close()
                except Exception:
                    pass
                await asyncio.sleep(0.02)

        task = asyncio.create_task(flooder())
        matched = False
        deadline = time.time() + 3
        try:
            while time.time() < deadline:
                raw = await asyncio.wait_for(ws.recv(), timeout=2)
                data = json.loads(raw)
                h = data.get("heading")
                if h is not None and abs(h - target) < 0.05:
                    matched = True
                    break
        finally:
            stop.set()
            task.cancel()
        assert not matched, "Bad checksum HDT should NOT be applied"


# --- multi-sentence single packet ---
@pytest.mark.asyncio
async def test_tcp_multi_sentence_single_packet():
    target = 201.9
    body = build_hdt(10.0) + build_hdt(55.5) + build_hdt(target)
    ws_url = BASE_URL.replace("http", "ws") + "/api/ws/heading"

    async with websockets.connect(ws_url) as ws:
        stop = asyncio.Event()

        async def flooder():
            while not stop.is_set():
                try:
                    reader, writer = await asyncio.open_connection(TCP_HOST, TCP_PORT)
                    writer.write(body)
                    await writer.drain()
                    await asyncio.sleep(0.02)
                    writer.close()
                except Exception:
                    pass
                await asyncio.sleep(0.01)

        task = asyncio.create_task(flooder())
        seen = False
        deadline = time.time() + 5
        try:
            while time.time() < deadline:
                raw = await asyncio.wait_for(ws.recv(), timeout=2)
                data = json.loads(raw)
                h = data.get("heading")
                if h is not None and abs(h - target) < 0.05:
                    seen = True
                    break
        finally:
            stop.set()
            task.cancel()
        assert seen, "Last of multiple sentences in one TCP packet must be parsed"


# --- one sentence split across two packets (buffering) ---
@pytest.mark.asyncio
async def test_tcp_sentence_split_across_packets():
    target = 66.6
    payload = build_hdt(target)
    # split at arbitrary boundary within the sentence
    a, b = payload[:8], payload[8:]
    ws_url = BASE_URL.replace("http", "ws") + "/api/ws/heading"

    async with websockets.connect(ws_url) as ws:
        stop = asyncio.Event()

        async def flooder():
            while not stop.is_set():
                try:
                    reader, writer = await asyncio.open_connection(TCP_HOST, TCP_PORT)
                    writer.write(a)
                    await writer.drain()
                    await asyncio.sleep(0.05)
                    writer.write(b)
                    await writer.drain()
                    await asyncio.sleep(0.02)
                    writer.close()
                except Exception:
                    pass
                await asyncio.sleep(0.02)

        task = asyncio.create_task(flooder())
        seen = False
        deadline = time.time() + 5
        try:
            while time.time() < deadline:
                raw = await asyncio.wait_for(ws.recv(), timeout=2)
                data = json.loads(raw)
                h = data.get("heading")
                if h is not None and abs(h - target) < 0.05:
                    seen = True
                    break
        finally:
            stop.set()
            task.cancel()
        assert seen, "Split-across-packets sentence must parse after buffering"


# --- Regression: WS pushes at ~10 Hz from UDP simulator ---
@pytest.mark.asyncio
async def test_ws_stream_rate_from_udp_simulator():
    ws_url = BASE_URL.replace("http", "ws") + "/api/ws/heading"
    async with websockets.connect(ws_url) as ws:
        # drain one message to sync
        await asyncio.wait_for(ws.recv(), timeout=2)
        start = time.time()
        n = 0
        while time.time() - start < 1.0:
            await asyncio.wait_for(ws.recv(), timeout=2)
            n += 1
        assert n >= 6, f"Expected ~10 msgs/s from UDP simulator, got {n}"
