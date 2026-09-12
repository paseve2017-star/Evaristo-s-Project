import { useCallback, useEffect, useState } from "react";
import "@/App.css";
import { CompassRose } from "@/components/CompassRose";
import { SettingsDialog } from "@/components/SettingsDialog";
import { useHeadingStream } from "@/hooks/useHeadingStream";
import { Maximize, Minimize, Settings, Crosshair, RotateCcw } from "lucide-react";

const fmt = (v) => (v === null || v === undefined ? "---.-" : v.toFixed(1).padStart(5, "0"));

function StatusLed({ status }) {
  const styles = {
    live: { bg: "#10B981", glow: "0 0 10px 2px rgba(16,185,129,0.7)", label: "LIVE" },
    stale: { bg: "#F59E0B", glow: "0 0 12px 3px rgba(245,158,11,0.8)", label: "STALE" },
    offline: { bg: "#EF4444", glow: "0 0 12px 3px rgba(239,68,68,0.8)", label: "NO DATA" },
  };
  const s = styles[status] || styles.offline;
  return (
    <div className="flex items-center gap-2" data-testid="connection-status-led" data-status={status}>
      <span
        className={status !== "live" ? "animate-pulse" : ""}
        style={{
          width: 12, height: 12, borderRadius: "50%",
          backgroundColor: s.bg, boxShadow: s.glow, display: "inline-block",
        }}
      />
      <span className="font-mono text-xs tracking-[0.2em] text-slate-400">{s.label}</span>
    </div>
  );
}

export default function App() {
  const { heading, headingRaw, status, sentence, simulator, udpPort, wsUrl, applyWsUrl } = useHeadingStream();
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [settingsOpen, setSettingsOpen] = useState(false);
  const [bearingVisible, setBearingVisible] = useState(true);
  const [bearing, setBearing] = useState(0);

  const toggleFullscreen = useCallback(() => {
    if (!document.fullscreenElement) {
      document.documentElement.requestFullscreen?.().catch(() => {});
    } else {
      document.exitFullscreen?.().catch(() => {});
    }
  }, []);

  useEffect(() => {
    const onFsChange = () => setIsFullscreen(!!document.fullscreenElement);
    document.addEventListener("fullscreenchange", onFsChange);
    return () => document.removeEventListener("fullscreenchange", onFsChange);
  }, []);

  useEffect(() => {
    const onKey = (e) => {
      if (e.target.tagName === "INPUT") return;
      const k = e.key.toLowerCase();
      if (k === "f") toggleFullscreen();
      else if (k === "b") setBearingVisible((v) => !v);
      else if (k === "r") setBearing(0);
      else if (k === "s") setSettingsOpen(true);
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [toggleFullscreen]);

  const trueBearing = heading === null ? null : (heading + bearing) % 360;

  // Display modes via URL query params (change display without rebuild):
  //   (default)          plain analog card only
  //   ?panel=1           full diagnostic display
  //   ?digital=1 / =0    force center digital readout on/off
  //   ?bearing=1 / =0    force bearing sight tool on/off
  //   ?hud=1 / =0        force top/bottom status bars on/off
  //   Combinable, e.g.  http://localhost:8000/?digital=1&bearing=1
  const q = new URLSearchParams(window.location.search);
  const showPanel = q.has("panel");
  const pick = (key) => (q.has(key) ? q.get(key) !== "0" : showPanel);
  const showHud = pick("hud");
  const showDigital = pick("digital");
  const showBearing = pick("bearing");

  return (
    <div
      data-testid="gyro-repeater-app"
      className="w-screen h-screen overflow-hidden flex flex-col select-none"
      style={{ backgroundColor: "#05070A" }}
    >
      {/* Top HUD */}
      {showHud && (
      <header className="flex items-center justify-between px-5 py-3 border-b border-[#1E2633]">
        <div className="flex items-center gap-3">
          <span className="font-mono text-[11px] sm:text-xs tracking-[0.3em] text-slate-400 uppercase">
            NTPRO 5000 · Gyro Repeater
          </span>
          {simulator && (
            <span
              data-testid="simulator-badge"
              className="font-mono text-[10px] tracking-widest px-2 py-0.5 rounded border border-amber-500/40 text-amber-400"
            >
              SIM
            </span>
          )}
        </div>
        <div className="flex flex-wrap items-center justify-end gap-2 sm:gap-4">
          <StatusLed status={status} />
          <button
            data-testid="bearing-toggle-button"
            onClick={() => setBearingVisible((v) => !v)}
            className={`p-2 rounded-md border transition-colors ${bearingVisible ? "border-cyan-500/50 text-cyan-300" : "border-[#1E2633] text-slate-500 hover:text-slate-300"}`}
            title="Toggle bearing sight (B)"
          >
            <Crosshair size={16} />
          </button>
          <button
            data-testid="bearing-reset-button"
            onClick={() => setBearing(0)}
            className="p-2 rounded-md border border-[#1E2633] text-slate-500 hover:text-slate-300 transition-colors"
            title="Reset bearing to lubber line (R)"
          >
            <RotateCcw size={16} />
          </button>
          <button
            data-testid="fullscreen-toggle-button"
            onClick={toggleFullscreen}
            className="p-2 rounded-md border border-[#1E2633] text-slate-400 hover:text-slate-200 transition-colors"
            title="Fullscreen (F)"
          >
            {isFullscreen ? <Minimize size={16} /> : <Maximize size={16} />}
          </button>
          <button
            data-testid="settings-toggle-button"
            onClick={() => setSettingsOpen(true)}
            className="p-2 rounded-md border border-[#1E2633] text-slate-400 hover:text-slate-200 transition-colors"
            title="Settings (S)"
          >
            <Settings size={16} />
          </button>
        </div>
      </header>
      )}

      {/* Compass */}
      <main className="relative flex-1 flex items-center justify-center min-h-0">
        <div className="h-full max-h-full max-w-full aspect-square p-2">
          <CompassRose
            heading={heading}
            headingRaw={headingRaw}
            bearing={bearing}
            bearingVisible={showBearing && bearingVisible}
            onBearingChange={setBearing}
          />
        </div>

        {/* Center digital readout */}
        {showDigital && (
        <div className="absolute inset-0 flex flex-col items-center justify-center pointer-events-none">
          <div className="flex items-baseline" data-testid="digital-heading-value">
            {(() => {
              const [intPart, decPart] = heading === null ? ["---", "-"] : heading.toFixed(1).split(".");
              return (
                <>
                  <span
                    className="font-bold tracking-tighter text-white"
                    style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: "clamp(2rem, 6vmin, 4.2rem)" }}
                  >
                    {intPart.padStart(3, "0")}
                  </span>
                  <span
                    data-testid="digital-heading-tenths"
                    className="font-light text-slate-400"
                    style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: "clamp(1.1rem, 3.2vmin, 2.2rem)" }}
                  >
                    {`.${decPart}°`}
                  </span>
                </>
              );
            })()}
          </div>
          <span
            data-testid="digital-heading-true-label"
            className="font-mono text-[10px] sm:text-xs tracking-[0.4em] uppercase text-emerald-400 font-semibold mt-1"
          >
            TRUE
          </span>

          {bearingVisible && (
            <div className="mt-4 flex gap-5 font-mono text-sm sm:text-base">
              <div className="flex flex-col items-center">
                <span className="text-[9px] tracking-[0.25em] text-slate-500 uppercase">TB</span>
                <span data-testid="bearing-value-true" className="text-cyan-300 font-semibold">
                  {trueBearing === null ? "---.-" : `${trueBearing.toFixed(1).padStart(5, "0")}°`}
                </span>
              </div>
              <div className="flex flex-col items-center">
                <span className="text-[9px] tracking-[0.25em] text-slate-500 uppercase">RB</span>
                <span data-testid="bearing-value-relative" className="text-amber-300 font-semibold">
                  {`${bearing.toFixed(1).padStart(5, "0")}°`}
                </span>
              </div>
            </div>
          )}
        </div>
        )}
      </main>

      {/* Bottom status bar */}
      {showHud && (
      <footer className="flex items-center justify-between px-5 py-2.5 border-t border-[#1E2633] font-mono text-[11px] text-slate-500">
        <span data-testid="nmea-log-feed" className="truncate max-w-[45%] text-slate-400">
          {sentence || "waiting for $HEHDT …"}
        </span>
        <span className="hidden sm:block tracking-widest">
          UDP {udpPort ?? 4001} · 10 Hz
        </span>
        <span className="tracking-widest text-slate-600">
          F fullscreen · B bearing · R reset · S settings
        </span>
      </footer>
      )}

      <SettingsDialog
        open={settingsOpen}
        onOpenChange={setSettingsOpen}
        wsUrl={wsUrl}
        onApplyWsUrl={applyWsUrl}
      />
    </div>
  );
}
