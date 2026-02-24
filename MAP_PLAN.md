# Map View — Design Plan

## Vision

The map isn't just "pins on a map." It's a **geographic dimension of Time Slices** — you watch ideas migrate across the world. Baghdad → Al-Andalus → Florence → Paris → Vienna. Threads become visible **spatially**: you can see the "Death of God" thread arc from Paris to Turin to Weimar.

When a thread is active, the map draws animated arcs between connected locations, matching the existing thread system in the timeline view.

## Architecture

### Approach: Integrated Map Panel (not a separate page)

A **toggle button** in the header switches between Timeline view and Map view — or ideally, a **split view** where the map lives as a collapsible panel alongside the timeline. But given our 4 entries, let's start with a **full-screen map mode toggle**.

### Library: Leaflet.js

- Lightweight (~40kb), no API key, free tiles
- Dark tile provider: CartoDB Dark Matter (free, matches our aesthetic)
- Custom markers styled with our CSS variables
- Animated SVG arcs for thread connections

### Data Changes

Add `location` to each slice in `slices.json` / `slices.it.json`:

```json
{
  "year": "762",
  "location": {
    "lat": 33.3152,
    "lon": 44.3661,
    "place": "Baghdad"
  },
  ...
}
```

Place name is for display — lat/lon for positioning.

### Map Features

#### Base
- Dark tile layer (CartoDB Dark Matter) — matches our `--bg: #0a0a0f` aesthetic
- Custom circular markers using entry accent color
- Marker size reflects... nothing special, keep them uniform
- On hover: show year + title tooltip
- On click: expand a popup with teaser + link to scroll to that entry in the timeline

#### Time Slider (the wow factor)
- A horizontal slider at the bottom of the map
- Dragging it scrubs through time (min year to max year of all entries)
- Entries **fade in** as the slider reaches their year
- A subtle animated pulse when an entry "appears"
- Current year displayed prominently
- Optional: auto-play button that slowly advances through time

#### Thread Integration (key differentiator)
- When a thread is activated (from either view), the map draws **animated arcs** between connected entries
- Arcs use the same glow/accent color as the timeline SVG lines
- Thread banner appears on map too
- Clicking a thread tag on a map popup activates that thread
- Entries not in the active thread fade to very low opacity on the map

#### Animated Arcs
- Use Leaflet's SVG layer or a custom canvas overlay
- Arcs curve slightly (great-circle style) between locations
- Animate with dash-offset (same technique as timeline SVG thread lines)
- Staggered animation: first arc draws, then second, etc.

#### View Transitions
- Toggle button in header: 🗺️ / 📜 icons
- Smooth CSS transition between views
- Map preserves state (zoom, active thread) when toggling
- Active thread syncs between timeline and map views

### Visual Design

#### Markers
```
┌──────────────┐
│   ⬤ 762      │  ← Glowing dot + year
│   Baghdad    │  ← Place name below
└──────────────┘
```

Custom divIcon with our accent color, pulsing glow animation matching `--accent`.

#### Popups
Styled to match our card aesthetic:
- Dark background (`--surface`)
- Border with `--accent`
- Shows: year, title, teaser, thread tags
- "View in timeline →" link

#### Thread Arcs
- Curved SVG paths between locations
- Color: `rgba(124,111,247,0.5)` with glow filter
- Animated stroke-dashoffset reveal
- Small directional arrow or year label at midpoint

### Mobile
- Map takes full viewport width
- No split view on mobile — pure toggle between map and timeline
- Simplified markers (no labels, just dots)
- Tap to open popup
- Time slider still works but simplified

### Implementation Order

1. **Data**: Add `location` to all 4 entries in both JSON files
2. **Map skeleton**: Leaflet + dark tiles + basic markers
3. **Styling**: Custom markers, popups matching our design system
4. **Toggle**: Header button to switch views, state sync
5. **Time slider**: Scrubbing through entries with fade-in
6. **Thread arcs**: Animated connections on thread activation
7. **Polish**: Transitions, mobile, edge cases

### Dependencies
- Leaflet.js (CDN: `unpkg.com/leaflet@1.9.4`)
- CartoDB Dark Matter tiles (free, no API key)
- No build step — stays as a single HTML file

### Locations for Current Entries

| Year | Place | Lat | Lon |
|------|-------|-----|-----|
| 762 | Baghdad | 33.3152 | 44.3661 |
| 1504 | Florence | 43.7696 | 11.2558 |
| 1889 | Paris | 48.8566 | 2.3522 |
| 1922 | Weimar/Europe | 50.9795 | 11.3235 |

Note: 1922 is tricky — it's pan-European. Use Weimar (Bauhaus HQ) as the pin, but the popup should note the broader geography.

---

*Written: 2026-02-24*
