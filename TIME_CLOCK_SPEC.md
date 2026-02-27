# Time Clock Navigator — Design Spec

## Core Concept
A **rotatable disc** partially visible at the screen edge. The disc contains all entry markers — when you drag anywhere on the disc, it rotates, and the entries spin with it. The only fixed element is a **current position indicator** (like a needle) that stays in the middle of the visible arc, pointing at whatever entry is currently "selected."

Think of it like a vinyl record or a combination lock — you rotate the disc to bring different entries to the needle.

## Visual Design

### The Disc
- **Shape**: Solid filled semicircle (not just an arc outline)
- **Color**: `var(--surface)` or slightly darker, with subtle gradient
- **Position**: Mostly off-screen, only ~60-80px of the edge visible
  - **Desktop**: Left edge
  - **Mobile**: Right edge
- **Size**: Small footprint — disc radius large enough that the visible slice shows ~60-80px
- The disc should feel **physical** — a solid surface you can grab and rotate

### Entry Markers (on the disc)
- Hour lines radiating from center, positioned by year around the full semicircle
- Lines are **part of the disc** — they rotate with it when dragged
- Line style: `var(--accent)` purple, 2px width, subtle glow
- Year labels at outer end of each line, small `var(--mono)` font
- Labels rotate with the disc (they're painted on it)

### Current Position Indicator (fixed)
- A **stationary needle/marker** at the vertical center of the visible arc
- Points inward toward the disc center
- Brighter, with strong glow — clearly indicates "this is where you are"
- **Does not move** — the disc rotates behind it
- When scrolling the page, the disc rotates so the current entry aligns with this needle

### States
1. **Idle**: Visible but subtle — low glow, ~50-60% opacity
2. **Hover/Active**: Brighter, stronger glow, feels "grabbable"
3. **Dragging**: Full brightness, disc rotates smoothly following finger/cursor

## Interaction

### Drag to Rotate
- Touch/click **anywhere on the visible disc** and drag
- The entire disc rotates — entries spin past the fixed needle
- Haptic feedback (10ms vibration) when an entry passes the needle
- Release to select — smooth scroll to whichever entry is at the needle

### Momentum (optional)
- Flick gesture could give the disc momentum, letting it spin and gradually stop
- Entries tick past the needle with haptic feedback as it slows

### Scroll Sync
- As page scrolls, the disc rotates so the current entry stays at the needle
- Passive — doesn't fight with scrolling, just keeps in sync

### Tap Entry
- Tapping directly on a visible entry line/label rotates disc to bring it to needle, then scrolls

## Styling

- Disc fill: `var(--surface)` with radial gradient (darker at center)
- Disc edge: subtle `var(--border)` stroke or shadow
- Entry lines: `var(--accent)` with `drop-shadow` glow
- Needle: Bright `var(--accent)`, animated glow pulse
- On interaction: disc slightly enlarges (scale 1.05), glow intensifies
- Transitions: 200ms ease for scale/glow, rotation can be faster

## Technical Approach

### Structure
```
<div class="time-disc-container">        <!-- Fixed position container -->
  <div class="time-disc" rotate(Xdeg)>   <!-- Rotates via CSS transform -->
    <svg>                                 <!-- Disc face + entry lines -->
      <circle fill="..."/>               <!-- Solid disc background -->
      <line for each entry/>             <!-- Entry markers -->
      <text for each entry/>             <!-- Year labels -->
    </svg>
  </div>
  <div class="time-needle"/>             <!-- Fixed indicator, doesn't rotate -->
</div>
```

### Rotation Math
- Total rotation range: 180° (semicircle)
- Map year range to angle: `angle = ((year - minYear) / (maxYear - minYear)) * 180`
- Current scroll position → calculate which entry → rotate disc so that entry is at 90° (middle)

### Drag Handling
- On drag start: record initial angle and pointer position
- On drag move: calculate angle delta from pointer movement, apply to disc rotation
- On drag end: find nearest entry to needle, snap rotation, trigger scroll

## Mobile
- **Must work on mobile** — touch drag is primary interaction
- Right edge positioning on mobile (left edge on desktop)
- Larger touch target — the whole visible disc surface is draggable
- Touch events: `touchstart`, `touchmove`, `touchend` with `passive: false` for `touchmove`

## Thread Mode
- Only show entries in active thread on the disc
- Recalculate year range and positions
- Rebuild on `activateThread()` / `clearThread()`

## Map Mode
- Hide the disc when map view is active

## Integration Points
- `slicesReady` — build disc after data loads
- `loadSlices()` — rebuild on language switch
- `activateThread()` / `clearThread()` — rebuild for thread filter
- `showMapView()` / `showTimelineView()` — hide/show disc
- `highlightAndScroll()` — use when entry is selected

## Files
All code in index.html (CSS in `<style>`, JS at end of `<script>`).
