import { createFileRoute } from "@tanstack/react-router";
import { FileText, Download, FilePlus, Calendar, MoreVertical } from "lucide-react";
import { SectionLabel } from "@/components/pravah/atoms";

export const Route = createFileRoute("/reports")({
  component: RouteComponent,
});

function RouteComponent() {
  const reports = [
    { title: "Mayor's Monthly Traffic Briefing", date: "Oct 1, 2026", type: "PDF", size: "2.4 MB", tag: "Executive" },
    { title: "Weekly Congestion Summary (ORR)", date: "Sep 28, 2026", type: "CSV", size: "840 KB", tag: "Analytics" },
    { title: "Incident Response Time Audit", date: "Sep 15, 2026", type: "PDF", size: "1.1 MB", tag: "Compliance" },
    { title: "Carbon Emissions Impact Estimate", date: "Sep 1, 2026", type: "XLSX", size: "3.2 MB", tag: "Environment" },
  ];

  return (
    <div className="h-full p-4 max-w-5xl mx-auto">
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-foreground">Reports & Exports</h1>
          <p className="mt-1 text-sm text-[var(--text-secondary)]">Access scheduled briefings and generate custom data exports.</p>
        </div>
        <button className="inline-flex items-center gap-2 rounded-lg bg-[var(--brand-primary)] px-4 py-2 text-[13px] font-medium text-white transition-colors hover:bg-[var(--brand-primary)]/90">
          <FilePlus className="h-4 w-4" /> Generate New Report
        </button>
      </div>

      <div className="rounded-xl border border-[var(--border)] bg-[var(--surface-1)] p-4 flex flex-col">
        <div className="flex items-center justify-between mb-4">
          <SectionLabel>Recent Generated Reports</SectionLabel>
          <div className="flex gap-2">
            <button className="flex items-center gap-2 rounded-md border border-[var(--border-muted)] bg-[var(--surface-0)] px-3 py-1.5 text-[12px] font-medium text-foreground hover:bg-[var(--surface-2)]">
              <Calendar className="h-3.5 w-3.5" /> Date Range
            </button>
          </div>
        </div>

        <div className="grid grid-cols-2 gap-4">
          {reports.map((r, i) => (
            <div key={i} className="flex flex-col rounded-lg border border-[var(--border-muted)] bg-[var(--surface-0)] p-4 transition-colors hover:border-[var(--brand-primary)]/50 group cursor-pointer">
              <div className="flex items-start justify-between">
                <div className="flex items-center gap-3">
                  <div className={`grid h-10 w-10 place-items-center rounded-lg ${r.type === 'PDF' ? 'bg-[#e03c3c15] text-[#e03c3c]' : 'bg-[#00c2a815] text-[#00c2a8]'}`}>
                    <FileText className="h-5 w-5" />
                  </div>
                  <div className="flex flex-col">
                    <span className="font-semibold text-foreground text-[14px]">{r.title}</span>
                    <span className="text-[12px] text-[var(--text-tertiary)]">Generated on {r.date} • {r.size}</span>
                  </div>
                </div>
                <button className="text-[var(--text-tertiary)] hover:text-foreground">
                  <MoreVertical className="h-4 w-4" />
                </button>
              </div>
              <div className="mt-4 flex items-center justify-between border-t border-[var(--border-muted)] pt-3">
                <span className="inline-flex items-center rounded-full bg-[var(--surface-2)] px-2.5 py-0.5 text-[10px] font-medium text-[var(--text-secondary)] uppercase tracking-wider">
                  {r.tag}
                </span>
                <button className="inline-flex items-center gap-1.5 text-[12px] font-medium text-[var(--brand-primary)] hover:underline opacity-0 group-hover:opacity-100 transition-opacity">
                  <Download className="h-3.5 w-3.5" /> Download {r.type}
                </button>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
