import { createFileRoute } from "@tanstack/react-router";
import { LifeBuoy, BookOpen, MessageSquare, Server, CheckCircle2 } from "lucide-react";
import { SectionLabel } from "@/components/pravah/atoms";

export const Route = createFileRoute("/support")({
  component: RouteComponent,
});

function RouteComponent() {
  return (
    <div className="h-full overflow-y-auto p-4 custom-scrollbar">
      <div className="mb-6 flex flex-col items-center justify-center py-8 text-center">
        <div className="grid h-16 w-16 place-items-center rounded-full bg-[var(--brand-glow)] text-[var(--brand-primary)] mb-4">
          <LifeBuoy className="h-8 w-8" />
        </div>
        <h1 className="text-3xl font-bold text-foreground">How can we help?</h1>
        <p className="mt-2 text-sm text-[var(--text-secondary)] max-w-md">Search the knowledge base or open a ticket with the ACRU IT department.</p>
        
        <div className="mt-6 w-full max-w-xl">
          <input 
            type="text" 
            placeholder="Search for answers, SOPs, or API documentation..." 
            className="w-full rounded-full border border-[var(--border-muted)] bg-[var(--surface-1)] px-6 py-3.5 text-[14px] text-foreground shadow-sm focus:border-[var(--brand-primary)] focus:outline-none focus:ring-1 focus:ring-[var(--brand-primary)]"
          />
        </div>
      </div>

      <div className="grid grid-cols-3 gap-6 max-w-5xl mx-auto">
        <div className="col-span-2 flex flex-col gap-6">
          <div className="grid grid-cols-2 gap-4">
            <div className="flex flex-col rounded-xl border border-[var(--border)] bg-[var(--surface-1)] p-5 hover:border-[var(--brand-primary)]/50 transition-colors cursor-pointer">
              <BookOpen className="h-6 w-6 text-[var(--brand-primary)] mb-3" />
              <span className="font-semibold text-foreground text-[15px]">Documentation & SOPs</span>
              <span className="mt-1 text-[13px] text-[var(--text-tertiary)]">Read the Standard Operating Procedures for handling severe incidents.</span>
            </div>
            <div className="flex flex-col rounded-xl border border-[var(--border)] bg-[var(--surface-1)] p-5 hover:border-[var(--brand-primary)]/50 transition-colors cursor-pointer">
              <MessageSquare className="h-6 w-6 text-[var(--psi-moderate)] mb-3" />
              <span className="font-semibold text-foreground text-[15px]">Open an IT Ticket</span>
              <span className="mt-1 text-[13px] text-[var(--text-tertiary)]">Report a bug, request hardware maintenance, or get software access.</span>
            </div>
          </div>

          <div className="rounded-xl border border-[var(--border)] bg-[var(--surface-1)] p-5">
            <SectionLabel>Quick Contact Form</SectionLabel>
            <div className="mt-4 flex flex-col gap-4">
              <div className="grid grid-cols-2 gap-4">
                <div className="flex flex-col gap-1.5">
                  <label className="text-[12px] font-medium text-[var(--text-secondary)]">Name</label>
                  <input type="text" className="rounded-lg border border-[var(--border-muted)] bg-[var(--surface-0)] px-3 py-2 text-[13px] text-foreground focus:outline-none focus:border-[var(--brand-primary)]" defaultValue="Operator 1" />
                </div>
                <div className="flex flex-col gap-1.5">
                  <label className="text-[12px] font-medium text-[var(--text-secondary)]">Department</label>
                  <input type="text" className="rounded-lg border border-[var(--border-muted)] bg-[var(--surface-0)] px-3 py-2 text-[13px] text-foreground focus:outline-none focus:border-[var(--brand-primary)]" defaultValue="Traffic Control Room" />
                </div>
              </div>
              <div className="flex flex-col gap-1.5">
                <label className="text-[12px] font-medium text-[var(--text-secondary)]">Message</label>
                <textarea className="min-h-[100px] resize-none rounded-lg border border-[var(--border-muted)] bg-[var(--surface-0)] p-3 text-[13px] text-foreground focus:outline-none focus:border-[var(--brand-primary)]" placeholder="Describe your issue..." />
              </div>
              <button className="self-end rounded-lg bg-[var(--brand-primary)] px-5 py-2 text-[13px] font-semibold text-white transition-colors hover:bg-[var(--brand-primary)]/90">
                Submit Request
              </button>
            </div>
          </div>
        </div>

        <div className="flex flex-col">
          <div className="rounded-xl border border-[var(--border)] bg-[var(--surface-1)] p-5">
            <div className="flex items-center gap-2 mb-4 border-b border-[var(--border)] pb-4">
              <Server className="h-5 w-5 text-[var(--text-secondary)]" />
              <span className="font-semibold text-foreground">System Status</span>
            </div>
            <div className="flex flex-col gap-4">
              {[
                { name: "ACRU Core API", status: "Operational" },
                { name: "Mapbox Routing Engine", status: "Operational" },
                { name: "NLP Triage Service", status: "Operational" },
                { name: "Camera Feed Ingestion", status: "Operational" },
              ].map((sys, i) => (
                <div key={i} className="flex items-center justify-between">
                  <span className="text-[13px] text-[var(--text-secondary)]">{sys.name}</span>
                  <div className="flex items-center gap-1.5 text-[12px] font-medium text-[var(--brand-primary)]">
                    <CheckCircle2 className="h-4 w-4" /> {sys.status}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
