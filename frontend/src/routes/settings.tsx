import { createFileRoute } from "@tanstack/react-router";
import { useState, useEffect } from "react";
import { User, Palette, Map as MapIcon, Bell, Shield, Key, Check } from "lucide-react";

export const Route = createFileRoute("/settings")({
  component: SettingsPage,
});

const tabs = [
  { id: "profile", label: "Profile", icon: User },
  { id: "appearance", label: "Appearance", icon: Palette },
  { id: "map", label: "Map Configuration", icon: MapIcon },
  { id: "notifications", label: "Notifications", icon: Bell },
];

function SettingsPage() {
  const [activeTab, setActiveTab] = useState("profile");
  const [isLight, setIsLight] = useState(false);

  useEffect(() => {
    const isLightMode = document.documentElement.getAttribute("data-theme") === "light";
    setIsLight(isLightMode);
  }, []);

  const toggleTheme = (theme: "light" | "dark") => {
    setIsLight(theme === "light");
    if (theme === "light") {
      document.documentElement.setAttribute("data-theme", "light");
    } else {
      document.documentElement.removeAttribute("data-theme");
    }
  };

  const renderContent = () => {
    switch (activeTab) {
      case "profile":
        return (
          <div className="space-y-6">
            <div>
              <h2 className="text-lg font-semibold text-foreground">Profile Information</h2>
              <p className="text-[13px] text-[var(--text-secondary)]">Update your account details and public profile.</p>
            </div>

            <div className="grid gap-6 border-t border-[var(--border)] pt-6">
              <div className="flex items-center gap-6">
                <div className="flex h-20 w-20 items-center justify-center rounded-full bg-[var(--surface-2)] text-2xl font-semibold text-foreground">
                  AR
                </div>
                <div>
                  <button className="rounded-lg bg-foreground px-4 py-2 text-[13px] font-semibold text-background hover:bg-foreground/90">
                    Change Avatar
                  </button>
                </div>
              </div>

              <div className="grid max-w-xl gap-4">
                <div className="grid gap-2">
                  <label className="text-[13px] font-medium text-foreground">Full Name</label>
                  <input
                    type="text"
                    defaultValue="Ananya Rao"
                    className="rounded-lg border border-[var(--border)] bg-[var(--surface-0)] px-3 py-2 text-[13px] text-foreground focus:border-[var(--brand-primary)] focus:outline-none"
                  />
                </div>
                <div className="grid gap-2">
                  <label className="text-[13px] font-medium text-foreground">Email Address</label>
                  <input
                    type="email"
                    defaultValue="ananya.rao@pravah.gov.in"
                    className="rounded-lg border border-[var(--border)] bg-[var(--surface-0)] px-3 py-2 text-[13px] text-foreground focus:border-[var(--brand-primary)] focus:outline-none"
                  />
                </div>
                <div className="grid gap-2">
                  <label className="text-[13px] font-medium text-foreground">Role</label>
                  <input
                    type="text"
                    defaultValue="Control Room Officer"
                    disabled
                    className="rounded-lg border border-[var(--border)] bg-[var(--surface-1)] px-3 py-2 text-[13px] text-[var(--text-secondary)] cursor-not-allowed"
                  />
                </div>
              </div>
            </div>

            <div className="flex justify-end pt-4">
              <button className="rounded-lg bg-[var(--brand-primary)] px-4 py-2 text-[13px] font-semibold text-white hover:bg-[var(--brand-primary)]/90">
                Save Changes
              </button>
            </div>
          </div>
        );

      case "appearance":
        return (
          <div className="space-y-6">
            <div>
              <h2 className="text-lg font-semibold text-foreground">Appearance</h2>
              <p className="text-[13px] text-[var(--text-secondary)]">Customize how PRAVAH looks on your device.</p>
            </div>

            <div className="grid gap-6 border-t border-[var(--border)] pt-6">
              <div className="grid gap-3">
                <label className="text-[13px] font-medium text-foreground">Theme Preference</label>
                <div className="flex gap-4">
                  <button
                    onClick={() => toggleTheme("light")}
                    className={`flex items-center gap-2 rounded-lg border-2 p-4 transition-colors ${
                      isLight ? "border-[var(--brand-primary)] bg-[var(--surface-1)]" : "border-[var(--border)] bg-[var(--surface-0)] hover:border-[var(--text-secondary)]"
                    }`}
                  >
                    <div className="grid h-12 w-16 place-items-center rounded bg-[#f0f4f8] border border-[#e2e8f0]">
                      <div className="h-2 w-8 rounded bg-[#cbd5e1]" />
                    </div>
                    <div className="flex flex-col items-start gap-1 text-left">
                      <span className="text-[14px] font-medium text-foreground">Light Mode</span>
                      <span className="text-[12px] text-[var(--text-secondary)]">Clean and bright</span>
                    </div>
                  </button>

                  <button
                    onClick={() => toggleTheme("dark")}
                    className={`flex items-center gap-2 rounded-lg border-2 p-4 transition-colors ${
                      !isLight ? "border-[var(--brand-primary)] bg-[var(--surface-1)]" : "border-[var(--border)] bg-[var(--surface-0)] hover:border-[var(--text-secondary)]"
                    }`}
                  >
                    <div className="grid h-12 w-16 place-items-center rounded bg-[#0d0f14] border border-[#252b37]">
                      <div className="h-2 w-8 rounded bg-[#252b37]" />
                    </div>
                    <div className="flex flex-col items-start gap-1 text-left">
                      <span className="text-[14px] font-medium text-foreground">Dark Mode</span>
                      <span className="text-[12px] text-[var(--text-secondary)]">Sleek and easy on eyes</span>
                    </div>
                  </button>
                </div>
              </div>
            </div>
          </div>
        );

      case "map":
        return (
          <div className="space-y-6">
            <div>
              <h2 className="text-lg font-semibold text-foreground">Map Configuration</h2>
              <p className="text-[13px] text-[var(--text-secondary)]">Manage map settings and integrations.</p>
            </div>

            <div className="grid gap-6 border-t border-[var(--border)] pt-6">
              <div className="grid max-w-xl gap-4">
                <div className="grid gap-2">
                  <label className="text-[13px] font-medium text-foreground flex items-center gap-2">
                    <Key className="h-4 w-4" /> Mapbox API Token
                  </label>
                  <div className="flex items-center gap-2">
                    <input
                      type="password"
                      value="************************************"
                      disabled
                      className="w-full rounded-lg border border-[var(--border)] bg-[var(--surface-1)] px-3 py-2 text-[13px] text-[var(--text-secondary)]"
                    />
                    <div className="flex items-center gap-1 rounded bg-[var(--psi-low)]/20 px-2 py-1 text-[11px] font-semibold text-[var(--psi-low)]">
                      <Check className="h-3 w-3" /> Configured via .env
                    </div>
                  </div>
                  <p className="text-[11px] text-[var(--text-tertiary)]">
                    Your token is securely loaded from environment variables and cannot be edited here.
                  </p>
                </div>

                <div className="grid gap-2 mt-4">
                  <label className="text-[13px] font-medium text-foreground">Default View Coordinates</label>
                  <div className="flex gap-4">
                    <div className="flex-1 grid gap-1.5">
                      <span className="text-[11px] text-[var(--text-secondary)]">Latitude</span>
                      <input
                        type="text"
                        defaultValue="12.9716"
                        className="rounded-lg border border-[var(--border)] bg-[var(--surface-0)] px-3 py-2 text-[13px] text-foreground focus:border-[var(--brand-primary)] focus:outline-none"
                      />
                    </div>
                    <div className="flex-1 grid gap-1.5">
                      <span className="text-[11px] text-[var(--text-secondary)]">Longitude</span>
                      <input
                        type="text"
                        defaultValue="77.5946"
                        className="rounded-lg border border-[var(--border)] bg-[var(--surface-0)] px-3 py-2 text-[13px] text-foreground focus:border-[var(--brand-primary)] focus:outline-none"
                      />
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <div className="flex justify-end pt-4">
              <button className="rounded-lg bg-[var(--brand-primary)] px-4 py-2 text-[13px] font-semibold text-white hover:bg-[var(--brand-primary)]/90">
                Save Map Settings
              </button>
            </div>
          </div>
        );

      case "notifications":
        return (
          <div className="space-y-6">
            <div>
              <h2 className="text-lg font-semibold text-foreground">Notifications</h2>
              <p className="text-[13px] text-[var(--text-secondary)]">Control when and how you receive alerts.</p>
            </div>

            <div className="grid gap-4 border-t border-[var(--border)] pt-6 max-w-xl">
              {[
                { label: "High Severity Event Alerts", desc: "Get pushed immediately for any event with PSI > 80", on: true },
                { label: "ETA Delay Warnings", desc: "Notify when unit ETA extends by more than 15 mins", on: true },
                { label: "System Status Reports", desc: "Receive daily summary emails", on: false },
                { label: "Predictive Congestion Alerts", desc: "AI warnings for hotspots likely to form in next 2 hrs", on: true }
              ].map((n, i) => (
                <div key={i} className="flex items-center justify-between rounded-lg border border-[var(--border)] bg-[var(--surface-0)] p-4">
                  <div className="flex flex-col gap-1">
                    <span className="text-[14px] font-medium text-foreground">{n.label}</span>
                    <span className="text-[12px] text-[var(--text-secondary)]">{n.desc}</span>
                  </div>
                  <button className={`relative inline-flex h-5 w-9 shrink-0 cursor-pointer items-center rounded-full transition-colors ${n.on ? "bg-[var(--brand-primary)]" : "bg-[var(--surface-2)]"}`}>
                    <span className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${n.on ? "translate-x-4" : "translate-x-1"}`} />
                  </button>
                </div>
              ))}
            </div>
          </div>
        );

      default:
        return null;
    }
  };

  return (
    <div className="flex h-full flex-col bg-[var(--base)]">
      <div className="border-b border-[var(--border)] bg-background px-8 py-6">
        <h1 className="text-2xl font-bold text-foreground">Settings</h1>
        <p className="mt-1 text-[13px] text-[var(--text-secondary)]">Manage your account settings and preferences.</p>
      </div>

      <div className="flex flex-1 overflow-hidden">
        {/* Sidebar */}
        <aside className="w-[240px] shrink-0 border-r border-[var(--border)] bg-background overflow-y-auto px-4 py-6 custom-scrollbar">
          <nav className="flex flex-col gap-1">
            {tabs.map((tab) => {
              const isActive = activeTab === tab.id;
              const Icon = tab.icon;
              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`flex items-center gap-3 rounded-lg px-3 py-2 text-[13px] transition-colors ${
                    isActive
                      ? "bg-[var(--surface-1)] font-semibold text-foreground"
                      : "text-[var(--text-secondary)] hover:bg-[var(--surface-1)] hover:text-foreground"
                  }`}
                >
                  <Icon className={`h-4 w-4 ${isActive ? "text-foreground" : ""}`} />
                  {tab.label}
                </button>
              );
            })}
          </nav>
        </aside>

        {/* Content Area */}
        <main className="flex-1 overflow-y-auto bg-[var(--base)] p-8 custom-scrollbar">
          <div className="mx-auto max-w-4xl rounded-xl border border-[var(--border)] bg-background p-8 shadow-sm">
            {renderContent()}
          </div>
        </main>
      </div>
    </div>
  );
}
