import { createFileRoute } from "@tanstack/react-router";
import { SectionLabel } from "@/components/pravah/atoms";
import { CloudRain, TrendingUp, AlertTriangle, ArrowUpRight, ArrowDownRight, Clock } from "lucide-react";

export const Route = createFileRoute("/predictions")({
  component: RouteComponent,
});

function RouteComponent() {
  return (
    <div className="h-full overflow-y-auto p-4 custom-scrollbar">
      <div className="mb-6 flex items-end justify-between">
        <div>
          <h1 className="text-2xl font-bold text-foreground">Traffic Predictions</h1>
          <p className="mt-1 text-sm text-[var(--text-secondary)]">
            AI-driven forecasts based on historical data, live events, and weather impact.
          </p>
        </div>
        
        {/* Timeline Selector */}
        <div className="flex items-center gap-1 rounded-lg border border-[var(--border)] bg-[var(--surface-1)] p-1">
          {["Now", "+2h", "+4h", "+12h", "Tomorrow"].map((time, i) => (
            <button
              key={time}
              className={`rounded-md px-4 py-1.5 text-[12px] font-medium transition-colors ${
                i === 1 ? "bg-[var(--brand-primary)] text-white" : "text-[var(--text-secondary)] hover:text-foreground hover:bg-[var(--surface-2)]"
              }`}
            >
              {time}
            </button>
          ))}
        </div>
      </div>

      {/* Top Metrics */}
      <div className="grid grid-cols-3 gap-4 mb-6">
        <div className="flex flex-col rounded-xl border border-[var(--border)] bg-[var(--surface-1)] p-4">
          <div className="flex items-center gap-2">
            <div className="grid h-8 w-8 place-items-center rounded-full bg-[rgba(245,166,35,0.1)] text-[#f5a623]">
              <TrendingUp className="h-4 w-4" />
            </div>
            <span className="text-[12px] font-semibold text-[var(--text-secondary)] uppercase tracking-wider">Network Load</span>
          </div>
          <div className="mt-4 flex items-end justify-between">
            <span className="font-mono text-3xl font-bold text-foreground tabular-nums">142%</span>
            <div className="flex items-center gap-1 text-[12px] font-medium text-[var(--psi-severe)]">
              <ArrowUpRight className="h-3 w-3" /> 42% over normal
            </div>
          </div>
        </div>

        <div className="flex flex-col rounded-xl border border-[var(--border)] bg-[var(--surface-1)] p-4">
          <div className="flex items-center gap-2">
            <div className="grid h-8 w-8 place-items-center rounded-full bg-[rgba(224,60,60,0.1)] text-[var(--psi-severe)]">
              <Clock className="h-4 w-4" />
            </div>
            <span className="text-[12px] font-semibold text-[var(--text-secondary)] uppercase tracking-wider">Expected Delay</span>
          </div>
          <div className="mt-4 flex items-end justify-between">
            <span className="font-mono text-3xl font-bold text-foreground tabular-nums">+45m</span>
            <div className="flex items-center gap-1 text-[12px] font-medium text-[var(--psi-severe)]">
              <ArrowUpRight className="h-3 w-3" /> city-wide avg
            </div>
          </div>
        </div>

        <div className="flex flex-col rounded-xl border border-[var(--border)] bg-[var(--surface-1)] p-4">
          <div className="flex items-center gap-2">
            <div className="grid h-8 w-8 place-items-center rounded-full bg-[rgba(0,194,168,0.1)] text-[var(--brand-primary)]">
              <CloudRain className="h-4 w-4" />
            </div>
            <span className="text-[12px] font-semibold text-[var(--text-secondary)] uppercase tracking-wider">Weather Impact</span>
          </div>
          <div className="mt-4 flex items-end justify-between">
            <span className="font-mono text-3xl font-bold text-foreground tabular-nums">High</span>
            <div className="flex items-center gap-1 text-[12px] font-medium text-[var(--text-tertiary)]">
              Rain expected at 5PM
            </div>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-[350px_1fr] gap-6">
        <div className="rounded-xl border border-[var(--border)] bg-[var(--surface-1)] p-4">
          <SectionLabel>High-Risk Corridors</SectionLabel>
          <div className="mt-4 flex flex-col gap-3">
            {[
              { route: "Mysore Road", from: "Kengeri", prob: 88 },
              { route: "Outer Ring Road", from: "Silk Board", prob: 76 },
              { route: "Hosur Road", from: "Electronic City", prob: 64 },
              { route: "Tumkur Road", from: "Yeshwanthpur", prob: 45 },
            ].map((r, i) => (
              <div key={i} className="flex flex-col gap-2 rounded-lg border border-[var(--border-muted)] bg-[var(--surface-0)] p-3">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <AlertTriangle className={`h-3.5 w-3.5 ${r.prob > 80 ? "text-[var(--psi-severe)]" : r.prob > 60 ? "text-[var(--psi-high)]" : "text-[var(--psi-moderate)]"}`} />
                    <span className="text-[13px] font-medium text-foreground">{r.route}</span>
                  </div>
                  <span className="font-mono text-[12px] font-bold text-foreground">{r.prob}%</span>
                </div>
                <div className="flex items-center justify-between text-[11px] text-[var(--text-tertiary)]">
                  <span>Near {r.from}</span>
                  <span>Probability</span>
                </div>
                {/* Progress bar */}
                <div className="h-1.5 w-full overflow-hidden rounded-full bg-[var(--surface-3)] mt-1">
                  <div className={`h-full rounded-full ${r.prob > 80 ? "bg-[var(--psi-severe)]" : r.prob > 60 ? "bg-[var(--psi-high)]" : "bg-[var(--psi-moderate)]"}`} style={{ width: `${r.prob}%` }} />
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="rounded-xl border border-[var(--border)] bg-[var(--surface-1)] p-4 flex flex-col">
          <SectionLabel>Predicted Volume Surge</SectionLabel>
          <div className="mt-4 flex-1 rounded-lg border border-[var(--border-muted)] bg-[var(--surface-0)] flex items-center justify-center p-6 relative overflow-hidden">
            <div className="absolute inset-0 opacity-[0.03]" style={{ backgroundImage: "radial-gradient(circle at 2px 2px, white 1px, transparent 0)", backgroundSize: "24px 24px" }} />
            
            {/* Mock Area Chart */}
            <svg viewBox="0 0 500 200" className="w-full h-full preserve-3d" preserveAspectRatio="none">
              <defs>
                <linearGradient id="area-grad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="var(--psi-severe)" stopOpacity="0.3" />
                  <stop offset="100%" stopColor="var(--psi-severe)" stopOpacity="0" />
                </linearGradient>
                <linearGradient id="area-normal" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="var(--brand-primary)" stopOpacity="0.2" />
                  <stop offset="100%" stopColor="var(--brand-primary)" stopOpacity="0" />
                </linearGradient>
              </defs>
              
              {/* Normal Volume */}
              <path d="M 0 150 Q 100 140 200 120 T 400 130 T 500 160 L 500 200 L 0 200 Z" fill="url(#area-normal)" />
              <path d="M 0 150 Q 100 140 200 120 T 400 130 T 500 160" fill="none" stroke="var(--brand-primary)" strokeWidth="2" strokeDasharray="4 4" />
              
              {/* Predicted Volume */}
              <path d="M 0 140 Q 100 120 200 40 T 400 80 T 500 150 L 500 200 L 0 200 Z" fill="url(#area-grad)" />
              <path d="M 0 140 Q 100 120 200 40 T 400 80 T 500 150" fill="none" stroke="var(--psi-severe)" strokeWidth="3" />
              
              {/* Peak Marker */}
              <circle cx="280" cy="45" r="4" fill="var(--psi-severe)" />
              <text x="280" y="30" fill="var(--foreground)" fontSize="12" textAnchor="middle" fontWeight="bold">Peak +45m Delay</text>
            </svg>

            <div className="absolute bottom-4 left-4 flex gap-4 text-[11px] font-medium text-[var(--text-secondary)] bg-[var(--surface-1)] p-2 rounded-lg border border-[var(--border)]">
              <div className="flex items-center gap-1.5"><div className="w-3 h-0.5 bg-[var(--brand-primary)]" /> Historical Normal</div>
              <div className="flex items-center gap-1.5"><div className="w-3 h-0.5 bg-[var(--psi-severe)]" /> AI Prediction</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
