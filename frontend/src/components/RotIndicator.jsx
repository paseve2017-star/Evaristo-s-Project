export const RotIndicator = ({ rot }) => {
  const has = typeof rot === "number";
  const clamped = has ? Math.max(-30, Math.min(30, rot)) : 0;
  const half = (Math.abs(clamped) / 30) * 50;
  const side = clamped < -0.05 ? "PORT" : clamped > 0.05 ? "STBD" : "";
  const color = clamped < -0.05 ? "#EF4444" : "#10B981";

  return (
    <div className="flex flex-col items-end gap-1 w-56 sm:w-72" data-testid="rot-indicator">
      <div className="font-mono text-[10px] tracking-[0.25em] text-slate-500 uppercase">
        Rate of turn
      </div>
      <div
        className="relative w-full h-3 rounded-sm bg-[#0C0F14] border border-[#1E2633] overflow-hidden"
        data-testid="rot-indicator-bar"
      >
        <div className="absolute left-1/2 top-0 bottom-0 w-px bg-slate-600" />
        {[-20, -10, 10, 20].map((m) => (
          <div
            key={m}
            className="absolute top-0 bottom-0 w-px bg-[#1E2633]"
            style={{ left: `${50 + (m / 30) * 50}%` }}
          />
        ))}
        {has && Math.abs(clamped) > 0.05 && (
          <div
            className="absolute top-0 bottom-0 transition-[left,width] duration-150"
            style={{
              left: clamped < 0 ? `${50 - half}%` : "50%",
              width: `${half}%`,
              backgroundColor: color,
              opacity: 0.85,
            }}
          />
        )}
      </div>
      <div className="flex w-full justify-between font-mono text-[9px] text-slate-600">
        <span>30 P</span>
        <span>0</span>
        <span>30 S</span>
      </div>
      <div
        className="font-mono text-sm sm:text-base font-semibold"
        data-testid="rot-value"
        style={{ color: has && Math.abs(clamped) > 0.05 ? color : "#94A3B8" }}
      >
        {has ? `${Math.abs(rot).toFixed(1)}°/min ${side}`.trim() : "--.- °/min"}
      </div>
    </div>
  );
};
