import { Search, Bell, ChevronDown, Cloud, Moon, Sun, LogOut } from "lucide-react";
import { useEffect, useState } from "react";
import { supabase } from "@/lib/supabase";
import { useNavigate } from "@tanstack/react-router";

export function TopBar() {
  const [isLight, setIsLight] = useState(false);
  const [userEmail, setUserEmail] = useState<string | null>(null);
  const navigate = useNavigate();

  useEffect(() => {
    const isLightMode = document.documentElement.getAttribute("data-theme") === "light";
    setIsLight(isLightMode);

    // Get current user session
    supabase.auth.getSession().then(({ data: { session } }) => {
      setUserEmail(session?.user?.email || null);
    });

    // Listen for auth state changes
    const { data: { subscription } } = supabase.auth.onAuthStateChange((_event, session) => {
      setUserEmail(session?.user?.email || null);
    });

    return () => subscription.unsubscribe();
  }, []);

  const toggleTheme = () => {
    const newTheme = isLight ? "dark" : "light";
    setIsLight(!isLight);
    if (newTheme === "light") {
      document.documentElement.setAttribute("data-theme", "light");
    } else {
      document.documentElement.removeAttribute("data-theme");
    }
  };

  const handleLogout = async () => {
    await supabase.auth.signOut();
    navigate({ to: "/login" });
  };

  return (
    <div className="flex h-[72px] shrink-0 items-center gap-4 border-b border-[var(--border)] px-6 transition-colors duration-200">
      <div className="min-w-[220px]">
        <div className="flex items-center gap-1.5 text-[15px] font-semibold text-foreground">
          Traffic Control Room
          <ChevronDown className="h-4 w-4 text-[var(--text-secondary)]" />
        </div>
        <div className="mt-0.5 text-[12px] text-[var(--text-secondary)]">Bengaluru, India</div>
      </div>

      <div className="relative mx-auto flex h-10 w-full max-w-[520px] items-center gap-2 rounded-lg border border-[var(--border)] bg-[var(--surface-0)] px-3 text-[13px]">
        <Search className="h-4 w-4 text-[var(--text-secondary)]" />
        <input
          placeholder="Search events, locations, corridors…"
          className="h-full w-full bg-transparent text-foreground placeholder:text-[var(--text-secondary)] focus:outline-none"
        />
      </div>

      <div className="flex h-11 items-center gap-2.5 rounded-lg border border-[var(--border)] bg-[var(--surface-0)] px-3">
        <Cloud className="h-5 w-5 text-[var(--text-secondary)]" />
        <div className="leading-tight">
          <div className="font-mono text-[14px] font-semibold text-foreground">27°C</div>
          <div className="text-[10px] text-[var(--text-secondary)]">Partly Cloudy</div>
        </div>
      </div>

      <button className="relative grid h-10 w-10 place-items-center rounded-lg border border-[var(--border)] bg-[var(--surface-0)] text-foreground">
        <Bell className="h-4.5 w-4.5" />
        <span className="absolute -right-1 -top-1 grid h-4.5 min-w-4.5 place-items-center rounded-full bg-[var(--psi-severe)] px-1 text-[10px] font-bold text-white">5</span>
      </button>

      <button onClick={toggleTheme} className="grid h-10 w-10 place-items-center rounded-lg border border-[var(--border)] bg-[var(--surface-0)] text-foreground transition-colors hover:bg-[var(--surface-1)]">
        {isLight ? <Moon className="h-4.5 w-4.5" /> : <Sun className="h-4.5 w-4.5" />}
      </button>

      <div className="flex items-center gap-3 rounded-lg border border-[var(--border)] bg-[var(--surface-0)] py-1.5 pl-1.5 pr-2">
        <div className="grid h-9 w-9 place-items-center overflow-hidden rounded-md bg-[var(--brand-primary)] text-white text-[13px] font-bold">
          {userEmail ? userEmail.charAt(0).toUpperCase() : "U"}
        </div>
        <div className="leading-tight max-w-[150px]">
          <div className="text-[13px] font-semibold text-foreground truncate" title={userEmail || "Guest User"}>
            {userEmail || "Guest User"}
          </div>
          <div className="text-[11px] text-[var(--text-secondary)]">
            {userEmail ? "Authenticated" : "Not Logged In"}
          </div>
        </div>
        
        {userEmail ? (
          <button 
            onClick={handleLogout}
            className="ml-1 rounded-md p-1.5 text-[var(--text-secondary)] hover:bg-[var(--surface-2)] hover:text-[var(--psi-severe)] transition-colors"
            title="Log Out"
          >
            <LogOut className="h-4 w-4" />
          </button>
        ) : (
          <ChevronDown className="ml-1 h-4 w-4 text-[var(--text-secondary)]" />
        )}
      </div>
    </div>
  );
}
