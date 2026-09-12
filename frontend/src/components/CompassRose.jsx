import { useCallback, useRef } from "react";

const R_OUT = 470;
const R_MAJOR = 400;
const R_MID = 415;
const R_MINOR = 432;
const R_LABEL = 352;
const R_CARDINAL = 292;

const CARDINALS = { 0: "N", 90: "E", 180: "S", 270: "W" };
const INTERCARDINALS = { 45: "NE", 135: "SE", 225: "SW", 315: "NW" };

function Ticks() {
  const minor = [];
  const mid = [];
  const major = [];
  for (let a = 0; a < 360; a += 1) {
    if (a % 10 === 0) {
      major.push(
        <line key={a} x1="0" y1={-R_OUT} x2="0" y2={-R_MAJOR}
          stroke="#FFFFFF" strokeWidth={a % 30 === 0 ? 5 : 3}
          transform={`rotate(${a})`} />
      );
    } else if (a % 5 === 0) {
      mid.push(
        <line key={a} x1="0" y1={-R_OUT} x2="0" y2={-R_MID}
          stroke="#94A3B8" strokeWidth="2" transform={`rotate(${a})`} />
      );
    } else {
      minor.push(
        <line key={a} x1="0" y1={-R_OUT} x2="0" y2={-R_MINOR}
          stroke="#475569" strokeWidth="1" transform={`rotate(${a})`} />
      );
    }
  }
  return (
    <g>
      {minor}
      {mid}
      {major}
    </g>
  );
}

function Labels() {
  const items = [];
  for (let a = 0; a < 360; a += 10) {
    if (a % 90 === 0 || a % 45 === 0) continue;
    items.push(
      <g key={a} transform={`rotate(${a})`}>
        <text x="0" y={-R_LABEL} textAnchor="middle" dominantBaseline="middle"
          fill="#CBD5E1" fontSize="26" fontFamily="'JetBrains Mono', monospace"
          fontWeight="500" opacity="0.85">
          {String(a).padStart(3, "0")}
        </text>
      </g>
    );
  }
  Object.entries(CARDINALS).forEach(([deg, letter]) => {
    const a = Number(deg);
    items.push(
      <g key={`c-${a}`} transform={`rotate(${a})`}>
        <text x="0" y={-R_CARDINAL} textAnchor="middle" dominantBaseline="middle"
          fill={a === 0 ? "#FF453A" : "#F8FAFC"} fontSize="72" fontWeight="800"
          fontFamily="'Chivo', sans-serif" letterSpacing="4">
          {letter}
        </text>
      </g>
    );
  });
  Object.entries(INTERCARDINALS).forEach(([deg, letter]) => {
    const a = Number(deg);
    items.push(
      <g key={`i-${a}`} transform={`rotate(${a})`}>
        <text x="0" y={-R_CARDINAL} textAnchor="middle" dominantBaseline="middle"
          fill="#94A3B8" fontSize="40" fontWeight="600"
          fontFamily="'Chivo', sans-serif" letterSpacing="2" opacity="0.8">
          {letter}
        </text>
      </g>
    );
  });
  return <g>{items}</g>;
}

function Needles() {
  // Ship-style indicator needles: slim triangles with apex toward the center,
  // like a physical gyro repeater card. N needle red, others cream.
  const items = [];
  Object.entries(CARDINALS).forEach(([deg]) => {
    const a = Number(deg);
    const north = a === 0;
    items.push(
      <g key={`cn-${a}`} transform={`rotate(${a})`}>
        <polygon
          points="0,-335 22,-465 -22,-465"
          fill={north ? "#FF3B30" : "#F2EDE0"}
          stroke="#05070A"
          strokeWidth="2"
          opacity={north ? 1 : 0.92}
        />
      </g>
    );
  });
  Object.entries(INTERCARDINALS).forEach(([deg]) => {
    const a = Number(deg);
    items.push(
      <g key={`in-${a}`} transform={`rotate(${a})`}>
        <polygon
          points="0,-355 16,-460 -16,-460"
          fill="#C9C3B4"
          stroke="#05070A"
          strokeWidth="2"
          opacity="0.8"
        />
      </g>
    );
  });
  return <g>{items}</g>;
}

function MinuteDial({ headingRaw }) {
  // Inner "minutes" ring like a ship's gyro repeater: one full turn of the
  // ring = 10 degrees of heading (36:1 ratio), numbered 0-9 with 0.1° ticks.
  // Driven by the UNWRAPPED heading so it spins continuously through 359->0.
  const rot = headingRaw === null ? 0 : -headingRaw * 36;
  const ticks = [];
  for (let i = 0; i < 100; i++) {
    const a = i * 3.6;
    const isNum = i % 10 === 0;
    const isHalf = i % 5 === 0;
    ticks.push(
      <line
        key={i}
        x1="0" y1="-268" x2="0" y2={isNum ? "-238" : isHalf ? "-248" : "-256"}
        stroke={isNum ? "#F2EDE0" : "#8A94A6"}
        strokeWidth={isNum ? 3 : isHalf ? 2 : 1}
        transform={`rotate(${a})`}
      />
    );
  }
  const nums = [];
  for (let n = 0; n < 10; n++) {
    nums.push(
      <g key={n} transform={`rotate(${n * 36})`}>
        <text x="0" y="-205" textAnchor="middle" dominantBaseline="middle"
          fill={n === 0 ? "#FF3B30" : "#E8E4D8"} fontSize="40" fontWeight="700"
          fontFamily="'Chivo', sans-serif">
          {n}
        </text>
      </g>
    );
  }
  return (
    <g style={{ transform: `rotate(${rot}deg)` }} data-testid="minute-dial">
      <circle cx="0" cy="0" r="272" fill="#0C0F14" stroke="#2A3444" strokeWidth="2" />
      {ticks}
      {nums}
      <circle cx="0" cy="0" r="180" fill="none" stroke="#2A3444" strokeWidth="2" />
    </g>
  );
}

export const CompassRose = ({ heading, headingRaw, bearing, bearingVisible, onBearingChange }) => {
  const svgRef = useRef(null);
  const draggingRef = useRef(false);

  const angleFromEvent = useCallback((e) => {
    const rect = svgRef.current.getBoundingClientRect();
    const cx = rect.left + rect.width / 2;
    const cy = rect.top + rect.height / 2;
    const dx = e.clientX - cx;
    const dy = e.clientY - cy;
    return (Math.atan2(dx, -dy) * 180) / Math.PI < 0
      ? (Math.atan2(dx, -dy) * 180) / Math.PI + 360
      : (Math.atan2(dx, -dy) * 180) / Math.PI;
  }, []);

  const onPointerDown = useCallback((e) => {
    if (!bearingVisible) return;
    draggingRef.current = true;
    e.target.setPointerCapture?.(e.pointerId);
    onBearingChange(angleFromEvent(e));
  }, [bearingVisible, angleFromEvent, onBearingChange]);

  const onPointerMove = useCallback((e) => {
    if (!draggingRef.current || !bearingVisible) return;
    onBearingChange(angleFromEvent(e));
  }, [bearingVisible, angleFromEvent, onBearingChange]);

  const onPointerUp = useCallback(() => { draggingRef.current = false; }, []);

  const rot = heading === null ? 0 : -heading;

  return (
    <svg
      ref={svgRef}
      data-testid="compass-card-svg"
      viewBox="-500 -500 1000 1000"
      className="w-full h-full select-none"
      style={{ touchAction: "none", cursor: bearingVisible ? "crosshair" : "default" }}
      onPointerDown={onPointerDown}
      onPointerMove={onPointerMove}
      onPointerUp={onPointerUp}
    >
      <defs>
        <radialGradient id="cardFace" cx="50%" cy="50%" r="50%">
          <stop offset="0%" stopColor="#0C0F14" />
          <stop offset="78%" stopColor="#0C0F14" />
          <stop offset="100%" stopColor="#11161F" />
        </radialGradient>
      </defs>

      {/* Bezel */}
      <circle cx="0" cy="0" r="492" fill="none" stroke="#1E2633" strokeWidth="10" />
      <circle cx="0" cy="0" r="482" fill="url(#cardFace)" stroke="#2A3444" strokeWidth="2" />

      {/* Rotating card */}
      <g style={{ transform: `rotate(${rot}deg)`, transition: "none" }} data-testid="compass-rotating-card">
        <Ticks />
        <Needles />
        <Labels />
      </g>

      {/* Inner minutes ring (36:1 subdivider, like a ship's gyro repeater) */}
      <MinuteDial headingRaw={headingRaw} />

      {/* Bearing sight line (screen relative) */}
      {bearingVisible && (
        <g transform={`rotate(${bearing})`} data-testid="bearing-line-overlay">
          <line x1="0" y1="-140" x2="0" y2="-452" stroke="#00E5FF" strokeWidth="3"
            strokeDasharray="14 8" opacity="0.9" />
          <circle cx="0" cy="-452" r="16" fill="none" stroke="#00E5FF" strokeWidth="4" />
          <circle cx="0" cy="-452" r="5" fill="#00E5FF" />
        </g>
      )}

      {/* Fixed lubber line at 12 o'clock: simple red line to the inner ring */}
      <g data-testid="lubber-line">
        <line x1="0" y1="-494" x2="0" y2="-272" stroke="#FF3B30" strokeWidth="6" />
      </g>

      {/* Center hub + brass pivot (like the physical repeater) */}
      <circle cx="0" cy="0" r="112" fill="#05070A" stroke="#1E2633" strokeWidth="3" />
      <circle cx="0" cy="0" r="10" fill="#C8A24A" stroke="#05070A" strokeWidth="2" />
    </svg>
  );
};
