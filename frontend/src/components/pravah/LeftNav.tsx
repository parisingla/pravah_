import { Link, useLocation } from "@tanstack/react-router";
import {
  Home, Map, AlertTriangle, Brain, TrendingUp, Flame, Route as RouteIcon,
  Truck, FlaskConical, Bell, BarChart3, FileText, Settings, CircleDot,
  ChevronDown, Zap, ChevronsLeft, ChevronsRight, ShieldQuestion, LifeBuoy
} from "lucide-react";
import { useState } from "react";

type NavItem = {
  icon?: any;
  label: string;
  path?: string;
  badge?: string;
  pill?: string;
  badgeTone?: "red" | "default";
  subItems?: NavItem[];
};

const items: NavItem[] = [
  { icon: Home, label: "Dashboard", path: "/" },
  { icon: Map, label: "Live Map", path: "/live-map" },
  {
    icon: Flame,
    label: "Hotspots",
    path: "/hotspots"
  },
  {
    icon: Brain,
    label: "Intelligence",
    subItems: [
      { label: "Triage (NLP)", pill: "New", path: "/triage" },
      { label: "Predictions", path: "/predictions" },
      { label: "What-if Simulator", path: "/simulator" },
    ]
  },
  {
    icon: AlertTriangle,
    label: "Incidents",
    subItems: [
      { label: "Active Events", badge: "19", path: "/events" },
      { label: "Alerts", badge: "5", badgeTone: "red" as const, path: "/alerts" },
    ]
  },
  {
    icon: BarChart3,
    label: "Insights",
    subItems: [
      { label: "Analytics", path: "/analytics" },
      { label: "Reports", path: "/reports" },
    ]
  },
  { icon: LifeBuoy, label: "Support", path: "/support" },
  { icon: Settings, label: "Settings", path: "/settings" },
];

export function LeftNav() {
  const [isCollapsed, setIsCollapsed] = useState(false);
  const [openMenus, setOpenMenus] = useState<Record<string, boolean>>({
    Incidents: true,
  });
  const location = useLocation();

  const toggleMenu = (label: string) => {
    if (isCollapsed) {
      setIsCollapsed(false);
      setOpenMenus((prev) => ({ ...prev, [label]: true }));
    } else {
      setOpenMenus((prev) => ({ ...prev, [label]: !prev[label] }));
    }
  };

  const isActivePath = (path?: string) => {
    if (!path) return false;
    if (path === "/") return location.pathname === "/";
    return location.pathname.startsWith(path);
  };

  const isMenuChildActive = (subItems: NavItem[]) => {
    return subItems.some((it) => isActivePath(it.path));
  };

  return (
    <aside 
      className={`flex h-screen shrink-0 flex-col border-r border-border bg-background transition-all duration-300 ease-in-out ${
        isCollapsed ? "w-[72px]" : "w-[260px]"
      }`}
    >
      {/* Header */}
      <div className={`flex items-center gap-2.5 px-5 py-6 ${isCollapsed ? "justify-center px-0" : ""}`}>
        <div className="font-display text-[22px] font-bold tracking-tight text-foreground flex items-center">
          ACRU<span className="text-[var(--brand-primary)]">.</span>
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex flex-1 flex-col gap-1 overflow-y-auto px-3 overflow-x-hidden pb-4 custom-scrollbar">
        {items.map((it) => {
          const Icon = it.icon;
          const hasSubItems = it.subItems && it.subItems.length > 0;
          const isOpen = openMenus[it.label];
          const isChildActive = hasSubItems ? isMenuChildActive(it.subItems!) : false;
          const isDirectActive = isActivePath(it.path);

          if (hasSubItems) {
            return (
              <div key={it.label} className="flex flex-col">
                <button
                  onClick={() => toggleMenu(it.label)}
                  className={`group flex items-center justify-between rounded-lg px-3 py-2.5 transition-colors ${
                    isChildActive 
                      ? "text-foreground font-semibold" 
                      : "text-[var(--text-secondary)] hover:bg-[var(--surface-1)] hover:text-foreground"
                  } ${isCollapsed ? "justify-center" : ""}`}
                  title={isCollapsed ? it.label : undefined}
                >
                  <div className="flex items-center gap-3">
                    <Icon className={`h-[18px] w-[18px] shrink-0 ${isChildActive ? "text-foreground" : ""}`} />
                    {!isCollapsed && <span className="text-[13px]">{it.label}</span>}
                  </div>
                  {!isCollapsed && (
                    <ChevronDown className={`h-4 w-4 shrink-0 transition-transform ${isOpen ? "rotate-0" : "-rotate-90"}`} />
                  )}
                </button>
                
                {/* Sub items */}
                <div 
                  className={`overflow-hidden transition-all duration-300 ease-in-out ${
                    isOpen && !isCollapsed ? "max-h-[500px] opacity-100" : "max-h-0 opacity-0"
                  }`}
                >
                  <div className="ml-[21px] mt-1 flex flex-col gap-0.5 border-l border-border pl-4 pb-2">
                    {it.subItems!.map((sub) => {
                      const isSubActive = isActivePath(sub.path);
                      return (
                        <Link
                          key={sub.label}
                          to={sub.path!}
                          className={`relative flex items-center justify-between rounded-md px-3 py-2 text-[13px] transition-colors ${
                            isSubActive 
                              ? "bg-[var(--surface-1)] font-medium text-foreground" 
                              : "text-[var(--text-secondary)] hover:bg-[var(--surface-1)] hover:text-foreground"
                          }`}
                        >
                          {isSubActive && <span className="absolute -left-[17px] top-1/2 h-[20px] w-[2px] -translate-y-1/2 bg-foreground" />}
                          <span>{sub.label}</span>
                          
                          <div className="flex items-center gap-1.5">
                            {sub.badge && (
                              <span
                                className={`inline-flex h-5 min-w-5 items-center justify-center rounded-full px-1.5 text-[10px] font-bold ${
                                  sub.badgeTone === "red" 
                                    ? "bg-[var(--psi-severe)] text-white" 
                                    : "bg-foreground text-background"
                                }`}
                              >
                                {sub.badge}
                              </span>
                            )}
                            {sub.pill && (
                              <span className="inline-flex h-5 items-center rounded-full bg-[var(--brand-glow)] px-2 text-[10px] font-semibold text-[var(--brand-primary)]">
                                {sub.pill}
                              </span>
                            )}
                          </div>
                        </Link>
                      );
                    })}
                  </div>
                </div>
              </div>
            );
          }

          // Regular item
          return (
            <Link
              key={it.label}
              to={it.path!}
              className={`group relative flex items-center justify-between rounded-lg px-3 py-2.5 transition-colors ${
                isDirectActive 
                  ? "bg-[var(--surface-1)] font-medium text-foreground" 
                  : "text-[var(--text-secondary)] hover:bg-[var(--surface-1)] hover:text-foreground"
              } ${isCollapsed ? "justify-center" : ""}`}
              title={isCollapsed ? it.label : undefined}
            >
              <div className="flex items-center gap-3">
                {isDirectActive && <span className="absolute left-0 top-1/2 h-[20px] w-[3px] -translate-y-1/2 rounded-r-md bg-foreground" />}
                <Icon className={`h-[18px] w-[18px] shrink-0 ${isDirectActive ? "text-foreground" : ""}`} />
                {!isCollapsed && <span className="text-[13px]">{it.label}</span>}
              </div>
              
              {!isCollapsed && it.badge && (
                <span
                  className={`inline-flex h-5 min-w-5 items-center justify-center rounded-full px-1.5 text-[10px] font-bold ${
                    it.badgeTone === "red" 
                      ? "bg-[var(--psi-severe)] text-white" 
                      : "bg-[var(--surface-3)] text-[var(--text-secondary)]"
                  }`}
                >
                  {it.badge}
                </span>
              )}
            </Link>
          );
        })}
      </nav>

      {/* Bottom Section */}
      <div className="mt-auto flex flex-col gap-2 p-4">
        {/* Collapse Toggle */}
        <button
          onClick={() => setIsCollapsed(!isCollapsed)}
          className={`flex items-center gap-2 rounded-lg py-3 text-[13px] font-medium text-[var(--text-secondary)] transition-colors hover:text-foreground ${
            isCollapsed ? "justify-center" : "px-2"
          }`}
        >
          {isCollapsed ? <ChevronsRight className="h-4 w-4" /> : <ChevronsLeft className="h-4 w-4" />}
          {!isCollapsed && <span>Collapse sidebar</span>}
        </button>
      </div>
    </aside>
  );
}
