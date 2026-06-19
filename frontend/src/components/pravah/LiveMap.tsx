import { AlertTriangle, Truck, Layers, Search, ChevronDown, Maximize2 } from "lucide-react";
import { mapMarkers, type Severity } from "@/lib/pravah-mock";
import { SectionLabel } from "./atoms";
import { useState, useEffect, useRef } from "react";
import Map, { Marker, NavigationControl, type MapRef } from "react-map-gl";
import "mapbox-gl/dist/mapbox-gl.css";

const sevHex: Record<Severity, string> = {
  low: "var(--psi-low)", moderate: "var(--psi-moderate)", high: "var(--psi-high)", severe: "var(--psi-severe)",
};

const MAPBOX_TOKEN = import.meta.env.VITE_MAPBOX_TOKEN || "pk.eyJ1IjoiZHVtbXkiLCJhIjoiY2R1bW15In0.dummy";

export function LiveMap() {
  const [theme, setTheme] = useState("dark");
  const mapRef = useRef<MapRef>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const isLightMode = document.documentElement.getAttribute("data-theme") === "light";
    setTheme(isLightMode ? "light" : "dark");
    
    // Listen for theme changes on document
    const themeObserver = new MutationObserver(() => {
      const isLightMode = document.documentElement.getAttribute("data-theme") === "light";
      setTheme(isLightMode ? "light" : "dark");
    });
    
    themeObserver.observe(document.documentElement, { attributes: true, attributeFilter: ["data-theme"] });
    return () => themeObserver.disconnect();
  }, []);

  useEffect(() => {
    if (!containerRef.current) return;
    const resizeObserver = new ResizeObserver(() => {
      // Force Mapbox to resize when the container's size changes (e.g., sidebar collapse)
      mapRef.current?.resize();
    });
    resizeObserver.observe(containerRef.current);
    return () => resizeObserver.disconnect();
  }, []);

  const mapStyle = theme === "light" 
    ? "mapbox://styles/mapbox/navigation-day-v1" 
    : "mapbox://styles/mapbox/navigation-night-v1";

  return (
    <div className="relative flex h-full flex-col overflow-hidden rounded-xl border border-[var(--border)] bg-[var(--surface-0)]">
      {/* Header controls */}
      <div className="flex items-center justify-between gap-3 border-b border-[var(--border)] bg-[var(--surface-0)] px-4 py-3">
        <button className="inline-flex items-center gap-2 rounded-md border border-[var(--border)] bg-[var(--surface-1)] px-3 py-1.5 text-[12px] text-foreground">
          <Layers className="h-3.5 w-3.5 text-[var(--text-tertiary)]" /> All Layers <ChevronDown className="h-3.5 w-3.5 text-[var(--text-tertiary)]" />
        </button>
        <div className="flex h-8 flex-1 items-center gap-2 rounded-md border border-[var(--border)] bg-[var(--surface-1)] px-3 text-[12px]">
          <Search className="h-3.5 w-3.5 text-[var(--text-tertiary)]" />
          <input className="h-full w-full bg-transparent placeholder:text-[var(--text-tertiary)] focus:outline-none" placeholder="Bengaluru, Karnataka" defaultValue="Bengaluru, Karnataka" />
        </div>
        <div className="flex items-center gap-2 text-[12px] text-[var(--text-secondary)]">
          Sort by
          <button className="inline-flex items-center gap-1.5 rounded-md border border-[var(--border)] bg-[var(--surface-1)] px-2.5 py-1.5 text-foreground">
            Severity <ChevronDown className="h-3.5 w-3.5 text-[var(--text-tertiary)]" />
          </button>
        </div>
        <button className="grid h-8 w-8 place-items-center rounded-md border border-[var(--border)] bg-[var(--surface-1)] text-[var(--text-secondary)] hover:text-foreground">
          <Maximize2 className="h-3.5 w-3.5" />
        </button>
      </div>

      {/* Map canvas */}
      <div ref={containerRef} className="relative flex-1 overflow-hidden bg-[var(--base)]">
        <Map
          ref={mapRef}
          mapboxAccessToken={MAPBOX_TOKEN}
          initialViewState={{
            longitude: 77.5946,
            latitude: 12.9716,
            zoom: 11
          }}
          mapStyle={mapStyle}
        >
          <NavigationControl position="bottom-right" />
          
          {/* Map markers are adapted from mock data. We assume m.x and m.y in mock were screen coords. 
              We'll randomly distribute them around Bengaluru for the demo since the mock has screen coords. */}
          {mapMarkers.map((m) => {
            const isAlert = m.kind === "alert";
            const color = sevHex[m.sev];
            const showPulse = m.sev === "severe" || m.sev === "high";
            
            // Map the SVG x,y (900x600) to actual lat/lng around Bengaluru
            // Bengaluru approx range: lng 77.5 to 77.7, lat 12.85 to 13.05
            const lng = 77.5 + (m.x / 900) * 0.2;
            const lat = 13.05 - (m.y / 600) * 0.2;

            return (
              <Marker key={m.id} longitude={lng} latitude={lat} anchor="center">
                <div className="relative flex items-center justify-center">
                  {showPulse && isAlert && (
                    <div 
                      className="absolute rounded-full pulse-ring" 
                      style={{ width: '28px', height: '28px', border: `2px solid ${color}` }}
                    />
                  )}
                  <div 
                    className="flex h-7 w-7 items-center justify-center rounded-full border-2 border-[var(--base)]" 
                    style={{ backgroundColor: isAlert ? color : "var(--brand-primary)" }}
                  >
                    {isAlert ? (
                      <AlertTriangle className="h-3.5 w-3.5 text-white" />
                    ) : (
                      <Truck className="h-3.5 w-3.5 text-white" />
                    )}
                  </div>
                </div>
              </Marker>
            );
          })}
        </Map>

        {/* Selected event tooltip */}
        <div className="absolute left-4 top-4 w-[230px] rounded-lg border border-[var(--border)] bg-[var(--surface-2)]/95 p-3 text-[12px] shadow-2xl backdrop-blur">
          <div className="flex items-center justify-between gap-2">
            <span className="font-mono text-[11px] font-semibold text-[var(--text-secondary)]">#EVT-04561</span>
          </div>
          <div className="mt-1 flex items-center justify-between gap-2">
            <div className="text-[13px] font-semibold text-foreground">Breakdown</div>
            <span className="inline-flex h-5 items-center rounded bg-[var(--psi-high-bg)] px-1.5 text-[10px] font-semibold uppercase tracking-wider text-[var(--psi-high)]">High</span>
          </div>
          <div className="mt-1 text-[11px] text-[var(--text-secondary)]">Mysore Rd, Near Kengeri</div>
          <div className="mt-2 border-t border-[var(--border)] pt-2 text-[11px] text-[var(--text-secondary)]">
            ETA Impact: <span className="font-mono font-semibold text-foreground">1h 15m</span>
          </div>
        </div>
      </div>
    </div>
  );
}

export function LiveMapLegend() {
  return <SectionLabel>Live Map</SectionLabel>;
}
