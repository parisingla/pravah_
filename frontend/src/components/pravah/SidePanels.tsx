import { AlertTriangle, Droplets, Construction, Users, ChevronRight, ArrowRight } from "lucide-react";
import { activeEvents, hotspots, type Severity } from "@/lib/pravah-mock";
import { PSIBadge, SectionLabel, SevPill } from "./atoms";

const iconFor: Record<string, React.ComponentType<{ className?: string }>> = {
  alert: AlertTriangle,
  drop: Droplets,
  cone: Construction,
  users: Users,
};

const sevTint: Record<Severity, { bg: string; fg: string }> = {
  low:      { bg: "#22c55e22", fg: "#22c55e" },
  moderate: { bg: "#f5a62322", fg: "#f5a623" },
  high:     { bg: "#e03c3c22", fg: "#e03c3c" },
  severe:   { bg: "#8b000044", fg: "#ff5d5d" },
};

export function ActiveEvents() {
  return (
    <div className="rounded-xl border border-[var(--border)] bg-[var(--surface-1)] p-4 flex flex-col">
      <SectionLabel
        right={
          <button className="inline-flex items-center gap-1 text-[11px] font-medium text-[var(--brand-primary)] hover:text-[var(--brand-primary)]">
            View All <ArrowRight className="h-3 w-3" />
          </button>
        }
      >
        Active Events <span className="ml-1 text-foreground">(12)</span>
      </SectionLabel>

      <div className="mt-3 flex flex-col divide-y divide-[var(--surface-3)]">
        {activeEvents.map((e) => {
          const Icon = iconFor[e.icon] ?? AlertTriangle;
          const c = sevTint[e.sev];
          return (
            <button key={e.id} className="group flex items-center gap-3 py-2.5 text-left transition-colors hover:bg-[var(--surface-2)]/60">
              <div className="grid h-8 w-8 shrink-0 place-items-center rounded-full" style={{ background: c.bg, color: c.fg }}>
                <Icon className="h-4 w-4" />
              </div>
              <div className="min-w-0 flex-1 leading-snug">
                <div className="truncate text-[12px] font-semibold text-foreground">{e.type}</div>
                <div className="truncate text-[11px] text-[var(--text-secondary)]">{e.road}</div>
                <div className="truncate text-[10px] text-[var(--text-tertiary)]">{e.near}</div>
              </div>
              <div className="shrink-0 mr-1">
                <PSIBadge score={e.psi} />
              </div>
              <div className="flex shrink-0 flex-col items-end leading-snug">
                <div className="text-[11px] font-medium text-foreground">{e.eta}</div>
                <div className="text-[9px] text-[var(--text-tertiary)]">({e.range})</div>
              </div>
              <ChevronRight className="h-3.5 w-3.5 shrink-0 text-[#3f4757] group-hover:text-[var(--text-tertiary)]" />
            </button>
          );
        })}
      </div>

      <div className="mt-auto pt-3 flex flex-wrap items-center justify-between gap-x-2 gap-y-1.5 border-t border-[var(--surface-3)] text-[9px] font-semibold uppercase tracking-wider">
        <Legend color="#22c55e" label="PSI 0-30 Low" />
        <Legend color="#f5a623" label="31-60 Moderate" />
        <Legend color="#e03c3c" label="61-80 High" />
        <Legend color="#8b0000" label="81-100 Severe" />
      </div>
    </div>
  );
}

function Legend({ color, label }: { color: string; label: string }) {
  return (
    <span className="inline-flex items-center gap-1.5 text-[10px] text-[var(--text-secondary)]">
      <span className="h-2 w-2 rounded-full" style={{ background: color }} /> {label}
    </span>
  );
}

export function CongestionHotspots() {
  return (
    <div className="rounded-xl border border-[var(--border)] bg-[var(--surface-1)] p-4">
      <SectionLabel>
        Congestion Hotspots <span className="ml-1 normal-case text-[10px] tracking-normal text-[var(--text-tertiary)]">(Next 2 Hours)</span>
      </SectionLabel>

      <div className="mt-4 flex gap-3">
        <div className="flex min-w-0 flex-1 flex-col gap-3">
          {hotspots.map((h) => {
            const isHigh = h.sev === "high" || h.sev === "severe";
            const badgeBg = isHigh ? "#e03c3c" : "#22c55e"; // red or green based on screenshot
            const sevColor = isHigh ? "#e03c3c" : "#f5a623"; // red or yellow based on screenshot text
            const sevText = h.sev === "high" || h.sev === "severe" ? "High" : "Medium";
            
            return (
              <div key={h.rank} className="flex items-start gap-2">
                <div 
                  className="mt-[1px] grid h-4 w-4 shrink-0 place-items-center rounded-full text-[9px] font-bold text-white shadow-sm"
                  style={{ background: badgeBg }}
                >
                  {h.rank}
                </div>
                <div className="min-w-0 flex-1">
                  <div className="truncate text-[11.5px] font-medium text-foreground leading-tight">{h.road}</div>
                </div>
                <div className="flex shrink-0 flex-col items-start leading-tight">
                  <span className="text-[10px] font-bold" style={{ color: sevColor }}>{sevText}</span>
                  <span className="text-[9.5px] text-[var(--text-tertiary)]">{h.km}</span>
                </div>
              </div>
            );
          })}
        </div>

        <div className="shrink-0">
          <MiniHeatmap />
        </div>
      </div>

      {/* timeline */}
      <div className="mt-5">
        <div className="relative h-1 rounded-full bg-[var(--surface-3)]">
          <div className="absolute left-0 top-0 h-full w-[40%] rounded-full bg-[var(--text-secondary)]" />
          <div className="absolute left-[40%] top-1/2 grid h-2.5 w-2.5 -translate-x-1/2 -translate-y-1/2 place-items-center rounded-full border border-background bg-[var(--text-secondary)] shadow-sm" />
        </div>
        <div className="mt-2 flex justify-between font-mono text-[9px] text-[var(--text-tertiary)]">
          <span>Now</span><span>+30m</span><span className="font-semibold text-foreground">+1h</span><span>+1.5h</span><span>+2h</span>
        </div>
      </div>

      <button className="mt-5 inline-flex w-full items-center justify-center gap-1.5 rounded-lg border border-[var(--border)] bg-[var(--surface-2)] py-2.5 text-[12px] font-medium text-[var(--brand-primary)] hover:bg-[var(--surface-3)] transition-colors">
        View Full Heatmap <ArrowRight className="h-3.5 w-3.5" />
      </button>
    </div>
  );
}

import Map, { Source, Layer, type HeatmapLayer } from "react-map-gl";
import "mapbox-gl/dist/mapbox-gl.css";
import { useMemo, useState, useEffect } from "react";

const MAPBOX_TOKEN = import.meta.env.VITE_MAPBOX_TOKEN || "pk.eyJ1IjoiZHVtbXkiLCJhIjoiY2R1bW15In0.dummy";

function generateMockHeatmapData() {
  const centers = [
    { lng: 77.68, lat: 12.93, intensity: 1.0 },
    { lng: 77.49, lat: 12.92, intensity: 0.8 },
    { lng: 77.67, lat: 13.00, intensity: 0.6 },
    { lng: 77.62, lat: 12.91, intensity: 0.7 },
  ];
  const points: any[] = [];
  centers.forEach(center => {
    for (let i = 0; i < 50; i++) {
      const u1 = Math.random();
      const u2 = Math.random();
      const z0 = Math.sqrt(-2.0 * Math.log(u1)) * Math.cos(2.0 * Math.PI * u2);
      const z1 = Math.sqrt(-2.0 * Math.log(u1)) * Math.sin(2.0 * Math.PI * u2);
      points.push({
        type: "Feature",
        properties: { weight: Math.max(0.1, center.intensity * Math.random()) },
        geometry: { type: "Point", coordinates: [center.lng + z0 * 0.015, center.lat + z1 * 0.015] }
      });
    }
  });
  return { type: "FeatureCollection", features: points };
}

const heatmapLayer: HeatmapLayer = {
  id: "mini-heat",
  type: "heatmap",
  source: "mini-heatmap-data",
  paint: {
    "heatmap-weight": ["interpolate", ["linear"], ["get", "weight"], 0, 0, 1, 1],
    "heatmap-intensity": 1.5,
    "heatmap-color": [
      "interpolate", ["linear"], ["heatmap-density"],
      0, "rgba(0, 194, 168, 0)",
      0.2, "rgba(34, 197, 94, 0.4)",
      0.4, "rgba(245, 166, 35, 0.6)",
      0.7, "rgba(255, 149, 0, 0.8)",
      1, "rgba(224, 60, 60, 0.9)"
    ],
    "heatmap-radius": 15,
    "heatmap-opacity": 0.8,
  }
};

function MiniHeatmap() {
  const geojsonData = useMemo(() => generateMockHeatmapData(), []);
  const [theme, setTheme] = useState("dark");

  useEffect(() => {
    const isLightMode = document.documentElement.getAttribute("data-theme") === "light";
    setTheme(isLightMode ? "light" : "dark");
  }, []);

  return (
    <div className="h-[130px] w-[130px] overflow-hidden rounded-xl border border-[var(--surface-2)] shadow-inner">
      <Map
        mapboxAccessToken={MAPBOX_TOKEN}
        initialViewState={{ longitude: 77.62, latitude: 12.95, zoom: 9 }}
        mapStyle={theme === "light" ? "mapbox://styles/mapbox/light-v11" : "mapbox://styles/mapbox/dark-v11"}
        interactive={false}
      >
        <Source id="mini-heatmap-data" type="geojson" data={geojsonData}>
          <Layer {...heatmapLayer} />
        </Source>
      </Map>
    </div>
  );
}
