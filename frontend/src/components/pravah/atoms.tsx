import type { Severity } from "@/lib/pravah-mock";

export const sevColor: Record<Severity, string> = {
  low: "#22c55e",
  moderate: "#f5a623",
  high: "#e03c3c",
  severe: "#e03c3c",
};

export const sevLabel: Record<Severity, string> = {
  low: "LOW",
  moderate: "MODERATE",
  high: "HIGH",
  severe: "SEVERE",
};

export function SectionLabel({ children, right }: { children: React.ReactNode; right?: React.ReactNode }) {
  return (
    <div className="flex items-center justify-between">
      <h3 className="text-[11px] font-semibold uppercase tracking-[0.12em] text-[#7a8599]">{children}</h3>
      {right}
    </div>
  );
}

export function PSIBadge({ score }: { score: number }) {
  let bg = "#22c55e";
  if (score >= 81) bg = "#8b0000";
  else if (score >= 61) bg = "#e03c3c";
  else if (score >= 31) bg = "#f5a623";
  return (
    <span
      className="inline-flex h-7 min-w-[2.5rem] items-center justify-center rounded-md px-2 font-mono text-[13px] font-bold text-white tabular-nums"
      style={{ background: bg }}
    >
      {score}
    </span>
  );
}

export function SevPill({ sev }: { sev: Severity }) {
  const map: Record<Severity, { bg: string; fg: string }> = {
    low:      { bg: "#22c55e22", fg: "#22c55e" },
    moderate: { bg: "#f5a62322", fg: "#f5a623" },
    high:     { bg: "#e03c3c22", fg: "#e03c3c" },
    severe:   { bg: "#8b000033", fg: "#ff5d5d" },
  };
  const c = map[sev];
  return (
    <span className="inline-flex h-5 items-center rounded px-1.5 text-[10px] font-semibold uppercase tracking-wider" style={{ background: c.bg, color: c.fg }}>
      {sevLabel[sev]}
    </span>
  );
}

export function StatusPill({ status }: { status: string }) {
  const map: Record<string, { bg: string; fg: string; border?: string }> = {
    "In Transit": { bg: "transparent", fg: "#00c2a8", border: "#00c2a8" },
    "Picked Up":  { bg: "#f5a62322", fg: "#f5a623" },
    "Delivered":  { bg: "#22c55e22", fg: "#22c55e" },
    "Assigned":   { bg: "#00c2a822", fg: "#00c2a8" },
    "Pending":    { bg: "#7a859922", fg: "#b6bfd0" },
    "Responded":  { bg: "#3b82f622", fg: "#3b82f6" },
  };
  const c = map[status] ?? { bg: "#1e2433", fg: "#e8edf5" };
  return (
    <span
      className="inline-flex items-center rounded-md px-2.5 py-1 text-[11px] font-medium"
      style={{ background: c.bg, color: c.fg, border: c.border ? `1px solid ${c.border}` : "1px solid transparent" }}
    >
      {status}
    </span>
  );
}
