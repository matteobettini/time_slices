/**
 * Time Disc Navigator
 * 
 * Fixed needle in center. Ticks move past it as you scroll.
 * Ticks spaced by year. Dragging maps year to entry.
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

  const BAR_WIDTH = 60;
  const TICK_LENGTH = 14;
  const TRACK_SCALE = 0.5; // Ticks span 50% of viewport height

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
    
    entries = sorted.map((slice, index) => ({
      year: parseInt(slice.year),
      slice,
      index,
      el: document.querySelector(`#entry-${slice.id}`)
    }));

    render();
  }

  // Find which entry is currently at viewport center
  function findCurrentEntry() {
    const centerY = window.innerHeight / 2;
    let closest = null;
    let closestDist = Infinity;
    entries.forEach(e => {
      if (!e.el) return;
      const rect = e.el.getBoundingClientRect();
      const dist = Math.abs(rect.top + rect.height / 2 - centerY);
      if (dist < closestDist) {
        closestDist = dist;
        closest = e;
      }
    });
    return closest;
  }

  // Get scroll progress (0 to 1)
  function getScrollProgress() {
    const maxScroll = document.documentElement.scrollHeight - window.innerHeight;
    return maxScroll > 0 ? window.scrollY / maxScroll : 0;
  }

  function render() {
    const h = window.innerHeight;
    const centerY = h / 2;
    
    svg.setAttribute('width', BAR_WIDTH);
    svg.setAttribute('height', h);
    svg.setAttribute('viewBox', `0 0 ${BAR_WIDTH} ${h}`);

    if (!entries.length) return;

    const minYear = entries[0].year;
    const maxYear = entries[entries.length - 1].year;
    const yearSpan = maxYear - minYear || 1;

    let content = '';

    // Background
    content += `<defs>
      <linearGradient id="barFadeH" x1="0%" y1="0%" x2="100%" y2="0%">
        <stop offset="0%" style="stop-color:#1a1a1a;stop-opacity:0.8"/>
        <stop offset="50%" style="stop-color:#1a1a1a;stop-opacity:0.4"/>
        <stop offset="100%" style="stop-color:#1a1a1a;stop-opacity:0"/>
      </linearGradient>
      <linearGradient id="glowFade" x1="0%" y1="0%" x2="100%" y2="0%">
        <stop offset="0%" style="stop-color:#888888;stop-opacity:0.2"/>
        <stop offset="100%" style="stop-color:#888888;stop-opacity:0"/>
      </linearGradient>
    </defs>`;
    content += `<rect class="disc-glow" x="0" y="0" width="${BAR_WIDTH}" height="${h}" fill="url(#glowFade)" />`;
    content += `<rect class="disc-bg" x="0" y="0" width="${BAR_WIDTH + 20}" height="${h}" fill="url(#barFadeH)" />`;

    // Current entry at viewport center
    const currentEntry = findCurrentEntry();
    const currentYearRatio = currentEntry ? (currentEntry.year - minYear) / yearSpan : 0;

    // Track height and offset
    // Ticks are positioned by year, track moves so current entry's tick is at center
    const trackHeight = h * TRACK_SCALE;
    const trackOffset = centerY - (currentYearRatio * trackHeight);

    // Draw ticks
    entries.forEach(e => {
      const yearRatio = (e.year - minYear) / yearSpan;
      const tickY = trackOffset + yearRatio * trackHeight;
      
      // Skip if off screen
      if (tickY < -30 || tickY > h + 30) return;
      
      const x1 = 0;
      const x2 = TICK_LENGTH;
      const labelX = x2 + 4;
      
      const isCurrent = e === currentEntry;
      const tickClass = isCurrent ? 'disc-tick current' : 'disc-tick';

      content += `<line class="${tickClass}" data-id="${e.slice.id}" data-year="${e.year}" data-index="${e.index}" x1="${x1}" y1="${tickY}" x2="${x2}" y2="${tickY}" />`;

      const yearText = typeof window.formatYear === 'function' ? window.formatYear(e.year) : e.year;
      const labelClass = isCurrent ? 'disc-label current' : 'disc-label';
      content += `<text class="${labelClass}" x="${labelX}" y="${tickY + 4}" text-anchor="start">${yearText}</text>`;
    });

    // Fixed needle at center
    content += `<line class="disc-needle" x1="0" y1="${centerY}" x2="${BAR_WIDTH}" y2="${centerY}" />`;

    // Update year display
    if (currentEntry && yearDisplay) {
      yearDisplay.textContent = typeof window.formatYear === 'function' ? window.formatYear(currentEntry.year) : currentEntry.year;
    }

    svg.innerHTML = content;
  }

  // Find entry by Y position on bar (accounting for current track position)
  function findEntryAtBarY(clientY) {
    if (!entries.length) return null;
    
    const h = window.innerHeight;
    const centerY = h / 2;
    const minYear = entries[0].year;
    const maxYear = entries[entries.length - 1].year;
    const yearSpan = maxYear - minYear || 1;
    
    const currentEntry = findCurrentEntry();
    const currentYearRatio = currentEntry ? (currentEntry.year - minYear) / yearSpan : 0;
    const trackHeight = h * TRACK_SCALE;
    const trackOffset = centerY - (currentYearRatio * trackHeight);
    
    // Convert clientY to year
    const yearRatio = (clientY - trackOffset) / trackHeight;
    const targetYear = minYear + yearRatio * yearSpan;
    
    // Find closest entry to this year
    let closest = null;
    let closestDist = Infinity;
    entries.forEach(e => {
      const dist = Math.abs(e.year - targetYear);
      if (dist < closestDist) {
        closestDist = dist;
        closest = e;
      }
    });
    
    return closest;
  }

  function scrollToEntry(entry) {
    if (!entry || !entry.el) return;
    const rect = entry.el.getBoundingClientRect();
    const centerY = window.innerHeight / 2;
    const scrollDelta = rect.top + rect.height / 2 - centerY;
    window.scrollBy({ top: scrollDelta, behavior: 'auto' });
  }

  function initDrag() {
    let lastClientY = 0;
    
    function onStart(e) {
      isDragging = true;
      container.classList.add('active');
      lastClientY = e.touches ? e.touches[0].clientY : e.clientY;
      e.preventDefault();
    }

    function onMove(e) {
      if (!isDragging) return;
      e.preventDefault();
      
      const clientY = e.touches ? e.touches[0].clientY : e.clientY;
      const deltaY = lastClientY - clientY;
      lastClientY = clientY;
      
      // Convert delta in bar space to scroll delta
      // The bar track represents the full timeline compressed
      // So a small move on bar = larger scroll on page
      const h = window.innerHeight;
      const trackHeight = h * TRACK_SCALE;
      const maxScroll = document.documentElement.scrollHeight - window.innerHeight;
      
      // Scale factor: how much page scroll per pixel of bar drag
      const scaleFactor = maxScroll / trackHeight;
      const scrollDelta = deltaY * scaleFactor;
      
      window.scrollBy({ top: scrollDelta, behavior: 'auto' });
      render();
    }

    function onEnd() {
      if (!isDragging) return;
      isDragging = false;
      container.classList.remove('active');
      
      // Snap to closest entry
      const current = findCurrentEntry();
      if (current && current.el) {
        const rect = current.el.getBoundingClientRect();
        const centerY = window.innerHeight / 2;
        const scrollDelta = rect.top + rect.height / 2 - centerY;
        window.scrollBy({ top: scrollDelta, behavior: 'smooth' });
      }
    }

    container.addEventListener('mousedown', onStart);
    document.addEventListener('mousemove', onMove);
    document.addEventListener('mouseup', onEnd);
    container.addEventListener('touchstart', onStart, { passive: false });
    document.addEventListener('touchmove', onMove, { passive: false });
    document.addEventListener('touchend', onEnd);

    svg.addEventListener('click', (e) => {
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
