export type Severity = "low" | "moderate" | "high" | "severe";

export const summaryMetrics = [
  { label: "Active Events", value: "12", delta: "↑ 3 vs yesterday", deltaTone: "bad", accent: "teal", icon: "shield" },
  { label: "Predicted Delay", value: "4h 32m", delta: "↑ 18% vs yesterday", deltaTone: "bad", accent: "amber", icon: "alert" },
  { label: "Units Deployed", value: "28 / 45", delta: "62% utilized", deltaTone: "neutral", accent: "purple", icon: "users" },
  { label: "Severe Events", value: "3", delta: "High Impact", deltaTone: "bad", accent: "red", icon: "siren" },
];

export const fleetRows = [
  { type: "Truck",  count: 42, pct: 84 },
  { type: "Van",    count: 23, pct: 60 },
  { type: "Car",    count: 15, pct: 40 },
  { type: "Trailer", count: 9, pct: 30 },
  { type: "M-Cycle", count: 3, pct: 10 },
];

export const fuelBars = Array.from({ length: 56 }, (_, i) =>
  20 + Math.round(40 + 35 * Math.sin(i / 3) + (i % 4) * 6 + ((i * 7) % 11))
);

export const orders = [
  { id: "#AB045861", customer: "TNA Groups",   tag: "Electronics", from: "Brooklyn, New York",    to: "South Bronx, New York",     weight: "1,200 kg", eta: "12 Sep, 2025", status: "In Transit" },
  { id: "#BC022341", customer: "Gravitas LLC", tag: "Logistics",   from: "Manhattan, New York",   to: "Queens, New York",          weight: "650 kg",   eta: "14 Oct, 2025", status: "Picked Up" },
  { id: "#AB045863", customer: "BVI GROUP",    tag: "Telecom",     from: "Beverly Hills, Los Angeles", to: "Santa Monica, Los Angeles", weight: "1,352 kg", eta: "25 Oct, 2025", status: "Delivered" },
  { id: "#CA012341", customer: "MEGAONE",      tag: "Sports",      from: "Mitte, Berlin",         to: "Kreuzberg, Berlin",         weight: "45 kg",    eta: "05 Oct, 2025", status: "In Transit" },
];

export const activeEvents = [
  { id: "EVT-04561", type: "Breakdown",       icon: "alert",  sev: "high"     as Severity, road: "Mysore Rd",       near: "Near Kengeri",   psi: 72, eta: "1h 15m", range: "35m – 2h 40m" },
  { id: "EVT-04562", type: "Waterlogging",    icon: "drop",   sev: "high"     as Severity, road: "ORR",             near: "Bellandur",      psi: 64, eta: "55m",   range: "20m – 1h 40m" },
  { id: "EVT-04563", type: "Accident",        icon: "alert",  sev: "severe"   as Severity, road: "Silk Board",      near: "Near BTM",       psi: 81, eta: "1h 40m", range: "45m – 3h 10m" },
  { id: "EVT-04564", type: "Construction",    icon: "cone",   sev: "moderate" as Severity, road: "Old Madras Rd",   near: "Near KR Puram",  psi: 59, eta: "2h 25m", range: "1h – 4h 30m" },
  { id: "EVT-04565", type: "Rally / Procession", icon: "users", sev: "severe" as Severity, road: "MG Road",         near: "Near Trinity",   psi: 88, eta: "2h 10m", range: "55m – 4h 5m" },
];

export const hotspots = [
  { rank: 1, road: "ORR – Marathahalli",      sev: "high"     as Severity, km: "2.4 km" },
  { rank: 2, road: "ORR – Bellandur",         sev: "high"     as Severity, km: "2.1 km" },
  { rank: 3, road: "Mysore Rd – Kengeri",     sev: "high"     as Severity, km: "1.8 km" },
  { rank: 4, road: "Old Madras Rd – KR Puram", sev: "moderate" as Severity, km: "1.5 km" },
  { rank: 5, road: "Hosur Rd – Silk Board",   sev: "moderate" as Severity, km: "1.3 km" },
];

export const mapMarkers = [
  { id: "m1", x: 380, y: 130, sev: "moderate" as Severity, kind: "vehicle" },
  { id: "m2", x: 520, y: 110, sev: "moderate" as Severity, kind: "alert" },
  { id: "m3", x: 320, y: 250, sev: "severe"   as Severity, kind: "alert", selected: true },
  { id: "m4", x: 600, y: 230, sev: "low"      as Severity, kind: "vehicle" },
  { id: "m5", x: 720, y: 250, sev: "moderate" as Severity, kind: "vehicle" },
  { id: "m6", x: 460, y: 340, sev: "severe"   as Severity, kind: "alert" },
  { id: "m7", x: 580, y: 380, sev: "moderate" as Severity, kind: "alert" },
  { id: "m8", x: 700, y: 340, sev: "low"      as Severity, kind: "vehicle" },
  { id: "m9", x: 380, y: 430, sev: "severe"   as Severity, kind: "alert" },
  { id: "m10", x: 720, y: 470, sev: "moderate" as Severity, kind: "alert" },
];
