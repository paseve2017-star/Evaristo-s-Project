const W = 600;
const H = 70;

export const HeadingChart = ({ history }) => {
  let body;
  const has = history && history.length >= 2;
  let maxDev = 5;

  if (has) {
    // Unwrap angles relative to the newest sample so 359->0 draws continuously
    const pts = [];
    let ref = history[history.length - 1].h;
    for (let i = history.length - 1; i >= 0; i--) {
      let h = history[i].h;
      while (h - ref > 180) h -= 360;
      while (h - ref < -180) h += 360;
      ref = h;
      pts.push({ t: history[i].t, h });
    }
    pts.reverse();
    const latest = pts[pts.length - 1].h;
    const tMin = pts[pts.length - 1].t - 60000;
    maxDev = Math.max(5, ...pts.map((p) => Math.abs(p.h - latest)));
    const y = (h) => H / 2 - ((h - latest) / maxDev) * (H / 2 - 8);
    const points = pts
      .map((p) => `${Math.max(0, ((p.t - tMin) / 60000) * W).toFixed(1)},${y(p.h).toFixed(1)}`)
      .join(" ");
    body = (
      <svg viewBox={`0 0 ${W} ${H}`} preserveAspectRatio="none" className="w-full h-full">
        <line x1="0" y1={H / 2} x2={W} y2={H / 2} stroke="#1E2633" strokeWidth="1" strokeDasharray="6 4" />
        <polyline points={points} fill="none" stroke="#00E5FF" strokeWidth="1.5" opacity="0.9" />
        <circle cx={W} cy={y(latest)} r="3" fill="#00E5FF" />
      </svg>
    );
  }

  return (
    <div className="relative" data-testid="heading-history-chart">
      <div className="flex justify-between font-mono text-[9px] tracking-[0.2em] text-slate-600 uppercase mb-1">
        <span>Heading · last 60 s</span>
        <span>{has ? `±${maxDev.toFixed(0)}° auto` : "no data"}</span>
      </div>
      <div className="h-[70px] rounded-sm bg-[#0C0F14] border border-[#1E2633] overflow-hidden">
        {body}
      </div>
    </div>
  );
};
