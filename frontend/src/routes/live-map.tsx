import { createFileRoute } from "@tanstack/react-router";
import { LiveMap } from "@/components/pravah/LiveMap";

export const Route = createFileRoute("/live-map")({
  component: RouteComponent,
});

function RouteComponent() {
  return (
    <div className="h-full p-4">
      <LiveMap />
    </div>
  );
}
