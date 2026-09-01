import { useCallback, useEffect, useRef, useState } from "react";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

export function defaultWsUrl() {
  const proto = BACKEND_URL.startsWith("https") ? "wss" : "ws";
  return `${proto}://${BACKEND_URL.replace(/^https?:\/\//, "")}/api/ws/heading`;
}

export function getWsUrl() {
  return localStorage.getItem("gyro_ws_url") || defaultWsUrl();
}

export function useHeadingStream() {
  const [heading, setHeading] = useState(null); // smoothed display value
  const [status, setStatus] = useState("offline"); // live | stale | offline
  const [sentence, setSentence] = useState(null);
  const [simulator, setSimulator] = useState(false);
  const [udpPort, setUdpPort] = useState(null);
  const [wsUrl, setWsUrl] = useState(getWsUrl());
  const [rot, setRot] = useState(null);
  const [cog, setCog] = useState(null);
  const [sog, setSog] = useState(null);
  const historyRef = useRef([]); // last 60 s of {t, h} samples

  const targetRef = useRef(null);
  const displayRef = useRef(null);
  const lastMsgAtRef = useRef(0);
  const wsOpenRef = useRef(false);
  const wsRef = useRef(null);
  const reconnectTimerRef = useRef(null);

  const connect = useCallback(() => {
    if (wsRef.current) {
      try { wsRef.current.close(); } catch (e) { /* noop */ }
    }
    let ws;
    try {
      ws = new WebSocket(getWsUrl());
    } catch (e) {
      setStatus("offline");
      reconnectTimerRef.current = setTimeout(connect, 2000);
      return;
    }
    wsRef.current = ws;
    ws.onopen = () => { wsOpenRef.current = true; };
    ws.onmessage = (ev) => {
      try {
        const data = JSON.parse(ev.data);
        lastMsgAtRef.current = Date.now();
        if (typeof data.heading === "number") {
          targetRef.current = data.heading;
          if (displayRef.current === null) displayRef.current = data.heading;
          historyRef.current.push({ t: Date.now(), h: data.heading });
          const cutoff = Date.now() - 60000;
          while (historyRef.current.length && historyRef.current[0].t < cutoff) {
            historyRef.current.shift();
          }
        }
        if (typeof data.rot === "number") setRot(data.rot);
        if (typeof data.cog === "number") setCog(data.cog);
        if (typeof data.sog === "number") setSog(data.sog);
        if (data.sentence) setSentence(data.sentence);
        setSimulator(!!data.simulator);
        if (data.udp_port) setUdpPort(data.udp_port);
      } catch (e) { /* ignore malformed frame */ }
    };
    ws.onclose = () => {
      wsOpenRef.current = false;
      reconnectTimerRef.current = setTimeout(connect, 2000);
    };
    ws.onerror = () => { try { ws.close(); } catch (e) { /* noop */ } };
  }, []);

  useEffect(() => {
    connect();
    return () => {
      clearTimeout(reconnectTimerRef.current);
      if (wsRef.current) wsRef.current.close();
    };
  }, [connect, wsUrl]);

  // Smooth interpolation of the compass card (unwrapped shortest path)
  useEffect(() => {
    let raf;
    const tick = () => {
      const t = targetRef.current;
      if (t !== null && displayRef.current !== null) {
        const d = displayRef.current;
        const diff = ((t - d + 540) % 360) - 180;
        const next = (d + diff * 0.14 + 360) % 360;
        displayRef.current = next;
        setHeading(next);
      }
      raf = requestAnimationFrame(tick);
    };
    raf = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(raf);
  }, []);

  // Connection health evaluation
  useEffect(() => {
    const iv = setInterval(() => {
      if (!wsOpenRef.current) {
        setStatus("offline");
        return;
      }
      const age = Date.now() - lastMsgAtRef.current;
      if (lastMsgAtRef.current === 0 || age > 2000) setStatus("stale");
      else setStatus("live");
    }, 400);
    return () => clearInterval(iv);
  }, []);

  const applyWsUrl = useCallback((url) => {
    if (url) localStorage.setItem("gyro_ws_url", url);
    else localStorage.removeItem("gyro_ws_url");
    setWsUrl(getWsUrl());
  }, []);

  return { heading, status, sentence, simulator, udpPort, wsUrl, applyWsUrl, rot, cog, sog, historyRef };
}
