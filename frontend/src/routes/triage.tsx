import { createFileRoute } from "@tanstack/react-router";
import { useState } from "react";
import { Brain, FileText, CheckCircle, AlertTriangle, Zap, MapPin, Truck, Shield } from "lucide-react";
import { SectionLabel, StatusPill } from "@/components/pravah/atoms";

export const Route = createFileRoute("/triage")({
  component: RouteComponent,
});

function RouteComponent() {
  const [inputText, setInputText] = useState("");
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [result, setResult] = useState<any>(null);

  const handleAnalyze = () => {
    if (!inputText.trim()) return;
    setIsAnalyzing(true);
    setResult(null);
    
    // Mocking an NLP API delay
    setTimeout(() => {
      setIsAnalyzing(false);
      setResult({
        event: "Massive Pileup / Accident",
        severity: "Severe",
        location: "Outer Ring Road near Bellandur",
        impact: "3 lanes blocked, high cascading delay expected.",
        confidence: "98%",
        actions: [
          "Dispatch heavy duty tow trucks (2 units)",
          "Alert nearest medical responders",
          "Update Variable Message Signs (VMS) on ORR approach",
          "Suggest reroutes via Sarjapur Road"
        ]
      });
    }, 1500);
  };

  return (
    <div className="h-full overflow-y-auto p-4 custom-scrollbar">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-foreground">AI Triage (NLP)</h1>
        <p className="mt-1 text-sm text-[var(--text-secondary)]">
          Paste unstructured emergency calls, tweets, or field reports below. Our NLP engine will automatically extract key entities and recommend mitigation strategies.
        </p>
      </div>

      <div className="grid grid-cols-[1fr_400px] gap-6">
        {/* Left Column: Input */}
        <div className="flex flex-col gap-4">
          <div className="flex flex-col rounded-xl border border-[var(--border)] bg-[var(--surface-1)] p-4">
            <SectionLabel>Raw Incident Report</SectionLabel>
            <textarea
              value={inputText}
              onChange={(e) => setInputText(e.target.value)}
              placeholder="e.g., Massive pileup on Outer Ring Road near Bellandur, 3 lanes blocked, raining heavily..."
              className="mt-3 min-h-[200px] w-full resize-none rounded-lg border border-[var(--border-muted)] bg-[var(--surface-0)] p-4 text-[13px] text-foreground focus:border-[var(--brand-primary)] focus:outline-none focus:ring-1 focus:ring-[var(--brand-primary)]"
            />
            <div className="mt-4 flex items-center justify-between">
              <span className="text-[11px] text-[var(--text-tertiary)]">Powered by ACRU Cognitive Engine v2.4</span>
              <button
                onClick={handleAnalyze}
                disabled={isAnalyzing || !inputText.trim()}
                className="inline-flex items-center gap-2 rounded-lg bg-[var(--brand-primary)] px-5 py-2.5 text-[13px] font-semibold text-white transition-colors hover:bg-[var(--brand-primary)]/90 disabled:opacity-50"
              >
                {isAnalyzing ? (
                  <>
                    <div className="h-4 w-4 animate-spin rounded-full border-2 border-white/30 border-t-white" />
                    Analyzing...
                  </>
                ) : (
                  <>
                    <Brain className="h-4 w-4" />
                    Analyze via AI
                  </>
                )}
              </button>
            </div>
          </div>

          <div className="rounded-xl border border-[var(--border)] bg-[var(--surface-1)] p-4">
            <SectionLabel>Recent Processed Reports</SectionLabel>
            <div className="mt-3 flex flex-col gap-3">
              {[
                { time: "10 mins ago", text: "Tree fell on Indiranagar 100ft road blocking traffic.", type: "Obstruction", status: "Active" },
                { time: "45 mins ago", text: "Waterlogging at Silk Board junction, cars moving slow.", type: "Weather", status: "Active" },
                { time: "2 hrs ago", text: "Protest starting near Town Hall.", type: "Event", status: "Resolved" },
              ].map((item, i) => (
                <div key={i} className="flex items-center justify-between rounded-lg border border-[var(--border-muted)] bg-[var(--surface-0)] p-3">
                  <div className="flex flex-col gap-1">
                    <span className="text-[12px] font-medium text-foreground">{item.text}</span>
                    <span className="text-[10px] text-[var(--text-tertiary)]">{item.time} • Extracted: {item.type}</span>
                  </div>
                  <StatusPill status={item.status as any} />
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Right Column: Results */}
        <div className="flex flex-col gap-4">
          <div className="rounded-xl border border-[var(--border)] bg-[var(--surface-1)] p-4">
            <SectionLabel>Extraction Results</SectionLabel>
            
            {result ? (
              <div className="mt-4 flex flex-col gap-5 animate-in fade-in slide-in-from-bottom-4 duration-500">
                <div className="grid grid-cols-2 gap-3">
                  <div className="flex flex-col rounded-lg bg-[var(--surface-0)] p-3 border border-[var(--border-muted)]">
                    <span className="text-[10px] uppercase tracking-wider text-[var(--text-tertiary)]">Event Type</span>
                    <div className="mt-1 flex items-center gap-1.5 font-medium text-foreground">
                      <AlertTriangle className="h-3.5 w-3.5 text-[var(--psi-severe)]" /> {result.event}
                    </div>
                  </div>
                  <div className="flex flex-col rounded-lg bg-[var(--surface-0)] p-3 border border-[var(--border-muted)]">
                    <span className="text-[10px] uppercase tracking-wider text-[var(--text-tertiary)]">Location</span>
                    <div className="mt-1 flex items-center gap-1.5 font-medium text-foreground">
                      <MapPin className="h-3.5 w-3.5 text-[var(--brand-primary)]" /> {result.location}
                    </div>
                  </div>
                </div>

                <div className="flex flex-col rounded-lg bg-[var(--surface-0)] p-3 border border-[var(--border-muted)]">
                  <span className="text-[10px] uppercase tracking-wider text-[var(--text-tertiary)]">Impact Radius</span>
                  <p className="mt-1 text-[13px] text-foreground">{result.impact}</p>
                </div>

                <div className="flex items-center justify-between rounded-lg bg-[var(--brand-glow)] p-3 border border-[var(--brand-primary)]/20">
                  <div className="flex items-center gap-2 text-[var(--brand-primary)]">
                    <Zap className="h-4 w-4" />
                    <span className="text-[12px] font-semibold">AI Confidence Score</span>
                  </div>
                  <span className="font-mono text-[16px] font-bold text-[var(--brand-primary)]">{result.confidence}</span>
                </div>
              </div>
            ) : (
              <div className="mt-4 flex flex-col items-center justify-center rounded-lg border border-dashed border-[var(--border)] bg-[var(--surface-0)] py-12 text-center">
                <Brain className="h-8 w-8 text-[var(--text-tertiary)]" />
                <span className="mt-3 text-[13px] text-[var(--text-secondary)]">Waiting for input...</span>
              </div>
            )}
          </div>

          <div className="rounded-xl border border-[var(--border)] bg-[var(--surface-1)] p-4 flex-1">
            <SectionLabel>Recommended Actions</SectionLabel>
            {result ? (
              <div className="mt-4 flex flex-col gap-3 animate-in fade-in slide-in-from-bottom-4 duration-500 delay-150">
                {result.actions.map((action: string, i: number) => (
                  <label key={i} className="flex cursor-pointer items-start gap-3 rounded-lg border border-[var(--border-muted)] bg-[var(--surface-0)] p-3 transition-colors hover:bg-[var(--surface-2)]">
                    <div className="mt-0.5 flex h-4 w-4 shrink-0 items-center justify-center rounded border border-[var(--border-muted)] bg-transparent">
                      <input type="checkbox" className="opacity-0 absolute" />
                    </div>
                    <span className="text-[13px] text-foreground">{action}</span>
                  </label>
                ))}
                <button className="mt-2 w-full rounded-lg bg-[var(--surface-2)] py-2.5 text-[12px] font-semibold text-foreground hover:bg-[var(--surface-3)] transition-colors border border-[var(--border)]">
                  Execute Selected Actions
                </button>
              </div>
            ) : (
              <div className="mt-4 flex flex-col items-center justify-center rounded-lg border border-dashed border-[var(--border)] bg-[var(--surface-0)] py-8 text-center">
                <Shield className="h-6 w-6 text-[var(--text-tertiary)]" />
                <span className="mt-2 text-[12px] text-[var(--text-tertiary)]">No actions to recommend</span>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
