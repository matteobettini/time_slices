# Time Clock Navigator — Design Spec

## Core Concept
A semicircle arc along the screen edge that acts like a clock face — entries are positioned as "hour lines" radiating from the clock's center. Drag or tap to rotate and navigate through time.

## Visual Design

### Shape & Position
- **Desktop**: Left edge, semicircle curves into the screen (clock faces right)
- **Mobile**: Right edge, semicircle curves into the screen (clock faces left)
- Radius: ~40% of viewport height (responsive)
- The "center" of the clock sits just off-screen at the edge

### Entry Hour Lines
- Each entry is a radial line emanating from the center, like hour markers on a clock
- Lines positioned proportionally by year around the arc (earliest at top, latest at bottom)
- Line style: `var(--accent)` purple (#7c6ff7), 2-3px width, subtle glow
- Line length: ~20px default, extends to ~30px on hover/current
- Year label sits at the outer end of each line (e.g., "762", "1347", "1922")
- Labels use `var(--mono)` font, small size (~0.65rem)

### Current Position Indicator
- The "current" entry's line is longer, brighter, with stronger glow
- Optional: a subtle arc segment or "hand" connecting center to current line
- Smooth animation as scroll position changes

### States
1. **Idle**: Dimmed (20-30% opacity), lines barely visible, no labels
2. **Hover/Active**: Full opacity, all lines visible, year labels fade in
3. **Dragging**: Current indicator follows finger/cursor, haptic feedback when passing each line

## Interaction

### Drag to Navigate
- Touch/click and drag along the arc
- Position snaps to nearest entry line with haptic feedback (10ms vibration)
- Smooth scroll animation to selected entry

### Tap Lines
- Direct tap on a line or its label jumps to that entry
- Subtle pulse animation on the line

### Scroll Sync
- As page scrolls, the current indicator moves to reflect position
- Passive sync (doesn't interfere with normal scrolling)

## Styling (matching Time Slices aesthetic)
- Arc outline: thin stroke in `var(--border)` or subtle gradient
- Hour lines: `var(--accent)` (#7c6ff7) with glow
- Current line: brighter, longer, animated glow pulse
- Year labels: `var(--mono)`, `var(--text-dim)` color, fade in on hover
- Background: optional subtle radial gradient from center
- Transitions: 200-300ms ease for all state changes

## Technical Approach
- SVG container for the semicircle and all lines (scalable, easy arc math)
- Each entry = one `<line>` element radiating from center
- CSS for transitions, hover states, glow effects
- JavaScript for:
  - Building clock from SLICES data after load
  - Calculating line angles from year values
  - Scroll position tracking (IntersectionObserver or scroll events)
  - Drag interaction (pointer events)
  - Haptic feedback via `navigator.vibrate()`
  - Rebuilding on language switch

## Thread Mode
- When a thread is active, only show lines for entries in that thread
- Arc spans only the thread's year range
- Rebuild on `activateThread()` / `clearThread()`

## Map Mode
- Hide the clock entirely when map view is active

## Integration Points
Look at existing code for:
- `slicesReady` promise (wait for data before building clock)
- `loadSlices()` - rebuild clock after language switch
- `activateThread()` / `clearThread()` - rebuild for thread filtering
- `showMapView()` / `showTimelineView()` - hide/show clock
- `highlightAndScroll()` - use this when user taps a clock line

## Files
All code goes in index.html (CSS in the `<style>` block, JS at the end of the `<script>` block).
