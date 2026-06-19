# PRAVAH — Traffic Control Room Dashboard
## Design System & Specification

> **Product:** PRAVAH (प्रवाह) — Real-time urban traffic intelligence platform  
> **Audience:** Control room officers, fleet dispatchers, traffic authority supervisors  
> **Page's single job:** Give an operator everything they need to assess, triage, and act on traffic events at a glance — without switching screens.

---

## 1. Design Philosophy

PRAVAH sits at the intersection of **mission-critical reliability** and **fluid situational awareness**. The visual language borrows from aerospace control rooms and air traffic systems: dense, information-rich, but never cluttered. Every pixel earns its place.

The **signature element**: a living city map as the gravitational center of the layout — not a decorative backdrop, but the primary data surface. Every panel around it is a satellite reading that feeds back to the map.

The aesthetic risk: **PSI color encoding bleeds out of the event cards and into the UI chrome itself** — severity tinting subtly washes the background of the right panel when aggregate stress is high, making the dashboard's own skin respond to city conditions.

---

## 2. Color Palette

### 2.1 Dark Theme (Primary / Default)

```
Surface hierarchy (from deepest to highest):
─────────────────────────────────────────────
--color-base         #0A0D12   ← Sidebar / canvas void
--color-surface-0    #10141C   ← Main content background
--color-surface-1    #161B26   ← Card backgrounds
--color-surface-2    #1E2535   ← Elevated cards / tooltips
--color-surface-3    #252D40   ← Hover states, input fills
--color-border       #2B3451   ← Dividers, card outlines
--color-border-muted #1D2233   ← Subtle rules
```

```
Brand:
────────────────────────────────────────────────────
--color-brand-primary     #00C896   ← PRAVAH teal (logo, active nav, success)
--color-brand-glow        #00C89620 ← Glow halos behind active elements
--color-brand-hindi       #00C896   ← प्रवाह text in sidebar
```

```
Severity / PSI System (core semantic colors):
────────────────────────────────────────────────────
--color-psi-low          #4ADE80   ← PSI 0–30  · Safe · Green
--color-psi-low-bg       #4ADE8015
--color-psi-moderate     #FACC15   ← PSI 31–60 · Caution · Amber
--color-psi-moderate-bg  #FACC1515
--color-psi-high         #F97316   ← PSI 61–80 · High · Orange
--color-psi-high-bg      #F9731615
--color-psi-severe       #EF4444   ← PSI 81–100 · Severe · Red
--color-psi-severe-bg    #EF444415
```

```
Event type accents:
────────────────────────────────────────────────────
--color-event-breakdown   #EF4444   ← Red triangle
--color-event-waterlog    #3B82F6   ← Blue water
--color-event-accident    #EF4444   ← Red (critical)
--color-event-construct   #F97316   ← Orange (ongoing)
--color-event-rally       #EF4444   ← Red (high impact)
```

```
Text:
────────────────────────────────────────────────────
--color-text-primary   #F0F4FF   ← Primary labels, headings
--color-text-secondary #8B95B0   ← Supporting labels, subtitles
--color-text-tertiary  #4D5A77   ← Timestamps, metadata
--color-text-disabled  #2D3752   ← Inactive states
--color-text-brand     #00C896   ← Links, active items, up-trend
--color-text-warning   #FACC15   ← Warnings, delta badges
```

```
Data / Chart tones:
────────────────────────────────────────────────────
--color-chart-diesel   #F97316
--color-chart-gasoline #FACC15
--color-chart-bar      #3B82F6
--color-chart-bar-alt  #00C896
```

```
Status badges:
────────────────────────────────────────────────────
--color-status-in-transit  #3B82F620, text #93C5FD
--color-status-picked-up   #00C89620, text #00C896
--color-status-delivered   #4ADE8020, text #4ADE80
--color-status-pending     #FACC1520, text #FACC15
```

---

### 2.2 Light Theme

```
Surface hierarchy:
────────────────────────────────────────────────────
--color-base         #F0F2F8   ← Page background
--color-surface-0    #FFFFFF   ← Primary card bg
--color-surface-1    #F4F6FB   ← Nested card / table row bg
--color-surface-2    #E8ECF4   ← Hover / elevated states
--color-surface-3    #DCE1EE   ← Active wells, input fills
--color-border       #CBD2E5   ← Dividers
--color-border-muted #E2E6F0   ← Subtle rules
```

```
Brand (unchanged — teal reads equally on light):
────────────────────────────────────────────────────
--color-brand-primary     #009F77   ← Slightly deeper teal for light
--color-brand-glow        #009F7715
```

```
Severity / PSI (shifted for readability on white):
────────────────────────────────────────────────────
--color-psi-low          #16A34A
--color-psi-low-bg       #DCFCE7
--color-psi-moderate     #CA8A04
--color-psi-moderate-bg  #FEF9C3
--color-psi-high         #EA580C
--color-psi-high-bg      #FFEDD5
--color-psi-severe       #DC2626
--color-psi-severe-bg    #FEE2E2
```

```
Text (inverted):
────────────────────────────────────────────────────
--color-text-primary   #111827
--color-text-secondary #4B5563
--color-text-tertiary  #9CA3AF
--color-text-disabled  #D1D5DB
--color-text-brand     #009F77
--color-text-warning   #CA8A04
```

```
Status badges (light):
────────────────────────────────────────────────────
--color-status-in-transit  #DBEAFE, text #1E40AF
--color-status-picked-up   #D1FAE5, text #065F46
--color-status-delivered   #D1FAE5, text #14532D
--color-status-pending     #FEF3C7, text #92400E
```

---

## 3. Typography

### Font Stack

| Role | Family | Weights | Usage |
|------|---------|---------|-------|
| **Display / Brand** | `Inter` | 700, 800 | "PRAVAH" wordmark, section headings like "Traffic Control Room" |
| **UI Body** | `Inter` | 400, 500, 600 | Nav labels, card subtitles, form fields, table rows |
| **Data / Mono** | `JetBrains Mono` | 400, 600 | Order IDs (#AB045861), metric values (4h 32m, 28/45), PSI scores, ETAs |
| **Hindi Script** | `Noto Sans Devanagari` | 400 | प्रवाह subtitle in sidebar only |

> **Rationale:** Inter's wide optical range lets it handle both tight 11px captions and 36px stat values without swapping families. JetBrains Mono gives data fields the fixed-width alignment and technical authority they deserve — not a style choice, but a function one. Devanagari sub-label cements cultural identity.

### Type Scale

```
--text-xs     11px / 1.4 / 400   ← Timestamps, metadata, axis ticks
--text-sm     12px / 1.5 / 400   ← Table cells, secondary labels
--text-base   13px / 1.6 / 400   ← Body copy, nav items, card descriptions
--text-md     14px / 1.5 / 500   ← Card headers, section labels
--text-lg     16px / 1.4 / 600   ← Panel titles ("TODAY'S SUMMARY")
--text-xl     20px / 1.3 / 700   ← Section page title
--text-2xl    28px / 1.2 / 700   ← Hero stat (e.g. "4h 32m", "12")
--text-3xl    36px / 1.1 / 800   ← (reserved for splash / alerts)

Mono data:
--text-mono-sm   12px / JetBrains Mono 400
--text-mono-md   13px / JetBrains Mono 600
--text-mono-lg   16px / JetBrains Mono 600
--text-mono-xl   24px / JetBrains Mono 700   ← Fuel avg "7.4 L"
```

---

## 4. Spacing & Layout

### Grid

```
Layout type: Fixed sidebar + fluid content area + fixed right rail

Sidebar:        180px fixed
Main content:   flex-1 (min ~600px)
Right rail:     320px fixed
Total minimum:  1100px
```

```
┌──────────────┬────────────────────────────────────────┬──────────────────┐
│  SIDEBAR     │         MAIN CONTENT AREA              │   RIGHT RAIL     │
│  180px       │                                        │   320px          │
│              │  ┌───────────────┐  ┌────────────────┐ │                  │
│  Logo        │  │ TODAY'S        │  │   LIVE MAP     │ │  ACTIVE EVENTS   │
│  ─────────   │  │ SUMMARY        │  │   (full height)│ │  ───────────     │
│  Nav items   │  └───────────────┘  │                │ │  Event cards     │
│              │  ┌───────────────┐  │                │ │                  │
│              │  │ FLEET DIST.   │  │                │ │  CONGESTION      │
│              │  └───────────────┘  │                │ │  HOTSPOTS        │
│              │  ┌───────────────┐  │                │ │                  │
│              │  │ FUEL & COST   │  └────────────────┘ │  Heatmap mini    │
│              │  └───────────────┘                      │                  │
│              │  ┌─────────────────────────────────────┐│                  │
│              │  │             ORDERS TABLE            ││                  │
│              │  └─────────────────────────────────────┘│                  │
│  ─────────   │                                          │                  │
│  System      │                                          │                  │
└──────────────┴────────────────────────────────────────┴──────────────────┘
```

### Spacing Tokens

```
--space-1    4px
--space-2    8px
--space-3    12px
--space-4    16px
--space-5    20px
--space-6    24px
--space-8    32px
--space-10   40px
--space-12   48px
```

### Border Radius

```
--radius-sm    4px    ← Badges, status pills
--radius-md    8px    ← Cards, input fields
--radius-lg    12px   ← Panels, modal containers
--radius-xl    16px   ← Map container, overlay tooltips
--radius-full  9999px ← Circular icons, avatar
```

---

## 5. Component Specifications

### 5.1 Sidebar Navigation

```css
/* Structure */
width: 180px;
background: var(--color-base);
border-right: 1px solid var(--color-border-muted);
padding: 20px 12px;

/* Logo area */
.logo-mark {
  width: 32px; height: 32px;
  background: var(--color-brand-primary);
  border-radius: 8px;
  /* animated green ring — signature pulse on hover */
}

/* Nav item */
.nav-item {
  display: flex; align-items: center; gap: 10px;
  padding: 10px 12px;
  border-radius: var(--radius-md);
  color: var(--color-text-secondary);
  font-size: var(--text-base);
  font-weight: 500;
  transition: background 150ms, color 150ms;
}
.nav-item:hover { background: var(--color-surface-2); color: var(--color-text-primary); }
.nav-item.active {
  background: var(--color-brand-glow);
  color: var(--color-brand-primary);
  border-left: 2px solid var(--color-brand-primary);
}

/* Badge */
.nav-badge {
  margin-left: auto;
  background: var(--color-psi-severe);
  color: white;
  font-size: 10px; font-weight: 700;
  padding: 2px 6px;
  border-radius: var(--radius-full);
}
.nav-badge.new {
  background: var(--color-brand-primary);
}
```

### 5.2 Top Header Bar

```css
.topbar {
  height: 60px;
  background: var(--color-surface-1);
  border-bottom: 1px solid var(--color-border-muted);
  display: flex; align-items: center;
  padding: 0 var(--space-6);
  gap: var(--space-4);
}

/* Location breadcrumb */
.location-title {
  font-size: var(--text-xl);
  font-weight: 700;
  color: var(--color-text-primary);
}
.location-sub {
  font-size: var(--text-sm);
  color: var(--color-text-secondary);
  margin-top: 1px;
}

/* Search */
.search-bar {
  flex: 1; max-width: 480px;
  background: var(--color-surface-3);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  padding: 0 var(--space-4);
  height: 36px;
  color: var(--color-text-primary);
  font-size: var(--text-base);
}
.search-bar::placeholder { color: var(--color-text-tertiary); }

/* Weather widget */
.weather-chip {
  display: flex; align-items: center; gap: var(--space-2);
  padding: 6px 12px;
  background: var(--color-surface-2);
  border-radius: var(--radius-md);
  font-size: var(--text-base);
}

/* Notification bell */
.notif-bell {
  position: relative;
  width: 36px; height: 36px;
  border-radius: var(--radius-full);
  background: var(--color-surface-2);
}
.notif-count {
  position: absolute; top: -4px; right: -4px;
  background: var(--color-psi-severe);
  color: white; font-size: 9px; font-weight: 700;
  width: 16px; height: 16px;
  border-radius: var(--radius-full);
  display: flex; align-items: center; justify-content: center;
}
```

### 5.3 Stat Cards (Today's Summary)

```css
.stat-card {
  background: var(--color-surface-1);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  padding: var(--space-4);
  display: flex; flex-direction: column; gap: var(--space-1);
  transition: border-color 200ms;
}
.stat-card:hover { border-color: var(--color-brand-primary); }

.stat-label {
  font-size: var(--text-xs);
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: var(--color-text-secondary);
}

.stat-value {
  font-family: 'JetBrains Mono', monospace;
  font-size: var(--text-2xl);
  font-weight: 700;
  color: var(--color-text-primary);
  line-height: 1.1;
}

.stat-delta {
  font-size: var(--text-xs);
  font-weight: 500;
  display: flex; align-items: center; gap: 4px;
}
.stat-delta.up   { color: var(--color-psi-low); }     /* green = good */
.stat-delta.warn { color: var(--color-text-warning); } /* amber = watch */
.stat-delta.bad  { color: var(--color-psi-severe); }  /* red = alert */

/* Severity variant — red tint card */
.stat-card.severe {
  border-color: var(--color-psi-severe);
  background: linear-gradient(135deg, var(--color-surface-1), #EF444408);
}

/* Icon dot */
.stat-icon {
  width: 28px; height: 28px;
  border-radius: var(--radius-sm);
  display: flex; align-items: center; justify-content: center;
}
.stat-icon.green  { background: #4ADE8020; color: #4ADE80; }
.stat-icon.amber  { background: #FACC1520; color: #FACC15; }
.stat-icon.red    { background: #EF444420; color: #EF4444; }
.stat-icon.purple { background: #A78BFA20; color: #A78BFA; }
```

### 5.4 PSI Score Badges (Event Cards)

```css
.psi-badge {
  font-family: 'JetBrains Mono', monospace;
  font-size: var(--text-md);
  font-weight: 700;
  width: 40px; height: 28px;
  border-radius: var(--radius-sm);
  display: flex; align-items: center; justify-content: center;
  letter-spacing: -0.02em;
}

.psi-badge[data-level="low"]      { background: var(--color-psi-low-bg);      color: var(--color-psi-low); }
.psi-badge[data-level="moderate"] { background: var(--color-psi-moderate-bg); color: var(--color-psi-moderate); }
.psi-badge[data-level="high"]     { background: var(--color-psi-high-bg);     color: var(--color-psi-high); }
.psi-badge[data-level="severe"]   { background: var(--color-psi-severe-bg);   color: var(--color-psi-severe); }
```

### 5.5 Event List Cards

```css
.event-card {
  display: grid;
  grid-template-columns: 28px 1fr auto;
  align-items: start;
  gap: var(--space-3);
  padding: var(--space-4) 0;
  border-bottom: 1px solid var(--color-border-muted);
  cursor: pointer;
  transition: background 150ms;
}
.event-card:hover { background: var(--color-surface-2); margin: 0 -12px; padding: 12px 12px; border-radius: var(--radius-md); }

.event-type-icon {
  width: 28px; height: 28px;
  border-radius: var(--radius-full);
  display: flex; align-items: center; justify-content: center;
}

.event-name   { font-size: var(--text-md); font-weight: 600; color: var(--color-text-primary); }
.event-road   { font-size: var(--text-sm); color: var(--color-text-secondary); }
.event-loc    { font-size: var(--text-xs); color: var(--color-text-tertiary); }

.event-eta {
  font-family: 'JetBrains Mono', monospace;
  font-size: var(--text-md); font-weight: 600;
  color: var(--color-text-primary);
  text-align: right;
}
.event-eta-range { font-size: var(--text-xs); color: var(--color-text-tertiary); }
```

### 5.6 Fleet Distribution Bars

```css
.fleet-row {
  display: grid;
  grid-template-columns: 80px 30px 1fr 36px;
  align-items: center;
  gap: var(--space-3);
  padding: var(--space-2) 0;
}

.fleet-bar-track {
  height: 4px;
  background: var(--color-surface-3);
  border-radius: var(--radius-full);
  overflow: hidden;
}
.fleet-bar-fill {
  height: 100%;
  background: linear-gradient(90deg, var(--color-brand-primary), #00C89680);
  border-radius: var(--radius-full);
  transition: width 600ms cubic-bezier(.22,1,.36,1);
}

.fleet-pct {
  font-family: 'JetBrains Mono', monospace;
  font-size: var(--text-xs);
  color: var(--color-text-secondary);
  text-align: right;
}
```

### 5.7 Orders Table

```css
.orders-table {
  width: 100%;
  border-collapse: collapse;
}

.orders-table th {
  font-size: var(--text-xs);
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.07em;
  color: var(--color-text-tertiary);
  padding: var(--space-2) var(--space-3);
  border-bottom: 1px solid var(--color-border);
  text-align: left;
}

.orders-table td {
  padding: var(--space-3);
  border-bottom: 1px solid var(--color-border-muted);
  font-size: var(--text-sm);
  color: var(--color-text-primary);
  vertical-align: middle;
}

.orders-table tr:hover td { background: var(--color-surface-2); }

.order-id {
  font-family: 'JetBrains Mono', monospace;
  font-size: var(--text-mono-sm);
  color: var(--color-text-secondary);
}

.route-origin   { color: var(--color-text-primary); font-size: var(--text-sm); }
.route-dest     { color: var(--color-text-tertiary); font-size: var(--text-xs); }

/* Tab filter bar */
.tab-bar {
  display: flex; gap: var(--space-1);
  padding: var(--space-2);
  background: var(--color-surface-2);
  border-radius: var(--radius-md);
}
.tab {
  padding: 5px 14px;
  border-radius: var(--radius-sm);
  font-size: var(--text-sm);
  font-weight: 500;
  color: var(--color-text-secondary);
  cursor: pointer;
  transition: all 150ms;
}
.tab.active {
  background: var(--color-surface-0);
  color: var(--color-text-primary);
  box-shadow: 0 1px 3px rgba(0,0,0,0.3);
}
```

### 5.8 Map Tooltip (Event Popup)

```css
.map-tooltip {
  background: var(--color-surface-2);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  padding: var(--space-4);
  min-width: 200px;
  box-shadow: 0 8px 32px rgba(0,0,0,0.4);
}
.tooltip-id    { font-family: 'JetBrains Mono', monospace; font-size: var(--text-xs); color: var(--color-text-tertiary); }
.tooltip-type  { font-size: var(--text-md); font-weight: 700; color: var(--color-text-primary); margin: 4px 0; }
.tooltip-loc   { font-size: var(--text-sm); color: var(--color-text-secondary); }
.tooltip-badge {
  display: inline-flex; align-items: center;
  padding: 2px 8px;
  border-radius: var(--radius-full);
  font-size: var(--text-xs); font-weight: 700;
}
.tooltip-badge.high { background: var(--color-psi-severe-bg); color: var(--color-psi-severe); }
.tooltip-eta   { font-size: var(--text-xs); color: var(--color-text-tertiary); margin-top: var(--space-2); }
```

### 5.9 Congestion Hotspot List

```css
.hotspot-row {
  display: flex; align-items: center; gap: var(--space-3);
  padding: var(--space-2) 0;
  border-bottom: 1px solid var(--color-border-muted);
}
.hotspot-rank {
  font-family: 'JetBrains Mono', monospace;
  font-size: var(--text-xs);
  color: var(--color-text-tertiary);
  width: 16px; text-align: center;
}
.hotspot-name  { flex: 1; font-size: var(--text-sm); color: var(--color-text-primary); }
.hotspot-level { font-size: var(--text-xs); font-weight: 600; }
.hotspot-level.high   { color: var(--color-psi-severe); }
.hotspot-level.medium { color: var(--color-psi-high); }
.hotspot-dist  { font-family: 'JetBrains Mono', monospace; font-size: var(--text-xs); color: var(--color-text-tertiary); }
```

---

## 6. Map Layer Design

The map uses a **near-black, low-saturation tile style** (Mapbox "Navigation Night" variant or equivalent) with custom layer overrides:

```
Map tile background:   #0A0D12
Road network (local):  #1E2535
Road network (major):  #252D40 / #2B3451
Expressways:           #3D4F70
Water bodies:          #0F1A2E
Labels:                #4D5A77 (district), #8B95B0 (major)
```

**Event markers:**
```
Breakdown / Accident / Severe:   ▲  #EF4444, fill: #EF444420
Waterlogging:                    💧 #3B82F6
Construction:                    ⚠  #F97316
Unit (vehicle) marker:           🚗 #00C896 circle, stroke #0A0D12
```

**Routes:**
```
Active corridor:    stroke: #00C896,  width: 3px, opacity: 0.8
Congested corridor: stroke: #EF4444, width: 4px, opacity: 0.6, dash: [8,4]
Clear corridor:     stroke: #4ADE80,  width: 2px, opacity: 0.4
```

**Heatmap (Congestion panel minimap):**
```
cold → warm:  #3B82F6 → #FACC15 → #EF4444
opacity: 0.7
radius: 30px at zoom level
```

---

## 7. Motion & Interaction

```
Transition easing:   cubic-bezier(0.22, 1, 0.36, 1)  ← "smooth brake"
Card hover:          150ms background, border
Sidebar expand:      250ms width
Stat value count-up: 600ms on load (count from 0 to final value)
Progress bar fill:   600ms on load, staggered by 80ms each row
Map marker pulse:    2s infinite scale(1)→scale(1.3)→scale(1), active events only
Tooltip appear:      150ms fade + 4px translateY
Alert badge shake:   400ms on new event (keyframes: rotate ±5deg x3)
PSI score flash:     300ms background blink when severity escalates
```

---

## 8. Dark / Light Theme Toggle

Implement via CSS `data-theme` attribute on `<html>`:

```css
/* Default: dark */
:root {
  --color-base: #0A0D12;
  --color-surface-0: #10141C;
  /* ... all tokens above ... */
}

/* Light theme override */
[data-theme="light"] {
  --color-base: #F0F2F8;
  --color-surface-0: #FFFFFF;
  /* ... light tokens above ... */
}
```

**Toggle button placement:** Top-right of the header bar, between notifications and user avatar. Use a sun/moon icon with a 200ms crossfade transition.

```css
.theme-toggle {
  width: 36px; height: 36px;
  border-radius: var(--radius-full);
  background: var(--color-surface-2);
  border: 1px solid var(--color-border);
  cursor: pointer;
  transition: background 200ms, color 200ms;
  display: flex; align-items: center; justify-content: center;
}
```

**Map tile theme:** Swap between dark tileset and a light "Mapbox Navigation Day" or equivalent on theme change.

---

## 9. Responsive Breakpoints

```
≥ 1440px:   Full 3-column layout (sidebar + map + rail)
1200–1440:  Collapse right rail into a slide-over drawer
1024–1200:  Sidebar icon-only mode (48px), map takes more space
< 1024:     Stack to single column, map becomes full-screen modal
< 768:      Mobile: bottom tab nav replaces sidebar
```

---

## 10. Alternative UI Prompt Directions

Below are three distinct aesthetic directions that could re-imagine PRAVAH beyond the current dark control-room look:

---

### Direction A — "Glassmorphic Command" (Futuristic)

**Prompt:**
> *Design a traffic dashboard using glassmorphism: translucent frosted-glass panels over a deep navy-to-indigo gradient base (#050A1F → #1A0A3C). All cards use `backdrop-filter: blur(20px)`, white borders at 8% opacity, and `background: rgba(255,255,255,0.06)`. Accent with electric violet (#8B5CF6) and cyan (#06B6D4). Event severity uses a neon-glow text-shadow. The map bleeds edge-to-edge with no card border. Typography: `Space Grotesk` for data, `Syne` for headings.*

```
Palette:
  Base:        #050A1F
  Glass:       rgba(255,255,255,0.06) + blur(20px)
  Accent 1:    #8B5CF6  ← Violet
  Accent 2:    #06B6D4  ← Cyan
  Severe:      #FF3D71 + glow
  Safe:        #00FFA3 + glow
```

---

### Direction B — "Warm Ops" (Human-centered)

**Prompt:**
> *Design PRAVAH as a warm, approachable dashboard for non-technical city officers. Use a cream-white background (#FAF8F4), warm slate panels (#F1EFE9), and ink-black text (#1A1714). Replace cold teals with saffron-amber (#F59E0B) as the brand accent and terracotta-orange (#C2410C) for severe alerts. Typography: `Merriweather` for headings, `Source Sans 3` for body. Cards have soft drop shadows, no hard borders. The map uses a warm sepia tile style. The dashboard feels like a newspaper command post, not a spaceship.*

```
Palette:
  Base:        #FAF8F4
  Panel:       #F1EFE9
  Ink:         #1A1714
  Accent:      #F59E0B  ← Saffron
  Severe:      #C2410C  ← Terracotta
  Safe:        #16A34A
  Shadow:      rgba(26,23,20,0.08)
```

---

### Direction C — "Brutalist Data Wall" (High-density)

**Prompt:**
> *Design PRAVAH as a high-density brutalist data wall: pure #000000 background, white text, zero border-radius, 1px solid white borders at 20% opacity for all cards. No gradients, no shadows. Use a strict 12-column grid with hairline rules. The only color is function-critical: #FF0000 for severe, #FFAA00 for high, #00FF88 for clear. Typography: monospace throughout — `IBM Plex Mono` for everything. Numbers are large and bold. Section dividers are full-width horizontal rules with a section counter (01 / 02 / 03) in 10px mono. The map uses an OpenStreetMap grayscale tile with no decorative layers.*

```
Palette:
  Base:     #000000
  Surface:  #0A0A0A
  Border:   rgba(255,255,255,0.2)
  Text:     #FFFFFF
  Severe:   #FF0000
  High:     #FFAA00
  Clear:    #00FF88
  All mono: IBM Plex Mono
```

---

## 11. Accessibility Checklist

- [ ] All text meets **WCAG AA** contrast (≥4.5:1 for body, ≥3:1 for large text)
- [ ] PSI severity never communicated by color alone — always paired with icon + label
- [ ] All interactive elements have visible `:focus-visible` ring (`2px solid var(--color-brand-primary), offset 2px`)
- [ ] Map event markers have `aria-label` with event type, road, and severity
- [ ] `prefers-reduced-motion` disables all animations, count-ups, and marker pulses
- [ ] `prefers-color-scheme: light` auto-sets light theme unless user has overridden
- [ ] Font sizes never below 11px; data mono values maintain adequate tracking

---

## 12. Icon System

Use **Lucide Icons** (consistent stroke-based, 1.5px stroke weight, 20×20 or 16×16 grid):

```
Overview        → LayoutDashboard
Live Map        → Map
Events          → AlertTriangle
Triage (NLP)    → BrainCircuit
Predictions     → TrendingUp
Hotspots        → Flame
Dispatch        → Navigation
Units           → Truck
What-if         → FlaskConical
Alerts          → Bell
Analytics       → BarChart2
Reports         → FileText
Settings        → Settings

Event types:
Breakdown       → WrenchIcon / AlertTriangle (red)
Waterlogging    → Droplets (blue)
Accident        → AlertOctagon (red)
Construction    → HardHat (orange)
Rally           → Users (red)
```

---

## 13. Routing & Authentication Architecture

- **Framework:** TanStack Router (`@tanstack/react-router`)
- **Protected Routes:** All dashboard pages are strictly protected. The `RootComponent` in `__root.tsx` actively monitors the Supabase session via `supabase.auth.getSession()` and `onAuthStateChange`.
- **Redirect Logic:**
  - Unauthenticated users attempting to access the app are force-redirected to `/login`.
  - Authenticated users on the `/login` page are automatically routed back to `/` (Dashboard).
- **Authentication Provider:** Supabase Auth (Email/Password & Google OAuth).
- **Theme Initialization:** The root HTML node is explicitly initialized with `data-theme="light"` via the `RootShell` component to enforce the Light Theme by default on the first load, bypassing the dark theme fallback.

---

## 14. Implemented Views & Components

- **Dashboard (`/`)**: Main hub featuring `LiveMap`, `SidePanels` (Today's Summary, Fleet Dist, Fuel Cost), and the global `TopBar`.
- **Login (`/login`)**: Custom-built, pixel-perfect authentication screen. Features a complex, responsive SVG `clip-path` banner with smooth bezier curves (`objectBoundingBox`), creating a high-end tech aesthetic with custom cutouts. Integrates Supabase Email and Google Auth.
- **Analytics (`/analytics`)**: Detailed metrics page implementing custom SVG charting including stepped-area traffic volume trends and stacked rounded-bar incident distribution charts to seamlessly match the design language.
- **Events (`/events`)**: Data-dense full-screen list view of active incidents and logs.
- **Reports (`/reports`)**: Clean, grid-based file manager UI for executive briefings.
- **Support (`/support`)**: Help Center UI with a global search bar and live API status board.
- **Responsive Layout Architecture:** Dynamic width recalculation using `ResizeObserver` attached to map containers. This ensures Mapbox seamlessly re-renders and fills the void space whenever the left sidebar dynamically collapses or expands.

---

*PRAVAH Design System v1.0 · June 2026 · Team PRAVAH*
