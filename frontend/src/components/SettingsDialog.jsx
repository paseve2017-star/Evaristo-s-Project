import { useEffect, useState } from "react";
import axios from "axios";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

export const SettingsDialog = ({ open, onOpenChange, wsUrl, onApplyWsUrl }) => {
  const [url, setUrl] = useState(wsUrl);
  const [health, setHealth] = useState(null);

  useEffect(() => {
    if (!open) return;
    setUrl(wsUrl);
    axios.get(`${API}/health`).then((r) => setHealth(r.data)).catch(() => setHealth(null));
  }, [open, wsUrl]);

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent data-testid="settings-dialog" className="bg-[#0C0F14] border-[#1E2633] text-slate-100 sm:max-w-md">
        <DialogHeader>
          <DialogTitle className="font-mono tracking-widest text-sm uppercase text-slate-300">
            Repeater Settings
          </DialogTitle>
          <DialogDescription className="text-slate-500 text-xs font-mono">
            NTPRO 5000 · $HEHDT over UDP
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-5 py-2">
          <div className="space-y-2">
            <Label htmlFor="ws-url" className="text-xs font-mono uppercase tracking-wider text-slate-400">
              WebSocket URL override
            </Label>
            <Input
              id="ws-url"
              data-testid="ws-url-input"
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              className="bg-[#05070A] border-[#1E2633] font-mono text-sm text-slate-200"
              placeholder="wss://host/api/ws/heading"
            />
            <p className="text-[11px] text-slate-500 font-mono">
              Saved locally; reconnects immediately.
            </p>
          </div>

          <div className="grid grid-cols-2 gap-3 font-mono text-xs">
            <div className="rounded-md border border-[#1E2633] bg-[#05070A] p-3">
              <div className="text-slate-500 uppercase tracking-wider text-[10px] mb-1">UDP listen port</div>
              <div className="text-slate-200 text-base" data-testid="udp-port-value">
                {health ? health.udp_port : "—"}
              </div>
            </div>
            <div className="rounded-md border border-[#1E2633] bg-[#05070A] p-3">
              <div className="text-slate-500 uppercase tracking-wider text-[10px] mb-1">Source mode</div>
              <div className="text-slate-200 text-base" data-testid="simulator-mode-value">
                {health ? (health.simulator ? "SIMULATOR" : "NTPRO LIVE") : "—"}
              </div>
            </div>
            <div className="rounded-md border border-[#1E2633] bg-[#05070A] p-3">
              <div className="text-slate-500 uppercase tracking-wider text-[10px] mb-1">Packets received</div>
              <div className="text-slate-200 text-base">{health ? health.packets : "—"}</div>
            </div>
            <div className="rounded-md border border-[#1E2633] bg-[#05070A] p-3">
              <div className="text-slate-500 uppercase tracking-wider text-[10px] mb-1">Last sender</div>
              <div className="text-slate-200 text-base truncate">{health?.last_sender || "—"}</div>
            </div>
          </div>

          <div className="flex gap-2 justify-end">
            <Button
              variant="outline"
              data-testid="settings-reset-ws-button"
              className="border-[#1E2633] bg-transparent text-slate-300 hover:bg-[#1E2633]"
              onClick={() => { onApplyWsUrl(""); onOpenChange(false); }}
            >
              Reset default
            </Button>
            <Button
              data-testid="settings-apply-button"
              className="bg-cyan-600 hover:bg-cyan-500 text-black font-semibold"
              onClick={() => { onApplyWsUrl(url.trim()); onOpenChange(false); }}
            >
              Apply &amp; Reconnect
            </Button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
};
