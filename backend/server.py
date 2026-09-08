import asyncio
import logging
import math
import os
import random
import time
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, APIRouter
from starlette.middleware.cors import CORSMiddleware

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

UDP_HOST = os.environ.get("UDP_HOST", "0.0.0.0")
UDP_PORT = int(os.environ.get("UDP_PORT", "4001"))
TCP_PORT = int(os.environ.get("NMEA_TCP_PORT", "4002"))  # direct TCP feed from Nmea.exe TelnetTransport
SIMULATOR_MODE = os.environ.get("SIMULATOR_MODE", "true").lower() == "true"
STALE_AFTER_SEC = 2.0
PUSH_INTERVAL_SEC = 0.1  # 10 Hz

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("gyro-repeater")

state = {
    "heading": None,
    "rot": None,
    "cog": None,
    "sog": None,
    "last_packet_at": None,
    "last_sentence": None,
    "last_sender": None,
    "packets": 0,
}
clients = set()


def nmea_checksum(body: str) -> int:
    cs = 0
    for ch in body:
        cs ^= ord(ch)
    return cs


def verified_body(raw: str):
    """Return the checksum-verified NMEA body (without $ and *cs), else None."""
    raw = raw.strip()
    if not raw.startswith("$"):
        return None
    payload = raw[1:]
    if "*" not in payload:
        return None
    body, _, cs = payload.partition("*")
    cs = cs.strip()[:2]
    try:
        if int(cs, 16) != nmea_checksum(body):
            return None
    except ValueError:
        return None
    return body


def parse_hdt(raw: str):
    """Return heading in degrees [0,360) from a $--HDT sentence, else None."""
    body = verified_body(raw)
    if body is None:
        return None
    parts = body.split(",")
    if len(parts) < 3 or not parts[0].endswith("HDT"):
        return None
    if parts[2].upper() != "T":
        return None
    try:
        return float(parts[1]) % 360.0
    except ValueError:
        return None


def parse_rot(raw: str):
    """Return rate of turn (deg/min, negative = port) from $--ROT, else None."""
    body = verified_body(raw)
    if body is None:
        return None
    parts = body.split(",")
    if len(parts) < 2 or not parts[0].endswith("ROT"):
        return None
    try:
        return float(parts[1])
    except ValueError:
        return None


def parse_vtg(raw: str):
    """Return (cog_deg, sog_knots) from $--VTG, else None."""
    body = verified_body(raw)
    if body is None:
        return None
    parts = body.split(",")
    if len(parts) < 6 or not parts[0].endswith("VTG"):
        return None
    try:
        return float(parts[1]) % 360.0, float(parts[5])
    except ValueError:
        return None


def handle_sentence(line: str) -> bool:
    h = parse_hdt(line)
    if h is not None:
        state["heading"] = h
        return True
    r = parse_rot(line)
    if r is not None:
        state["rot"] = r
        return True
    v = parse_vtg(line)
    if v is not None:
        state["cog"], state["sog"] = v
        return True
    return False


def build_hdt(heading: float) -> str:
    body = f"HEHDT,{heading:.1f},T"
    return f"${body}*{nmea_checksum(body):02X}\r\n"


def build_rot(rot: float) -> str:
    body = f"HEROT,{rot:.1f},A"
    return f"${body}*{nmea_checksum(body):02X}\r\n"


def build_vtg(cog: float, sog: float) -> str:
    body = f"HEVTG,{cog:.1f},T,,M,{sog:.1f},N,,K"
    return f"${body}*{nmea_checksum(body):02X}\r\n"


class HeadingUDPProtocol(asyncio.DatagramProtocol):
    def datagram_received(self, data: bytes, addr):
        process_data(data, f"{addr[0]}:{addr[1]}")


def process_data(data: bytes, sender: str):
    try:
        text = data.decode("ascii", errors="ignore")
    except Exception:
        return
    for line in text.splitlines():
        if not handle_sentence(line):
            continue
        state["last_packet_at"] = time.monotonic()
        state["last_sentence"] = line.strip()
        state["last_sender"] = sender
        state["packets"] += 1


async def handle_tcp_client(reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
    """Direct NMEA-over-TCP feed (Nmea.exe TelnetTransport)."""
    peer = writer.get_extra_info("peername")
    peer_str = f"{peer[0]}:{peer[1]}" if peer else "tcp"
    logger.info("TCP NMEA client connected: %s", peer_str)
    buf = b""
    try:
        while True:
            chunk = await reader.read(4096)
            if not chunk:
                break
            buf += chunk
            if len(buf) > 65536:  # sanity cap: drop garbage clients
                buf = b""
                continue
            while b"\n" in buf:
                line, buf = buf.split(b"\n", 1)
                process_data(line, peer_str)
    except Exception:
        pass
    finally:
        writer.close()
        logger.info("TCP NMEA client disconnected: %s", peer_str)


async def broadcast_loop():
    while True:
        if clients:
            now = time.monotonic()
            last = state["last_packet_at"]
            age = (now - last) if last is not None else None
            msg = {
                "heading": state["heading"],
                "rot": state["rot"],
                "cog": state["cog"],
                "sog": state["sog"],
                "ts": datetime.now(timezone.utc).isoformat(),
                "stale": age is None or age > STALE_AFTER_SEC,
                "age_sec": round(age, 3) if age is not None else None,
                "sentence": state["last_sentence"],
                "simulator": SIMULATOR_MODE,
                "udp_port": UDP_PORT,
            }
            dead = []
            for ws in list(clients):
                try:
                    await ws.send_json(msg)
                except Exception:
                    dead.append(ws)
            for ws in dead:
                clients.discard(ws)
        await asyncio.sleep(PUSH_INTERVAL_SEC)


async def simulator_loop():
    """Emit synthetic $HEHDT over UDP to the local listener at 10 Hz."""
    loop = asyncio.get_running_loop()
    transport, _ = await loop.create_datagram_endpoint(
        asyncio.DatagramProtocol,
        remote_addr=("127.0.0.1", UDP_PORT),
    )
    heading = 278.5
    rate = 0.0
    sog = 12.0
    try:
        while True:
            if random.random() < 0.01:
                rate = random.uniform(-0.05, 0.05)  # deg per 0.1 s -> ±30°/min max
            if random.random() < 0.005:
                sog = random.uniform(4.0, 16.0)
            heading = (heading + rate * 0.1 + random.uniform(-0.03, 0.03)) % 360.0
            rot = rate * 600.0  # deg/min
            cog = (heading + 2.5 + random.uniform(-0.5, 0.5)) % 360.0
            transport.sendto(build_hdt(heading).encode("ascii"))
            transport.sendto(build_rot(rot).encode("ascii"))
            transport.sendto(build_vtg(cog, sog).encode("ascii"))
            await asyncio.sleep(0.1)
    finally:
        transport.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    loop = asyncio.get_running_loop()
    await loop.create_datagram_endpoint(HeadingUDPProtocol, local_addr=(UDP_HOST, UDP_PORT))
    logger.info("UDP listener bound on %s:%s", UDP_HOST, UDP_PORT)
    await asyncio.start_server(handle_tcp_client, UDP_HOST, TCP_PORT)
    logger.info("TCP NMEA listener bound on %s:%s", UDP_HOST, TCP_PORT)
    tasks = [asyncio.create_task(broadcast_loop())]
    if SIMULATOR_MODE:
        tasks.append(asyncio.create_task(simulator_loop()))
        logger.info("Simulator mode ON: emitting synthetic $HEHDT to 127.0.0.1:%s", UDP_PORT)
    yield
    for t in tasks:
        t.cancel()


app = FastAPI(lifespan=lifespan)
api_router = APIRouter(prefix="/api")


@api_router.get("/health")
async def health():
    last = state["last_packet_at"]
    age = (time.monotonic() - last) if last is not None else None
    return {
        "status": "ok",
        "udp_host": UDP_HOST,
        "udp_port": UDP_PORT,
        "simulator": SIMULATOR_MODE,
        "last_packet_age_sec": round(age, 3) if age is not None else None,
        "stale": age is None or age > STALE_AFTER_SEC,
        "heading": state["heading"],
        "packets": state["packets"],
        "last_sender": state["last_sender"],
    }


@app.websocket("/api/ws/heading")
async def heading_ws(websocket: WebSocket):
    await websocket.accept()
    clients.add(websocket)
    logger.info("WebSocket client connected (%d total)", len(clients))
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        pass
    except Exception:
        pass
    finally:
        clients.discard(websocket)
        logger.info("WebSocket client disconnected (%d total)", len(clients))


app.include_router(api_router)

# Serve the built frontend from the same process (single-URL deploy on the LAN).
# Build once with: cd frontend && yarn build — then http://<repeater-pc-ip>:8000 opens the repeater.
_build_dir = ROOT_DIR.parent / "frontend" / "build"
if _build_dir.is_dir():
    from fastapi.staticfiles import StaticFiles
    app.mount("/", StaticFiles(directory=_build_dir, html=True), name="static")
    logger.info("Serving frontend build from %s", _build_dir)
else:
    @app.get("/")
    async def _build_missing():
        return {
            "error": "frontend build not found",
            "expected_at": str(_build_dir),
            "fix": "Copy the frontend/build folder from the project ZIP so it sits NEXT TO the backend folder (…/backend and …/frontend/build), then close and re-run run.bat.",
        }

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)
