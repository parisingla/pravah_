import { Shield, AlertTriangle, Users, Siren, Truck, MapPin, ChevronRight, Calendar, Filter, ArrowRight } from "lucide-react";
import { summaryMetrics, fleetRows, fuelBars, orders } from "@/lib/pravah-mock";
import { SectionLabel, StatusPill } from "./atoms";

const accentMap: Record<string, { bar: string; bg: string; icon: React.ComponentType<{ className?: string }>; iconBg: string; iconFg: string }> = {
  teal:   { bar: "#00c2a8", bg: "rgba(0, 194, 168, 0.1)", icon: Shield,        iconBg: "rgba(0, 194, 168, 0.2)", iconFg: "#00c2a8" },
  amber:  { bar: "#f5a623", bg: "rgba(245, 166, 35, 0.1)", icon: AlertTriangle, iconBg: "rgba(245, 166, 35, 0.2)", iconFg: "#f5a623" },
  purple: { bar: "#8b5cf6", bg: "rgba(139, 92, 246, 0.1)", icon: Users,         iconBg: "rgba(139, 92, 246, 0.2)", iconFg: "#8b5cf6" },
  red:    { bar: "#e03c3c", bg: "rgba(224, 60, 60, 0.1)", icon: Siren,         iconBg: "rgba(224, 60, 60, 0.2)", iconFg: "#e03c3c" },
};

export function TodaySummary() {
  return (
    <div className="rounded-xl border border-[var(--border)] bg-[var(--surface-1)] p-3.5 flex flex-col">
      <SectionLabel>Today's Summary</SectionLabel>
      <div className="mt-3 grid grid-cols-2 gap-2.5">
        {summaryMetrics.map((m) => {
          const a = accentMap[m.accent];
          const Icon = a.icon;
          return (
            <div key={m.label} className="flex flex-col rounded-[10px] p-3 transition-colors" style={{ background: a.bg }}>
              <div className="flex items-center gap-2">
                <div className="grid h-6 w-6 shrink-0 place-items-center rounded-full" style={{ background: a.iconBg, color: a.iconFg }}>
                  <Icon className="h-3 w-3" />
                </div>
                <span className="truncate text-[10px] font-semibold" style={{ color: a.iconFg }}>
                  {m.label}
                </span>
              </div>
              <div className="mt-3 font-mono text-[22px] font-bold leading-none text-foreground tabular-nums text-left">
                {m.value}
              </div>
              <div className="mt-1.5 truncate text-[10px] font-medium text-left" style={{ color: m.deltaTone === "bad" ? "var(--psi-severe)" : "var(--text-tertiary)" }}>
                <span style={{ color: m.deltaTone === "bad" ? "var(--psi-severe)" : a.iconFg }}>{m.delta.split(" ")[0]}</span> {m.delta.split(" ").slice(1).join(" ")}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

export function FleetDistribution() {
  return (
    <div className="rounded-xl border border-[var(--border)] bg-[var(--surface-1)] p-3.5 flex flex-col">
      <SectionLabel>Fleet Distribution</SectionLabel>
      <div className="mt-3 space-y-2.5">
        {fleetRows.map((r) => (
          <div key={r.type} className="grid grid-cols-[20px_60px_24px_1fr_36px] items-center gap-2">
            <Truck className="h-3.5 w-3.5 text-[var(--text-tertiary)]" />
            <span className="text-[11px] font-medium text-foreground">{r.type}</span>
            <span className="font-mono text-[11px] text-[var(--text-secondary)] tabular-nums">{r.count}</span>
            <div className="relative h-[10px] w-full overflow-hidden rounded-[1px] bg-[var(--text-tertiary)]/20">
              <div className="absolute inset-y-0 left-0 bg-[var(--text-secondary)] transition-all" style={{ width: `${r.pct}%` }} />
              <div className="absolute inset-0" style={{ backgroundImage: "repeating-linear-gradient(90deg, transparent, transparent 2px, var(--surface-1) 2px, var(--surface-1) 3px)" }} />
            </div>
            <span className="text-right font-mono text-[10px] text-[var(--text-tertiary)] tabular-nums">{r.pct}%</span>
          </div>
        ))}
      </div>
    </div>
  );
}

export function FuelUsage() {
  return (
    <div className="rounded-xl border border-[var(--border)] bg-[var(--surface-1)] p-3.5 flex flex-col">
      <SectionLabel>Fuel Usage & Cost</SectionLabel>
      <div className="mt-2.5 grid grid-cols-3 gap-2">
        <div>
          <div className="font-mono text-[18px] font-bold text-foreground">78%</div>
          <div className="text-[9.5px] uppercase tracking-wider text-[var(--text-tertiary)]">Diesel</div>
        </div>
        <div>
          <div className="text-[9.5px] uppercase tracking-wider text-[var(--text-tertiary)]">Average Fuel Efficiency</div>
          <div className="mt-0.5 font-mono text-[18px] font-bold text-foreground">7.4 L</div>
        </div>
        <div className="text-right">
          <div className="font-mono text-[18px] font-bold text-foreground">$21.4k</div>
          <div className="text-[9.5px] uppercase tracking-wider text-[var(--text-tertiary)]">Total Cost</div>
        </div>
      </div>
      <div className="mt-2.5 grid grid-cols-3 items-end gap-2">
        <div>
          <div className="font-mono text-[14px] font-semibold text-foreground">62%</div>
          <div className="text-[9.5px] uppercase tracking-wider text-[var(--text-tertiary)]">Gasoline</div>
        </div>
        <div />
        <div className="text-right">
          <div className="font-mono text-[11px] font-semibold text-foreground">+6%</div>
          <div className="text-[9px] uppercase tracking-wider text-[var(--text-tertiary)]">Last month</div>
        </div>
      </div>
      
      <div className="mt-3 overflow-hidden">
        <svg viewBox="0 0 300 50" className="h-[45px] w-full" preserveAspectRatio="none">
          {/* Background/Foreground Bars */}
          {fuelBars.map((h, i) => {
            const isHighlighted = i > 10 && i < 28;
            return (
              <rect 
                key={i} 
                x={i * 6.2} 
                y={50 - (h / 100) * 40} 
                width="4" 
                height={(h / 100) * 40} 
                fill={isHighlighted ? "var(--text-secondary)" : "var(--surface-3)"} 
                rx="1" 
              />
            );
          })}
          {/* Overlay Trend Line */}
          <path 
            d="M 0 40 Q 40 40 70 20 T 150 25 T 220 35 T 300 25" 
            fill="none" 
            stroke="var(--psi-moderate)" 
            strokeWidth="1.5" 
          />
        </svg>
      </div>
      <div className="mt-1 flex justify-between font-mono text-[9px] text-[var(--text-tertiary)]">
        <span>Sep</span><span>Oct</span>
      </div>
    </div>
  );
}

const tabs = ["All", "Pending", "Responded", "Assigned", "Completed"];

export function OrdersTable() {
  return (
    <div className="flex flex-col rounded-xl border border-[var(--border)] bg-[var(--surface-1)]">
      <div className="flex items-center gap-4 border-b border-[var(--border)] px-4 py-3">
        <SectionLabel>Orders</SectionLabel>
        <div className="flex items-center gap-1 rounded-lg bg-[var(--surface-0)] p-1">
          {tabs.map((t) => (
            <button
              key={t}
              className={`rounded-md px-3 py-1.5 text-[11.5px] font-medium ${
                t === "Assigned" ? "bg-[var(--surface-3)] text-foreground" : "text-[var(--text-tertiary)] hover:text-foreground"
              }`}
            >
              {t}
            </button>
          ))}
        </div>
        <div className="ml-auto flex items-center gap-2">
          <button className="grid h-8 w-8 place-items-center rounded-md border border-[var(--border)] bg-[var(--surface-0)] text-[var(--text-tertiary)] hover:text-foreground"><Calendar className="h-3.5 w-3.5" /></button>
          <button className="grid h-8 w-8 place-items-center rounded-md border border-[var(--border)] bg-[var(--surface-0)] text-[var(--text-tertiary)] hover:text-foreground"><Filter className="h-3.5 w-3.5" /></button>
        </div>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-[12.5px]">
          <thead>
            <tr className="text-left text-[10.5px] font-semibold uppercase tracking-wider text-[var(--text-tertiary)]">
              <th className="px-4 py-2.5 font-semibold">Order ID</th>
              <th className="px-4 py-2.5 font-semibold">Customer</th>
              <th className="px-4 py-2.5 font-semibold">Route</th>
              <th className="px-4 py-2.5 font-semibold">Weight</th>
              <th className="px-4 py-2.5 font-semibold">ETA</th>
              <th className="px-4 py-2.5 font-semibold">Status</th>
            </tr>
          </thead>
          <tbody>
            {orders.map((o, i) => (
              <tr key={o.id} className="border-t border-[var(--border-muted)] hover:bg-[var(--surface-2)]/80" style={{ background: i % 2 ? "#141822" : undefined }}>
                <td className="px-4 py-3">
                  <div className="flex items-center gap-2 font-mono text-foreground">
                    <span className="grid h-7 w-7 place-items-center rounded-md bg-[var(--surface-3)] text-[var(--text-tertiary)]"><Truck className="h-3.5 w-3.5" /></span>
                    {o.id}
                  </div>
                </td>
                <td className="px-4 py-3">
                  <div className="text-foreground">{o.customer}</div>
                  <div className="text-[11px] text-[var(--text-tertiary)]">{o.tag}</div>
                </td>
                <td className="px-4 py-3 text-[12px] text-[var(--text-secondary)]">
                  <div className="flex items-center gap-1.5"><MapPin className="h-3 w-3 text-[var(--brand-primary)]" /><span className="text-foreground">{o.from.split(",")[0]},</span><span>{o.from.split(",")[1]}</span></div>
                  <div className="mt-1 flex items-center gap-1.5"><MapPin className="h-3 w-3 text-[var(--psi-severe)]" /><span className="text-foreground">{o.to.split(",")[0]},</span><span>{o.to.split(",")[1]}</span></div>
                </td>
                <td className="px-4 py-3 font-mono text-foreground tabular-nums">{o.weight}</td>
                <td className="px-4 py-3 font-mono text-foreground tabular-nums">{o.eta}</td>
                <td className="px-4 py-3"><StatusPill status={o.status} /></td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="flex items-center justify-between border-t border-[var(--border)] px-4 py-3 text-[12px]">
        <span className="text-[var(--text-tertiary)]">Showing <span className="text-foreground">1 to 4</span> of <span className="text-foreground">24</span> orders</span>
        <button className="inline-flex items-center gap-1 text-[var(--brand-primary)] hover:text-[#22e0c5]">
          View All Orders <ArrowRight className="h-3.5 w-3.5" />
        </button>
      </div>
    </div>
  );
}
