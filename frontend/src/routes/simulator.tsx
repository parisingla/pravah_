import { createFileRoute } from "@tanstack/react-router";
import { useState } from "react";
import { SectionLabel } from "@/components/pravah/atoms";
import { Play, Settings2, TrafficCone, AlertOctagon, TrendingUp, RefreshCw, BarChart2, ShieldAlert } from "lucide-react";
import Map, { Source, Layer, type LineLayer } from "react-map-gl";
import "mapbox-gl/dist/mapbox-gl.css";

const MAPBOX_TOKEN = import.meta.env.VITE_MAPBOX_TOKEN || "pk.eyJ1IjoiZHVtbXkiLCJhIjoiY2R1bW15In0.dummy";

export const Route = createFileRoute("/simulator")({
  component: RouteComponent,
});

function RouteComponent() {
  const [isSimulating, setIsSimulating] = useState(false);
  const [hasResults, setHasResults] = useState(false);
  const [trigger, setTrigger] = useState("closure");

  const handleSimulate = () => {
    setIsSimulating(true);
    setHasResults(false);
    setTimeout(() => {
      setIsSimulating(false);
      setHasResults(true);
    }, 2000);
  };

  // Mock geojson for the simulated affected routes
  const simulatedRoutes = {
    type: "FeatureCollection",
    features: [
      {
        type: "Feature",
        properties: { impact: "high" },
        geometry: { type: "LineString", coordinates: [[77.62, 12.92], [77.63, 12.94], [77.64, 12.95]] }
      },
      {
        type: "Feature",
        properties: { impact: "severe" },
        geometry: { type: "LineString", coordinates: [[77.64, 12.95], [77.65, 12.96], [77.67, 12.96]] }
      }
    ]
  };

  const routeLayer: LineLayer = {
    id: "simulated-routes",
    type: "line",
    source: "simulated-routes-data",
    paint: {
      "line-color": [
        "match", ["get", "impact"],
        "severe", "#e03c3c",
        "high", "#f5a623",
        "#00c2a8"
      ],
      "line-width": 4,
      "line-opacity": 0.8
    }
  };

  return (
    <div className="h-full overflow-y-auto p-4 custom-scrollbar">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-foreground">What-If Simulator</h1>
        <p className="mt-1 text-sm text-[var(--text-secondary)]">
          Model the network impact of road closures, signal timing changes, and major events before making a decision.
        </p>
      </div>

      <div className="grid grid-cols-[320px_1fr] gap-6">
        {/* Left Sidebar: Scenario Builder */}
        <div className="flex flex-col gap-4">
          <div className="rounded-xl border border-[var(--border)] bg-[var(--surface-1)] p-4">
            <div className="flex items-center gap-2 mb-4">
              <Settings2 className="h-4 w-4 text-[var(--brand-primary)]" />
              <SectionLabel>Scenario Builder</SectionLabel>
            </div>

            <div className="flex flex-col gap-4">
              <div className="flex flex-col gap-1.5">
                <label className="text-[11px] font-semibold uppercase tracking-wider text-[var(--text-tertiary)]">Trigger Event</label>
                <select 
                  value={trigger}
                  onChange={(e) => setTrigger(e.target.value)}
                  className="w-full rounded-md border border-[var(--border-muted)] bg-[var(--surface-0)] px-3 py-2 text-[13px] text-foreground focus:border-[var(--brand-primary)] focus:outline-none"
                >
                  <option value="closure">Full Road Closure</option>
                  <option value="vip">VIP Movement (Rolling Block)</option>
                  <option value="weather">Extreme Weather (Flooding)</option>
                  <option value="signal">Signal Optimization Test</option>
                </select>
              </div>

              <div className="flex flex-col gap-1.5">
                <label className="text-[11px] font-semibold uppercase tracking-wider text-[var(--text-tertiary)]">Location / Corridor</label>
                <select className="w-full rounded-md border border-[var(--border-muted)] bg-[var(--surface-0)] px-3 py-2 text-[13px] text-foreground focus:border-[var(--brand-primary)] focus:outline-none">
                  <option>Outer Ring Road (Silk Board to Bellandur)</option>
                  <option>Mysore Road (Kengeri to Nayandahalli)</option>
                  <option>Hosur Road (Electronic City to Silk Board)</option>
                </select>
              </div>

              <div className="flex flex-col gap-1.5">
                <label className="text-[11px] font-semibold uppercase tracking-wider text-[var(--text-tertiary)]">Duration</label>
                <div className="flex gap-2">
                  <input type="number" defaultValue={2} className="w-16 rounded-md border border-[var(--border-muted)] bg-[var(--surface-0)] px-3 py-2 text-[13px] text-foreground text-center focus:border-[var(--brand-primary)] focus:outline-none" />
                  <select className="flex-1 rounded-md border border-[var(--border-muted)] bg-[var(--surface-0)] px-3 py-2 text-[13px] text-foreground focus:border-[var(--brand-primary)] focus:outline-none">
                    <option>Hours</option>
                    <option>Days</option>
                  </select>
                </div>
              </div>

              <button
                onClick={handleSimulate}
                disabled={isSimulating}
                className="mt-2 flex w-full items-center justify-center gap-2 rounded-lg bg-[var(--brand-primary)] py-2.5 text-[13px] font-semibold text-white transition-colors hover:bg-[var(--brand-primary)]/90 disabled:opacity-50"
              >
                {isSimulating ? (
                  <RefreshCw className="h-4 w-4 animate-spin" />
                ) : (
                  <Play className="h-4 w-4" />
                )}
                {isSimulating ? "Running Simulation..." : "Run Simulation"}
              </button>
            </div>
          </div>
        </div>

        {/* Main View: Results */}
        <div className="flex flex-col gap-6">
          {hasResults ? (
            <>
              {/* Map View */}
              <div className="relative h-[300px] w-full overflow-hidden rounded-xl border border-[var(--border)] bg-[var(--surface-1)] animate-in fade-in zoom-in-95 duration-500">
                <Map
                  mapboxAccessToken={MAPBOX_TOKEN}
                  initialViewState={{ longitude: 77.64, latitude: 12.94, zoom: 12.5 }}
                  mapStyle="mapbox://styles/mapbox/dark-v11"
                >
                  <Source id="simulated-routes-data" type="geojson" data={simulatedRoutes as any}>
                    <Layer {...routeLayer} />
                  </Source>
                </Map>
                <div className="absolute top-4 left-4 rounded-lg border border-[var(--border)] bg-[var(--surface-1)] p-3 shadow-lg flex flex-col gap-2">
                  <SectionLabel>Spillover Impact</SectionLabel>
                  <div className="flex items-center gap-2 text-[11px] text-[var(--text-secondary)]">
                    <div className="h-0.5 w-4 bg-[var(--psi-severe)]" /> Severe Gridlock
                  </div>
                  <div className="flex items-center gap-2 text-[11px] text-[var(--text-secondary)]">
                    <div className="h-0.5 w-4 bg-[var(--psi-high)]" /> Heavy Congestion
                  </div>
                </div>
              </div>

              {/* Metrics Diff */}
              <div className="grid grid-cols-3 gap-4 animate-in fade-in slide-in-from-bottom-4 duration-500 delay-150">
                <div className="flex flex-col rounded-xl border border-[var(--psi-severe)] bg-[rgba(224,60,60,0.05)] p-4">
                  <div className="flex items-center gap-2">
                    <TrafficCone className="h-4 w-4 text-[var(--psi-severe)]" />
                    <span className="text-[12px] font-semibold text-[var(--psi-severe)] uppercase tracking-wider">Network Delay</span>
                  </div>
                  <span className="mt-3 font-mono text-3xl font-bold text-foreground tabular-nums">+42m</span>
                  <span className="mt-1 text-[11px] text-[var(--text-secondary)]">System-wide average increase</span>
                </div>

                <div className="flex flex-col rounded-xl border border-[var(--psi-high)] bg-[rgba(245,166,35,0.05)] p-4">
                  <div className="flex items-center gap-2">
                    <AlertOctagon className="h-4 w-4 text-[var(--psi-high)]" />
                    <span className="text-[12px] font-semibold text-[var(--psi-high)] uppercase tracking-wider">Vehicles Affected</span>
                  </div>
                  <span className="mt-3 font-mono text-3xl font-bold text-foreground tabular-nums">14,200</span>
                  <span className="mt-1 text-[11px] text-[var(--text-secondary)]">Trapped in spillover zones</span>
                </div>

                <div className="flex flex-col rounded-xl border border-[var(--brand-primary)] bg-[rgba(0,194,168,0.05)] p-4">
                  <div className="flex items-center gap-2">
                    <BarChart2 className="h-4 w-4 text-[var(--brand-primary)]" />
                    <span className="text-[12px] font-semibold text-[var(--brand-primary)] uppercase tracking-wider">Carbon Emissions</span>
                  </div>
                  <span className="mt-3 font-mono text-3xl font-bold text-foreground tabular-nums">+12%</span>
                  <span className="mt-1 text-[11px] text-[var(--text-secondary)]">Due to idling vehicles</span>
                </div>
              </div>

              {/* Mitigation Recommendations */}
              <div className="rounded-xl border border-[var(--border)] bg-[var(--surface-1)] p-4 animate-in fade-in slide-in-from-bottom-4 duration-500 delay-300">
                <SectionLabel>AI Mitigation Strategy</SectionLabel>
                <div className="mt-4 grid grid-cols-2 gap-4">
                  <div className="flex items-start gap-3 rounded-lg border border-[var(--border-muted)] bg-[var(--surface-0)] p-3">
                    <ShieldAlert className="h-4 w-4 shrink-0 text-[var(--brand-primary)] mt-0.5" />
                    <div className="flex flex-col">
                      <span className="text-[13px] font-medium text-foreground">Increase Green Time</span>
                      <span className="mt-1 text-[11px] text-[var(--text-secondary)]">Add 15s to Silk Board junction East-West phase to flush spillover traffic.</span>
                    </div>
                  </div>
                  <div className="flex items-start gap-3 rounded-lg border border-[var(--border-muted)] bg-[var(--surface-0)] p-3">
                    <TrendingUp className="h-4 w-4 shrink-0 text-[var(--brand-primary)] mt-0.5" />
                    <div className="flex flex-col">
                      <span className="text-[13px] font-medium text-foreground">Activate Detour VMS</span>
                      <span className="mt-1 text-[11px] text-[var(--text-secondary)]">Route incoming traffic through Sarjapur Road before the choke point.</span>
                    </div>
                  </div>
                </div>
              </div>
            </>
          ) : (
            <div className="flex h-full min-h-[400px] flex-col items-center justify-center rounded-xl border border-dashed border-[var(--border)] bg-[var(--surface-0)] text-center">
              <Settings2 className="h-10 w-10 text-[var(--text-tertiary)] opacity-50" />
              <span className="mt-4 text-[14px] font-medium text-[var(--text-secondary)]">Configure a scenario to begin</span>
              <span className="mt-1 text-[12px] text-[var(--text-tertiary)] max-w-xs">Select a trigger, location, and duration to see the predicted network impact.</span>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
