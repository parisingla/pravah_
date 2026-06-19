import { createFileRoute } from "@tanstack/react-router";
import { LiveMap } from "@/components/pravah/LiveMap";
import { TodaySummary, FleetDistribution, FuelUsage, OrdersTable } from "@/components/pravah/CenterPanels";
import { ActiveEvents, CongestionHotspots } from "@/components/pravah/SidePanels";

export const Route = createFileRoute("/")({
  head: () => ({
    meta: [
      { title: "PRAVAH — Traffic Control Room" },
      { name: "description", content: "Real-time urban traffic command center: monitor events, dispatch units, predict corridor delays." },
      { property: "og:title", content: "PRAVAH — Traffic Control Room" },
      { property: "og:description", content: "Monitor live city traffic events, dispatch units, and predict corridor delays from one screen." },
    ],
  }),
  component: Overview,
});

function Overview() {
  return (
    <div className="grid h-full grid-cols-[300px_minmax(0,1fr)_340px] gap-4 p-4 overflow-hidden">
      {/* Left panel */}
      <div className="flex min-h-0 flex-col gap-4 overflow-y-auto pr-1 custom-scrollbar pb-2">
        <TodaySummary />
        <FleetDistribution />
        <FuelUsage />
      </div>

      {/* Center map */}
      <div className="min-h-0 overflow-hidden rounded-xl border border-[var(--border)] relative">
        <LiveMap />
      </div>

      {/* Right panel */}
      <div className="flex min-h-0 flex-col gap-4 overflow-y-auto pr-1 custom-scrollbar pb-2">
        <ActiveEvents />
        <CongestionHotspots />
      </div>
    </div>
  );
}
