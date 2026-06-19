import { createFileRoute } from "@tanstack/react-router";
import { BarChart3, Activity, Clock, ShieldCheck } from "lucide-react";
import { SectionLabel } from "@/components/pravah/atoms";

export const Route = createFileRoute("/analytics")({
  component: RouteComponent,
});

function RouteComponent() {
  return (
    <div className="h-full overflow-y-auto p-4 custom-scrollbar">
      <div className="mb-6 flex items-end justify-between">
        <div>
          <h1 className="text-2xl font-bold text-foreground">Analytics</h1>
          <p className="mt-1 text-sm text-[var(--text-secondary)]">City-wide traffic and incident trends.</p>
        </div>
        <select className="rounded-lg border border-[var(--border)] bg-[var(--surface-1)] px-4 py-2 text-[13px] font-medium text-foreground focus:outline-none focus:border-[var(--brand-primary)]">
          <option>Last 7 Days</option>
          <option>This Month</option>
          <option>Year to Date</option>
        </select>
      </div>

      <div className="grid grid-cols-4 gap-4 mb-6">
        {[
          { label: "Total Incidents", value: "482", icon: Activity, color: "var(--psi-high)" },
          { label: "Avg Resolution Time", value: "42m", icon: Clock, color: "var(--brand-primary)" },
          { label: "Avg Network Delay", value: "18m", icon: BarChart3, color: "var(--psi-moderate)" },
          { label: "SLA Compliance", value: "94.2%", icon: ShieldCheck, color: "var(--text-secondary)" }
        ].map((s, i) => (
          <div key={i} className="rounded-xl border border-[var(--border)] bg-[var(--surface-1)] p-4 flex flex-col">
            <div className="flex items-center gap-2">
              <s.icon className="h-4 w-4" style={{ color: s.color }} />
              <span className="text-[12px] font-semibold text-[var(--text-secondary)] uppercase tracking-wider">{s.label}</span>
            </div>
            <span className="mt-3 font-mono text-3xl font-bold text-foreground tabular-nums">{s.value}</span>
          </div>
        ))}
      </div>

      <div className="grid grid-cols-[1fr_400px] gap-6">
        <div className="rounded-xl border border-[var(--border)] bg-[var(--surface-1)] p-5">
          <div className="flex items-center justify-between mb-6">
            <SectionLabel>Traffic Volume Trend</SectionLabel>
            <div className="flex gap-2 bg-[var(--surface-0)] rounded-lg p-1 border border-[var(--border-muted)]">
              <button className="px-3 py-1 text-[11px] font-medium bg-[var(--surface-2)] rounded-md text-foreground shadow-sm">Today</button>
              <button className="px-3 py-1 text-[11px] font-medium text-[var(--text-secondary)] hover:text-foreground">This Week</button>
            </div>
          </div>
          <div className="relative h-[250px] w-full">
            <svg viewBox="0 0 800 250" className="w-full h-full preserve-3d" preserveAspectRatio="none">
              <defs>
                <linearGradient id="stepGrad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="var(--brand-primary)" stopOpacity="0.15" />
                  <stop offset="100%" stopColor="var(--brand-primary)" stopOpacity="0" />
                </linearGradient>
              </defs>
              
              {/* Horizontal Grid Lines */}
              {[50, 100, 150, 200].map(y => (
                <line key={y} x1="0" y1={y} x2="800" y2={y} stroke="var(--border-muted)" strokeDasharray="4 4" />
              ))}
              
              {/* Y-axis labels */}
              <text x="0" y="55" fill="var(--text-tertiary)" fontSize="11">90</text>
              <text x="0" y="105" fill="var(--text-tertiary)" fontSize="11">60</text>
              <text x="0" y="155" fill="var(--text-tertiary)" fontSize="11">30</text>
              
              {/* Step path */}
              <path 
                d="M 30 180 L 100 180 L 100 60 L 170 60 L 170 140 L 240 140 L 240 40 L 310 40 L 310 160 L 380 160 L 380 90 L 450 90 L 450 130 L 520 130 L 520 50 L 590 50 L 590 150 L 660 150 L 660 80 L 730 80 L 730 170 L 800 170" 
                fill="none" 
                stroke="var(--brand-primary)" 
                strokeWidth="2.5" 
                strokeLinejoin="round"
              />
              <path 
                d="M 30 180 L 100 180 L 100 60 L 170 60 L 170 140 L 240 140 L 240 40 L 310 40 L 310 160 L 380 160 L 380 90 L 450 90 L 450 130 L 520 130 L 520 50 L 590 50 L 590 150 L 660 150 L 660 80 L 730 80 L 730 170 L 800 170 L 800 250 L 30 250 Z" 
                fill="url(#stepGrad)" 
              />
              
              {/* Tooltip Popover */}
              <g transform="translate(520, 50)">
                <circle cx="0" cy="0" r="4" fill="var(--surface-0)" stroke="var(--brand-primary)" strokeWidth="2" />
                <circle cx="0" cy="0" r="14" fill="var(--brand-primary)" opacity="0.15" />
                <rect x="-35" y="-40" width="70" height="26" rx="6" fill="var(--brand-primary)" />
                <path d="M -6 -14 L 6 -14 L 0 -8 Z" fill="var(--brand-primary)" />
                <text x="0" y="-23" fill="white" fontSize="12" fontWeight="600" textAnchor="middle">14k vol</text>
              </g>
            </svg>
            
            {/* X-axis labels */}
            <div className="absolute bottom-0 left-0 right-0 flex justify-between px-10 text-[11px] font-medium text-[var(--text-tertiary)] uppercase tracking-wider">
              <span>6 AM</span>
              <span>9 AM</span>
              <span>12 PM</span>
              <span>3 PM</span>
              <span>6 PM</span>
              <span>9 PM</span>
            </div>
          </div>
        </div>

        <div className="rounded-xl border border-[var(--border)] bg-[var(--surface-1)] p-5">
          <SectionLabel>Incident Distribution</SectionLabel>
          <div className="mt-8 flex justify-between px-4 h-[200px]">
            {[
              { day: "Mon", total: 100, a: 30, b: 20 },
              { day: "Tue", total: 100, a: 45, b: 15 },
              { day: "Wed", total: 100, a: 25, b: 40 },
              { day: "Thu", total: 100, a: 60, b: 20 },
              { day: "Fri", total: 100, a: 80, b: 10 },
              { day: "Sat", total: 100, a: 40, b: 30 },
              { day: "Sun", total: 100, a: 20, b: 15 },
            ].map((d, i) => (
              <div key={i} className="flex flex-col items-center justify-end gap-3 w-8">
                <div className="relative w-2 h-full rounded-full bg-[var(--surface-3)] overflow-hidden">
                  <div className="absolute bottom-0 w-full rounded-full bg-[#8b5cf6]" style={{ height: `${d.a}%` }} />
                  <div className="absolute bottom-0 w-full rounded-full bg-[#c4b5fd]" style={{ height: `${d.b}%`, bottom: `${d.a}%` }} />
                </div>
                <span className="text-[11px] font-medium text-[var(--text-secondary)] uppercase">{d.day}</span>
              </div>
            ))}
          </div>
          
          {/* Legend */}
          <div className="mt-6 flex items-center justify-center gap-4 text-[11px] text-[var(--text-secondary)] font-medium">
            <div className="flex items-center gap-1.5"><div className="w-2.5 h-2.5 rounded-sm bg-[#8b5cf6]" /> Accidents</div>
            <div className="flex items-center gap-1.5"><div className="w-2.5 h-2.5 rounded-sm bg-[#c4b5fd]" /> Hazards</div>
          </div>
        </div>
      </div>
    </div>
  );
}
