import { createFileRoute } from "@tanstack/react-router";
import { useMemo, useState, useEffect, useRef } from "react";
import Map, { Source, Layer, NavigationControl, type HeatmapLayer, type MapRef } from "react-map-gl";
import "mapbox-gl/dist/mapbox-gl.css";
import { hotspots, type Severity } from "@/lib/pravah-mock";
import { Filter, Flame, Info } from "lucide-react";

export const Route = createFileRoute("/hotspots")({
  component: HotspotsPage,
});

const MAPBOX_TOKEN = import.meta.env.VITE_MAPBOX_TOKEN || "pk.eyJ1IjoiZHVtbXkiLCJhIjoiY2R1bW15In0.dummy";

const sevTint: Record<Severity, { bg: string; fg: string }> = {
  low: { bg: "var(--psi-low-bg, #22c55e33)", fg: "var(--psi-low, #22c55e)" },
  moderate: { bg: "var(--psi-moderate-bg, #f5a62333)", fg: "var(--psi-moderate, #f5a623)" },
  high: { bg: "var(--psi-high-bg, #ff950033)", fg: "var(--psi-high, #ff9500)" },
  severe: { bg: "var(--psi-severe-bg, #e03c3c33)", fg: "var(--psi-severe, #e03c3c)" },
};

function SevPill({ sev }: { sev: Severity }) {
  const c = sevTint[sev];
  return (
    <span 
      className="inline-flex h-[18px] items-center rounded-full px-1.5 text-[9px] font-bold uppercase tracking-wider" 
      style={{ background: c.bg, color: c.fg }}
    >
      {sev}
    </span>
  );
}

// Generate clustered mock data around Bengaluru
function generateMockHeatmapData() {
  const centers = [
    { lng: 77.68, lat: 12.93, intensity: 1.0 }, // ORR Bellandur/Marathahalli area
    { lng: 77.49, lat: 12.92, intensity: 0.8 }, // Mysore Rd Kengeri
    { lng: 77.67, lat: 13.00, intensity: 0.6 }, // Old Madras Rd KR Puram
    { lng: 77.62, lat: 12.91, intensity: 0.7 }, // Silk Board
  ];

  const points: any[] = [];
  
  centers.forEach(center => {
    // Generate ~150 points around each center using normal distribution approximation
    for (let i = 0; i < 150; i++) {
      // Box-Muller transform for normal distribution
      const u1 = Math.random();
      const u2 = Math.random();
      const z0 = Math.sqrt(-2.0 * Math.log(u1)) * Math.cos(2.0 * Math.PI * u2);
      const z1 = Math.sqrt(-2.0 * Math.log(u1)) * Math.sin(2.0 * Math.PI * u2);
      
      const spread = 0.015; // roughly 1.5km spread
      const lng = center.lng + z0 * spread;
      const lat = center.lat + z1 * spread;
      
      // Random weight between 0.1 and center.intensity
      const weight = Math.max(0.1, center.intensity * Math.random());
      
      points.push({
        type: "Feature",
        properties: { weight },
        geometry: { type: "Point", coordinates: [lng, lat] }
      });
    }
  });

  // Add some random noise points
  for (let i = 0; i < 100; i++) {
    points.push({
      type: "Feature",
      properties: { weight: Math.random() * 0.3 },
      geometry: { 
        type: "Point", 
        coordinates: [77.5 + Math.random() * 0.3, 12.85 + Math.random() * 0.25] 
      }
    });
  }

  return {
    type: "FeatureCollection",
    features: points
  };
}

const heatmapLayer: HeatmapLayer = {
  id: "congestion-heat",
  type: "heatmap",
  source: "congestion-data",
  paint: {
    // Increase the heatmap weight based on the 'weight' property
    "heatmap-weight": [
      "interpolate",
      ["linear"],
      ["get", "weight"],
      0, 0,
      1, 1
    ],
    // Increase the heatmap color weight by zoom level
    // heatmap-intensity is a multiplier on top of heatmap-weight
    "heatmap-intensity": [
      "interpolate",
      ["linear"],
      ["zoom"],
      0, 1,
      15, 3
    ],
    // Color scale mapping from density to color
    "heatmap-color": [
      "interpolate",
      ["linear"],
      ["heatmap-density"],
      0, "rgba(0, 194, 168, 0)",      // Brand Primary, transparent
      0.2, "rgba(34, 197, 94, 0.4)",  // Low (green)
      0.4, "rgba(245, 166, 35, 0.6)", // Moderate (amber)
      0.7, "rgba(255, 149, 0, 0.8)",  // High (orange)
      1, "rgba(224, 60, 60, 0.9)"     // Severe (red)
    ],
    // Adjust the heatmap radius by zoom level
    "heatmap-radius": [
      "interpolate",
      ["linear"],
      ["zoom"],
      10, 15,
      15, 40
    ],
    // Transition from heatmap to circle layer by zoom level
    "heatmap-opacity": [
      "interpolate",
      ["linear"],
      ["zoom"],
      10, 0.8,
      16, 0.4
    ],
  }
};

function HotspotsPage() {
  const [theme, setTheme] = useState("dark");
  const [activeFilter, setActiveFilter] = useState("Now");
  const mapRef = useRef<MapRef>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  
  const geojsonData = useMemo(() => generateMockHeatmapData(), []);

  useEffect(() => {
    const isLightMode = document.documentElement.getAttribute("data-theme") === "light";
    setTheme(isLightMode ? "light" : "dark");
    
    const observer = new MutationObserver(() => {
      const isLightMode = document.documentElement.getAttribute("data-theme") === "light";
      setTheme(isLightMode ? "light" : "dark");
    });
    
    observer.observe(document.documentElement, { attributes: true, attributeFilter: ["data-theme"] });
    return () => observer.disconnect();
  }, []);

  useEffect(() => {
    if (!containerRef.current) return;
    const resizeObserver = new ResizeObserver(() => {
      mapRef.current?.resize();
    });
    resizeObserver.observe(containerRef.current);
    return () => resizeObserver.disconnect();
  }, []);

  const mapStyle = theme === "light" 
    ? "mapbox://styles/mapbox/light-v11" 
    : "mapbox://styles/mapbox/dark-v11";

  return (
    <div className="relative flex h-full w-full overflow-hidden bg-[var(--base)]">
      
      {/* Fullscreen Map */}
      <div ref={containerRef} className="absolute inset-0">
        <Map
          ref={mapRef}
          mapboxAccessToken={MAPBOX_TOKEN}
          initialViewState={{
            longitude: 77.6246,
            latitude: 12.9516,
            zoom: 11.5
          }}
          mapStyle={mapStyle}
        >
          <Source id="congestion-data" type="geojson" data={geojsonData}>
            <Layer {...heatmapLayer} />
          </Source>
          
          <NavigationControl position="bottom-right" />
        </Map>
      </div>

      {/* Floating UI Overlay */}
      <div className="pointer-events-none absolute inset-y-0 left-0 flex w-[380px] flex-col p-6">
        <div className="pointer-events-auto flex h-full flex-col overflow-hidden rounded-xl border border-[var(--border)] bg-background/95 shadow-2xl backdrop-blur-md">
          
          {/* Header */}
          <div className="flex items-center justify-between border-b border-[var(--border)] px-5 py-4">
            <div className="flex items-center gap-2">
              <Flame className="h-5 w-5 text-[var(--brand-primary)]" />
              <h2 className="text-[15px] font-bold text-foreground">Congestion Hotspots</h2>
            </div>
            <button className="grid h-8 w-8 place-items-center rounded-md border border-[var(--border)] bg-[var(--surface-1)] text-[var(--text-secondary)] hover:text-foreground">
              <Filter className="h-4 w-4" />
            </button>
          </div>

          {/* Filters */}
          <div className="flex items-center gap-1.5 border-b border-[var(--border)] bg-[var(--surface-0)] px-5 py-3">
            {["Now", "+1 Hour", "+2 Hours", "+4 Hours"].map((f) => (
              <button
                key={f}
                onClick={() => setActiveFilter(f)}
                className={`rounded-full px-3 py-1.5 text-[11px] font-semibold transition-colors ${
                  activeFilter === f 
                    ? "bg-foreground text-background" 
                    : "bg-[var(--surface-2)] text-[var(--text-secondary)] hover:text-foreground"
                }`}
              >
                {f}
              </button>
            ))}
          </div>

          {/* Info Banner */}
          <div className="flex items-start gap-2 bg-[var(--psi-low-bg)] px-5 py-3 text-[11px] text-foreground">
            <Info className="mt-0.5 h-3.5 w-3.5 shrink-0 text-[var(--psi-low)]" />
            <p>
              Heatmap intensity is calculated based on real-time vehicle density, historical bottleneck patterns, and active severity incidents.
            </p>
          </div>

          {/* Top Hotspots List */}
          <div className="flex-1 overflow-y-auto custom-scrollbar p-5">
            <h3 className="mb-4 text-[11px] font-bold uppercase tracking-wider text-[var(--text-tertiary)]">
              Top Critical Zones
            </h3>
            
            <div className="flex flex-col gap-3">
              {hotspots.map((h) => (
                <div key={h.rank} className="group relative flex items-center gap-3 rounded-lg border border-[var(--border-muted)] bg-[var(--surface-1)] p-3 transition-colors hover:border-[var(--border)] hover:bg-[var(--surface-2)] cursor-pointer">
                  <div className="grid h-6 w-6 shrink-0 place-items-center rounded-full bg-[var(--surface-3)] font-mono text-[11px] font-bold text-[var(--text-secondary)]">
                    {h.rank}
                  </div>
                  <div className="min-w-0 flex-1">
                    <div className="truncate text-[13px] font-semibold text-foreground">{h.road}</div>
                    <div className="flex items-center gap-2 mt-0.5">
                      <span className="font-mono text-[10px] text-[var(--text-tertiary)]">{h.km} Affected</span>
                    </div>
                  </div>
                  <SevPill sev={h.sev} />
                </div>
              ))}
            </div>
          </div>
          
          {/* Legend */}
          <div className="border-t border-[var(--border)] bg-[var(--surface-0)] p-4">
            <div className="flex items-center justify-between text-[10px] font-semibold uppercase tracking-wider text-[var(--text-secondary)]">
              <span>Low Density</span>
              <span>Severe Blockage</span>
            </div>
            <div className="mt-2 h-2 w-full rounded-full bg-gradient-to-r from-[rgba(34,197,94,0.5)] via-[rgba(245,166,35,0.8)] to-[rgba(224,60,60,1)]" />
          </div>

        </div>
      </div>
    </div>
  );
}
