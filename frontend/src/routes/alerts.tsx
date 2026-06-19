import { createFileRoute } from "@tanstack/react-router";
import { Bell, Video, TrendingUp, AlertOctagon, CheckCircle2 } from "lucide-react";

export const Route = createFileRoute("/alerts")({
  component: RouteComponent,
});

function RouteComponent() {
  const alerts = [
    { id: 1, type: "system", icon: Video, color: "var(--psi-high)", text: "Camera 42 offline at Silk Board junction.", time: "2 mins ago" },
    { id: 2, type: "ai", icon: TrendingUp, color: "var(--psi-severe)", text: "Unusual congestion surge detected (+40% volume) on Mysore Road.", time: "15 mins ago" },
    { id: 3, type: "system", icon: AlertOctagon, color: "var(--psi-moderate)", text: "Sensor node battery low at Kengeri station.", time: "1 hour ago" },
  ];

  return (
    <div className="h-full p-4 max-w-4xl mx-auto">
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-foreground">System Alerts</h1>
          <p className="mt-1 text-sm text-[var(--text-secondary)]">Automated hardware and intelligence notifications.</p>
        </div>
        <div className="flex gap-2 bg-[var(--surface-1)] p-1 rounded-lg border border-[var(--border)]">
          <button className="px-4 py-1.5 text-[12px] font-medium bg-[var(--surface-3)] text-foreground rounded-md">Unread</button>
          <button className="px-4 py-1.5 text-[12px] font-medium text-[var(--text-secondary)] hover:text-foreground">All Alerts</button>
        </div>
      </div>

      <div className="flex flex-col gap-4">
        {alerts.map((a) => (
          <div key={a.id} className="flex items-start gap-4 rounded-xl border border-[var(--border-muted)] bg-[var(--surface-1)] p-5 transition-all hover:bg-[var(--surface-2)]/50">
            <div className="grid h-10 w-10 shrink-0 place-items-center rounded-full bg-[var(--surface-0)] border border-[var(--border)]" style={{ color: a.color }}>
              <a.icon className="h-5 w-5" />
            </div>
            <div className="flex-1">
              <div className="flex items-center justify-between">
                <span className="font-semibold text-foreground text-[14px]">{a.text}</span>
                <span className="text-[12px] text-[var(--text-tertiary)]">{a.time}</span>
              </div>
              <div className="mt-4 flex gap-3">
                <button className="inline-flex items-center gap-1.5 rounded-lg bg-[var(--brand-primary)] px-3 py-1.5 text-[12px] font-semibold text-white hover:bg-[var(--brand-primary)]/90">
                  <CheckCircle2 className="h-4 w-4" /> Acknowledge
                </button>
                <button className="inline-flex items-center gap-1.5 rounded-lg border border-[var(--border)] bg-[var(--surface-0)] px-3 py-1.5 text-[12px] font-medium text-foreground hover:bg-[var(--surface-2)]">
                  Create Ticket
                </button>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
