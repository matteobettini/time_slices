/**
 * Time Disc Navigator
 * 
 * Simple bar with ticks that follow actual DOM positions.
 * Drag to scroll, snaps to entries.
 */

(function() {
  'use strict';

  const container = document.getElementById('timeDiscContainer');
  const disc = document.getElementById('timeDisc');
  const svg = document.getElementById('timeDiscSvg');
  const yearDisplay = document.getElementById('timeDiscYear');

  if (!container || !disc || !svg) return;

  let entries = [];
  let isDragging = false;
  let dragStartY = 0;

  const BAR_WIDTH = 60;
  const TICK_LENGTH = 14;

  function build() {
    if (!window.SLICES || !window.SLICES.length) return;

    const slices = window.activeThread
      ? window.SLICES.filter(s => (s.threads || []).includes(window.activeThread))
      : window.SLICES;

    if (!slices.length) {
      entries = [];
      svg.innerHTML = '';
      return;
    }

    const sorted = [...slices].sort((a, b) => parseInt(a.year) - parseInt(b.year));
    
    entries = sorted.map(slice => ({
      year: parseInt(slice.year),
      slice,
      el: document.querySelector(`#entry-${slice.id}`)
    }));

    render();
  }

  function render() {
    const h = window.innerHeight;
    const centerY = h / 2;
    
    svg.setAttribute('width', BAR_WIDTH);
    svg.setAttribute('height', h);
    svg.setAttribute('viewBox', `0 0 ${BAR_WIDTH} ${h}`);

    let content = '';

    // Fading background with glow - fades left to right and at top/bottom edges
    content += `<defs>
      <linearGradient id="barFadeH" x1="0%" y1="0%" x2="100%" y2="0%">
        <stop offset="0%" style="stop-color:#0a0a0f;stop-opacity:0.95"/>
        <stop offset="60%" style="stop-color:#0a0a0f;stop-opacity:0.5"/>
        <stop offset="100%" style="stop-color:#0a0a0f;stop-opacity:0"/>
      </linearGradient>
      <linearGradient id="barFadeV" x1="0%" y1="0%" x2="0%" y2="100%">
        <stop offset="0%" style="stop-color:#0a0a0f;stop-opacity:1"/>
        <stop offset="15%" style="stop-color:#0a0a0f;stop-opacity:0"/>
        <stop offset="85%" style="stop-color:#0a0a0f;stop-opacity:0"/>
        <stop offset="100%" style="stop-color:#0a0a0f;stop-opacity:1"/>
      </linearGradient>
      <linearGradient id="glowFade" x1="0%" y1="0%" x2="100%" y2="0%">
        <stop offset="0%" style="stop-color:var(--accent);stop-opacity:0.15"/>
        <stop offset="100%" style="stop-color:var(--accent);stop-opacity:0"/>
      </linearGradient>
    </defs>`;
    // Glow layer (behind everything)
    content += `<rect class="disc-glow" x="0" y="0" width="${BAR_WIDTH + 20}" height="${h}" fill="url(#glowFade)" />`;
    // Main background fade
    content += `<rect class="disc-bg" x="0" y="0" width="${BAR_WIDTH + 30}" height="${h}" fill="url(#barFadeH)" />`;
    // Top/bottom fade
    content += `<rect class="disc-bg-edge" x="0" y="0" width="${BAR_WIDTH + 30}" height="${h}" fill="url(#barFadeV)" />`;

    // Find min/max years for proportional spacing
    const minYear = entries.length > 0 ? entries[0].year : 0;
    const maxYear = entries.length > 0 ? entries[entries.length - 1].year : 1;
    const yearSpan = maxYear - minYear || 1;

    // Calculate scroll position as ratio
    const maxScroll = document.documentElement.scrollHeight - window.innerHeight;
    const scrollRatio = maxScroll > 0 ? window.scrollY / maxScroll : 0;

    // The "track" of all ticks is compressed to show more at once
    // trackScale < 1 means ticks are closer together (more visible)
    const trackScale = 0.4; // Show ~40% of timeline height = more ticks visible
    const trackHeight = h * trackScale;
    
    // Track offset moves as we scroll - maps scroll to track position
    const trackOffset = centerY - (scrollRatio * trackHeight);

    // Find current entry - closest tick to center needle
    let currentEntry = null;
    let currentDist = Infinity;
    
    entries.forEach(e => {
      const yearRatio = (e.year - minYear) / yearSpan;
      const tickY = trackOffset + (yearRatio * trackHeight);
      const dist = Math.abs(tickY - centerY);
      if (dist < currentDist) {
        currentDist = dist;
        currentEntry = e;
      }
    });

    // Draw ticks - positioned by year scale
    entries.forEach(e => {
      if (!e.el) return;
      
      const yearRatio = (e.year - minYear) / yearSpan;
      const tickY = trackOffset + (yearRatio * trackHeight);
      
      // Skip if off screen
      if (tickY < -30 || tickY > h + 30) return;
      
      // Ticks at left edge, labels to the right
      const x1 = 0;
      const x2 = TICK_LENGTH;
      const labelX = x2 + 4;
      
      const isCurrent = e === currentEntry;
      const tickClass = isCurrent ? 'disc-tick current' : 'disc-tick';

      content += `<line class="${tickClass}" data-id="${e.slice.id}" data-year="${e.year}" x1="${x1}" y1="${tickY}" x2="${x2}" y2="${tickY}" />`;

      // Year label  
      const yearText = typeof window.formatYear === 'function' ? window.formatYear(e.year) : e.year;
      const labelClass = isCurrent ? 'disc-label current' : 'disc-label';
      content += `<text class="${labelClass}" x="${labelX}" y="${tickY + 4}" text-anchor="start">${yearText}</text>`;
    });

    // Needle at center (fixed)
    content += `<line class="disc-needle" x1="0" y1="${centerY}" x2="${BAR_WIDTH}" y2="${centerY}" />`;

    // Update year display with current entry
    if (currentEntry && yearDisplay) {
      yearDisplay.textContent = typeof window.formatYear === 'function' ? window.formatYear(currentEntry.year) : currentEntry.year;
    }

    svg.innerHTML = content;
  }

  function snapToClosestEntry() {
    if (!entries.length) return;
    
    const h = window.innerHeight;
    const centerY = h / 2;
    const minYear = entries[0].year;
    const maxYear = entries[entries.length - 1].year;
    const yearSpan = maxYear - minYear || 1;
    const maxScroll = document.documentElement.scrollHeight - window.innerHeight;
    const scrollRatio = maxScroll > 0 ? window.scrollY / maxScroll : 0;
    const trackScale = 0.4;
    const trackHeight = h * trackScale;
    const trackOffset = centerY - (scrollRatio * trackHeight);
    
    // Find entry whose tick is closest to needle
    let closest = null;
    let closestDist = Infinity;
    
    entries.forEach(e => {
      const yearRatio = (e.year - minYear) / yearSpan;
      const tickY = trackOffset + (yearRatio * trackHeight);
      const dist = Math.abs(tickY - centerY);
      if (dist < closestDist) {
        closestDist = dist;
        closest = e;
      }
    });
    
    if (closest && closest.el) {
      // Scroll to center this entry in viewport
      const rect = closest.el.getBoundingClientRect();
      const elCenter = rect.top + rect.height / 2;
      const scrollDelta = elCenter - centerY;
      
      window.scrollBy({ top: scrollDelta, behavior: 'smooth' });
      
      if (navigator.vibrate) navigator.vibrate(10);
    }
  }

  function initDrag() {
    function onStart(e) {
      isDragging = true;
      container.classList.add('active');
      const clientY = e.touches ? e.touches[0].clientY : e.clientY;
      dragStartY = clientY;
      e.preventDefault();
    }

    function onMove(e) {
      if (!isDragging) return;
      e.preventDefault();
      
      if (!entries.length) return;
      
      const clientY = e.touches ? e.touches[0].clientY : e.clientY;
      const h = window.innerHeight;
      const centerY = h / 2;
      
      // Find which entry's tick would be at the drag position
      const minYear = entries[0].year;
      const maxYear = entries[entries.length - 1].year;
      const yearSpan = maxYear - minYear || 1;
      const trackScale = 0.4;
      const trackHeight = h * trackScale;
      
      // Dragging moves the track - find which entry is now at needle
      // Current track offset based on current scroll
      const maxScroll = document.documentElement.scrollHeight - window.innerHeight;
      const scrollRatio = maxScroll > 0 ? window.scrollY / maxScroll : 0;
      const currentTrackOffset = centerY - (scrollRatio * trackHeight);
      
      // How much did we drag?
      const dragDelta = dragStartY - clientY;
      
      // New track offset if we moved by dragDelta
      const newTrackOffset = currentTrackOffset + dragDelta;
      
      // Find entry whose tick would be at centerY with this new offset
      let targetEntry = null;
      let closestDist = Infinity;
      
      entries.forEach(e => {
        const yearRatio = (e.year - minYear) / yearSpan;
        const tickY = newTrackOffset + (yearRatio * trackHeight);
        const dist = Math.abs(tickY - centerY);
        if (dist < closestDist) {
          closestDist = dist;
          targetEntry = e;
        }
      });
      
      // Scroll to center that entry
      if (targetEntry && targetEntry.el) {
        const rect = targetEntry.el.getBoundingClientRect();
        const elCenter = rect.top + rect.height / 2;
        const scrollDelta = elCenter - centerY;
        window.scrollBy({ top: scrollDelta, behavior: 'auto' });
      }
      
      // Update drag start for continuous dragging
      dragStartY = clientY;
      
      render();
    }

    function onEnd() {
      if (!isDragging) return;
      isDragging = false;
      container.classList.remove('active');
      snapToClosestEntry();
    }

    container.addEventListener('mousedown', onStart);
    document.addEventListener('mousemove', onMove);
    document.addEventListener('mouseup', onEnd);
    container.addEventListener('touchstart', onStart, { passive: false });
    document.addEventListener('touchmove', onMove, { passive: false });
    document.addEventListener('touchend', onEnd);

    svg.addEventListener('click', (e) => {
      if (isDragging) return;
      const tick = e.target.closest('.disc-tick');
      if (tick) {
        const el = document.querySelector(`#entry-${tick.dataset.id}`);
        if (el) {
          if (navigator.vibrate) navigator.vibrate(10);
          if (typeof window.highlightAndScroll === 'function') {
            window.highlightAndScroll(el);
          } else {
            el.scrollIntoView({ behavior: 'smooth', block: 'center' });
          }
        }
      }
    });
  }

  let scrollTimer = null;
  window.addEventListener('scroll', () => {
    if (scrollTimer) return;
    scrollTimer = requestAnimationFrame(() => {
      scrollTimer = null;
      if (!container.classList.contains('hidden')) render();
    });
  }, { passive: true });

  let resizeTimer = null;
  window.addEventListener('resize', () => {
    clearTimeout(resizeTimer);
    resizeTimer = setTimeout(build, 200);
  });

  window.buildTimeDisc = build;
  window.showTimeDisc = () => container.classList.remove('hidden');
  window.hideTimeDisc = () => container.classList.add('hidden');

  initDrag();
  if (window.SLICES && window.SLICES.length) build();

})();
