/**
 * Time Disc Navigator
 * 
 * Bar with ticks spaced by year.
 * Dragging scrolls to entries based on year position.
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
  const PADDING = 60; // Padding at top/bottom of bar

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

  // Convert year to Y position on bar
  function yearToBarY(year, h) {
    if (!entries.length) return h / 2;
    const minYear = entries[0].year;
    const maxYear = entries[entries.length - 1].year;
    const yearSpan = maxYear - minYear || 1;
    const usableHeight = h - PADDING * 2;
    const ratio = (year - minYear) / yearSpan;
    return PADDING + ratio * usableHeight;
  }

  // Convert Y position on bar to year
  function barYToYear(y, h) {
    if (!entries.length) return 0;
    const minYear = entries[0].year;
    const maxYear = entries[entries.length - 1].year;
    const yearSpan = maxYear - minYear || 1;
    const usableHeight = h - PADDING * 2;
    const ratio = Math.max(0, Math.min(1, (y - PADDING) / usableHeight));
    return minYear + ratio * yearSpan;
  }

  // Find entry closest to a year
  function findEntryByYear(targetYear) {
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

  // Find entry closest to viewport center
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

  function render() {
    const h = window.innerHeight;
    const centerY = h / 2;
    
    svg.setAttribute('width', BAR_WIDTH);
    svg.setAttribute('height', h);
    svg.setAttribute('viewBox', `0 0 ${BAR_WIDTH} ${h}`);

    let content = '';

    // Background with grey glow
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

    // Find current entry (in viewport)
    const currentEntry = findCurrentEntry();

    // Draw ticks - fixed positions based on year
    entries.forEach(e => {
      const tickY = yearToBarY(e.year, h);
      
      // Skip if off screen
      if (tickY < -20 || tickY > h + 20) return;
      
      const x1 = 0;
      const x2 = TICK_LENGTH;
      const labelX = x2 + 4;
      
      const isCurrent = e === currentEntry;
      const tickClass = isCurrent ? 'disc-tick current' : 'disc-tick';

      content += `<line class="${tickClass}" data-id="${e.slice.id}" data-year="${e.year}" x1="${x1}" y1="${tickY}" x2="${x2}" y2="${tickY}" />`;

      const yearText = typeof window.formatYear === 'function' ? window.formatYear(e.year) : e.year;
      const labelClass = isCurrent ? 'disc-label current' : 'disc-label';
      content += `<text class="${labelClass}" x="${labelX}" y="${tickY + 4}" text-anchor="start">${yearText}</text>`;
    });

    // Needle - positioned at current entry's year position (not fixed at center)
    if (currentEntry) {
      const needleY = yearToBarY(currentEntry.year, h);
      content += `<line class="disc-needle" x1="0" y1="${needleY}" x2="${BAR_WIDTH}" y2="${needleY}" />`;
      
      if (yearDisplay) {
        yearDisplay.textContent = typeof window.formatYear === 'function' ? window.formatYear(currentEntry.year) : currentEntry.year;
      }
    }

    svg.innerHTML = content;
  }

  function scrollToEntry(entry) {
    if (!entry || !entry.el) return;
    const rect = entry.el.getBoundingClientRect();
    const centerY = window.innerHeight / 2;
    const scrollDelta = rect.top + rect.height / 2 - centerY;
    window.scrollBy({ top: scrollDelta, behavior: 'smooth' });
    if (navigator.vibrate) navigator.vibrate(10);
  }

  function initDrag() {
    function onStart(e) {
      isDragging = true;
      container.classList.add('active');
      e.preventDefault();
      
      // Immediately scroll to entry at click position
      const clientY = e.touches ? e.touches[0].clientY : e.clientY;
      const year = barYToYear(clientY, window.innerHeight);
      const entry = findEntryByYear(year);
      if (entry) scrollToEntry(entry);
    }

    function onMove(e) {
      if (!isDragging) return;
      e.preventDefault();
      
      const clientY = e.touches ? e.touches[0].clientY : e.clientY;
      const year = barYToYear(clientY, window.innerHeight);
      const entry = findEntryByYear(year);
      
      if (entry && entry.el) {
        // Scroll to center entry instantly
        const rect = entry.el.getBoundingClientRect();
        const centerY = window.innerHeight / 2;
        const scrollDelta = rect.top + rect.height / 2 - centerY;
        window.scrollBy({ top: scrollDelta, behavior: 'auto' });
        render();
      }
    }

    function onEnd() {
      if (!isDragging) return;
      isDragging = false;
      container.classList.remove('active');
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

  // Update on scroll
  let scrollTimer = null;
  window.addEventListener('scroll', () => {
    if (scrollTimer) return;
    scrollTimer = requestAnimationFrame(() => {
      scrollTimer = null;
      if (!container.classList.contains('hidden')) render();
    });
  }, { passive: true });

  // Rebuild on resize
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
