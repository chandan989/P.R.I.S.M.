import { useEffect, useRef, useState } from "react";
import { Settings, X, Check, RotateCcw, Wifi, WifiOff } from "lucide-react";
import { getApiBase, normalizeApiBase, setApiBase } from "@/lib/api";

interface Props {
  className?: string;
}

export default function BackendSettings({ className }: Props) {
  const [open, setOpen] = useState(false);
  const [url, setUrl] = useState(() => getApiBase());
  const [status, setStatus] = useState<"idle" | "checking" | "ok" | "fail">("idle");
  const ref = useRef<HTMLDivElement | null>(null);

  // Close when clicking outside
  useEffect(() => {
    if (!open) return;
    const handler = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false);
    };
    document.addEventListener("mousedown", handler);
    return () => document.removeEventListener("mousedown", handler);
  }, [open]);

  // Re-sync URL from storage when opening
  useEffect(() => {
    if (open) setUrl(getApiBase());
  }, [open]);

  const save = () => {
    setApiBase(url.trim() || null);
    checkConnection(getApiBase());
  };

  const reset = () => {
    setApiBase(null);
    setUrl(getApiBase());
    setStatus("idle");
  };

  const checkConnection = async (target?: string) => {
    const base = normalizeApiBase(target || getApiBase());
    setStatus("checking");
    try {
      const ctrl = new AbortController();
      const t = setTimeout(() => ctrl.abort(), 15000);
      const res = await fetch(`${base}/health`, { signal: ctrl.signal });
      clearTimeout(t);
      setStatus(res.ok ? "ok" : "fail");
    } catch {
      setStatus("fail");
    }
  };

  const statusColor =
    status === "ok" ? "var(--signal-green, #4ADE80)" :
    status === "fail" ? "var(--signal-red, #F87171)" :
    status === "checking" ? "var(--aura-cyan, #67E8F9)" :
    "var(--ink-tertiary, #888)";

  return (
    <div className={`backend-settings-wrap ${className ?? ""}`} ref={ref}>
      <button
        className="nav-icon-btn"
        aria-label="Backend settings"
        aria-expanded={open}
        onClick={() => setOpen((v) => !v)}
        title="Backend URL settings"
      >
        <Settings size={18} />
      </button>

      {open && (
        <div className="backend-popover" role="dialog" aria-label="Backend connection settings">
          <div className="backend-popover-header">
            <span>Backend Connection</span>
            <button className="backend-popover-close" onClick={() => setOpen(false)} aria-label="Close">
              <X size={14} />
            </button>
          </div>

          <label className="backend-popover-label" htmlFor="backend-url-input">
            API URL
          </label>
          <div className="backend-popover-row">
            <input
              id="backend-url-input"
              className="backend-popover-input"
              type="url"
              placeholder="https://your-ngrok-or-colab-url.ngrok-free.app"
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              onKeyDown={(e) => { if (e.key === "Enter") save(); }}
            />
          </div>

          <div className="backend-popover-actions">
            <button className="backend-popover-btn backend-popover-btn--primary" onClick={save}>
              <Check size={14} /> Save
            </button>
            <button className="backend-popover-btn" onClick={reset}>
              <RotateCcw size={14} /> Reset
            </button>
            <button className="backend-popover-btn" onClick={() => checkConnection()}>
              {status === "checking" ? (
                <span className="backend-spinner" />
              ) : status === "ok" ? (
                <Wifi size={14} />
              ) : status === "fail" ? (
                <WifiOff size={14} />
              ) : (
                <Wifi size={14} />
              )}
              Test
            </button>
          </div>

          <div className="backend-popover-status" style={{ color: statusColor }}>
            {status === "ok" && "✓ Connected to backend"}
            {status === "fail" && "✗ Cannot reach backend — mock mode active"}
            {status === "checking" && "Checking…"}
            {status === "idle" && "Paste your notebook URL and click Save"}
          </div>

          <div className="backend-popover-hint">
            Current: <code>{getApiBase()}</code>
          </div>
        </div>
      )}
    </div>
  );
}
