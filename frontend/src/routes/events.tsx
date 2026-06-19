import { createFileRoute } from "@tanstack/react-router";
import { useState } from "react";
import { Search, Filter, AlertTriangle, Download, MoreHorizontal, ChevronRight, Truck, MapPin } from "lucide-react";
import { SectionLabel, StatusPill, SevPill } from "@/components/pravah/atoms";
import { activeEvents } from "@/lib/pravah-mock";

export const Route = createFileRoute("/events")({
  component: RouteComponent,
});

function RouteComponent() {
  const [search, setSearch] = useState("");

  return (
    <div className="h-full flex flex-col p-4">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-foreground">Active Events</h1>
          <p className="mt-1 text-sm text-[var(--text-secondary)]">Monitor and manage all ongoing incidents across the network.</p>
        </div>
        <button className="inline-flex items-center gap-2 rounded-lg bg-[var(--surface-2)] px-4 py-2 text-[13px] font-medium text-foreground transition-colors hover:bg-[var(--surface-3)] border border-[var(--border)]">
          <Download className="h-4 w-4" /> Export CSV
        </button>
      </div>

      <div className="flex-1 rounded-xl border border-[var(--border)] bg-[var(--surface-1)] flex flex-col overflow-hidden">
        {/* Toolbar */}
        <div className="flex items-center justify-between border-b border-[var(--border)] p-4">
          <div className="flex items-center gap-3 w-full max-w-md">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-[var(--text-tertiary)]" />
              <input
                type="text"
                placeholder="Search events by ID or location..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="w-full rounded-lg border border-[var(--border-muted)] bg-[var(--surface-0)] pl-9 pr-4 py-2 text-[13px] text-foreground focus:border-[var(--brand-primary)] focus:outline-none"
              />
            </div>
            <button className="flex items-center gap-2 rounded-lg border border-[var(--border-muted)] bg-[var(--surface-0)] px-3 py-2 text-[13px] font-medium text-foreground hover:bg-[var(--surface-2)]">
              <Filter className="h-4 w-4" /> Filters
            </button>
          </div>
        </div>

        {/* Table */}
        <div className="flex-1 overflow-auto custom-scrollbar">
          <table className="w-full text-[13px]">
            <thead className="sticky top-0 bg-[var(--surface-1)] shadow-sm">
              <tr className="text-left text-[11px] font-semibold uppercase tracking-wider text-[var(--text-tertiary)] border-b border-[var(--border-muted)]">
                <th className="px-6 py-3 font-semibold">Event Details</th>
                <th className="px-6 py-3 font-semibold">Location</th>
                <th className="px-6 py-3 font-semibold">Severity</th>
                <th className="px-6 py-3 font-semibold">ETA to Clear</th>
                <th className="px-6 py-3 font-semibold">Responders</th>
                <th className="px-6 py-3 font-semibold text-right">Actions</th>
              </tr>
            </thead>
            <tbody>
              {activeEvents.map((e) => (
                <tr key={e.id} className="border-b border-[var(--border-muted)] hover:bg-[var(--surface-2)]/50 transition-colors group cursor-pointer">
                  <td className="px-6 py-4">
                    <div className="flex flex-col">
                      <span className="font-semibold text-foreground">{e.type}</span>
                      <span className="font-mono text-[11px] text-[var(--text-tertiary)]">{e.id}</span>
                    </div>
                  </td>
                  <td className="px-6 py-4">
                    <div className="flex flex-col">
                      <span className="text-foreground">{e.road}</span>
                      <span className="text-[12px] text-[var(--text-secondary)]">{e.near}</span>
                    </div>
                  </td>
                  <td className="px-6 py-4">
                    <SevPill sev={e.sev} />
                  </td>
                  <td className="px-6 py-4 font-mono font-medium text-foreground">{e.eta}</td>
                  <td className="px-6 py-4">
                    <div className="flex items-center gap-2">
                      <span className="flex h-6 w-6 items-center justify-center rounded-full bg-[var(--surface-3)] text-[10px] font-bold text-foreground ring-2 ring-[var(--surface-1)]">
                        {Math.floor(Math.random() * 3) + 1}
                      </span>
                      <span className="text-[12px] text-[var(--text-secondary)]">Units</span>
                    </div>
                  </td>
                  <td className="px-6 py-4 text-right">
                    <button className="text-[var(--text-tertiary)] hover:text-foreground">
                      <ChevronRight className="h-5 w-5" />
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        
        {/* Footer */}
        <div className="flex items-center justify-between border-t border-[var(--border)] px-6 py-3 text-[12px]">
          <span className="text-[var(--text-tertiary)]">Showing <span className="text-foreground">{activeEvents.length}</span> active events</span>
          <div className="flex gap-2">
            <button className="rounded px-3 py-1 text-[var(--text-secondary)] hover:bg-[var(--surface-2)]">Previous</button>
            <button className="rounded px-3 py-1 text-[var(--text-secondary)] hover:bg-[var(--surface-2)]">Next</button>
          </div>
        </div>
      </div>
    </div>
  );
}
