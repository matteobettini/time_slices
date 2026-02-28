/**
 * Time Disc Navigator
 * 
 * Fixed needle in center. Ticks move smoothly past it as you scroll.
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
  let ticksGroup = null;

  const BAR_WIDTH = 60;
  const TICK_LENGTH = 14;
  const TRACK_SCALE = 0.5;

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

    buildSVG();
    updatePosition();
  }

  function buildSVG() {
    const h = window.innerHeight;
    const centerY = h / 2;
    
    svg.setAttribute('width', BAR_WIDTH);
    svg.setAttribute('height', h);
    svg.setAttribute('viewBox', `0 0 ${BAR_WIDTH} ${h}`);

    if (!entries.length) return;

    const minYear = entries[0].year;
    const maxYear = entries[entries.length - 1].year;
    const yearSpan = maxYear - minYear || 1;
    const trackHeight = h * TRACK_SCALE;

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

    // Ticks group - will be translated
    content += `<g id="ticksGroup" style="transition: transform 0.15s ease-out;">`;
    
    // Draw ticks at their year-based positions (relative to track)
    entries.forEach(e => {
      const yearRatio = (e.year - minYear) / yearSpan;
      const tickY = yearRatio * trackHeight;
      
      const x1 = 0;
      const x2 = TICK_LENGTH;
      const labelX = x2 + 4;

      content += `<line class="disc-tick" data-id="${e.slice.id}" data-year="${e.year}" data-index="${e.index}" x1="${x1}" y1="${tickY}" x2="${x2}" y2="${tickY}" />`;

      const yearText = typeof window.formatYear === 'function' ? window.formatYear(e.year) : e.year;
      content += `<text class="disc-label" x="${labelX}" y="${tickY}" text-anchor="start" dominant-baseline="middle">${yearText}</text>`;
    });
    
    content += `</g>`;

    // Fixed needle at center - only right part (after year label)
    const needleStart = TICK_LENGTH + 35;
    content += `<line class="disc-needle" x1="${needleStart}" y1="${centerY}" x2="${BAR_WIDTH}" y2="${centerY}" />`;

    svg.innerHTML = content;
    ticksGroup = svg.getElementById('ticksGroup');
  }

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

  function updatePosition() {
    if (!ticksGroup || !entries.length) return;

    const h = window.innerHeight;
    const centerY = h / 2;
    const minYear = entries[0].year;
    const maxYear = entries[entries.length - 1].year;
    const yearSpan = maxYear - minYear || 1;
    const trackHeight = h * TRACK_SCALE;

    const currentEntry = findCurrentEntry();
    if (!currentEntry) return;

    const currentYearRatio = (currentEntry.year - minYear) / yearSpan;
    const currentTickY = currentYearRatio * trackHeight;
    
    // Translate group so current tick is at center
    const translateY = centerY - currentTickY;
    ticksGroup.style.transform = `translateY(${translateY}px)`;

    // Update current styling
    const ticks = ticksGroup.querySelectorAll('.disc-tick');
    const labels = ticksGroup.querySelectorAll('.disc-label');
    
    ticks.forEach((tick, i) => {
      tick.classList.toggle('current', entries[i] === currentEntry);
    });
    labels.forEach((label, i) => {
      label.classList.toggle('current', entries[i] === currentEntry);
    });

    // Update year display
    if (yearDisplay) {
      yearDisplay.textContent = typeof window.formatYear === 'function' ? window.formatYear(currentEntry.year) : currentEntry.year;
    }
  }

  function initDrag() {
    let lastClientY = 0;
    
    function onStart(e) {
      isDragging = true;
      container.classList.add('active');
      lastClientY = e.touches ? e.touches[0].clientY : e.clientY;
      // Disable transition during drag for immediate response
      if (ticksGroup) ticksGroup.style.transition = 'none';
      e.preventDefault();
    }

    function onMove(e) {
      if (!isDragging) return;
      e.preventDefault();
      
      const clientY = e.touches ? e.touches[0].clientY : e.clientY;
      const deltaY = lastClientY - clientY;
      lastClientY = clientY;
      
      const h = window.innerHeight;
      const trackHeight = h * TRACK_SCALE;
      const maxScroll = document.documentElement.scrollHeight - window.innerHeight;
      
      const scaleFactor = maxScroll / trackHeight;
      const scrollDelta = deltaY * scaleFactor;
      
      window.scrollBy({ top: scrollDelta, behavior: 'auto' });
      updatePosition();
    }

    function onEnd() {
      if (!isDragging) return;
      isDragging = false;
      container.classList.remove('active');
      
      // Re-enable transition
      if (ticksGroup) ticksGroup.style.transition = 'transform 0.15s ease-out';
      
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
      if (!container.classList.contains('hidden')) updatePosition();
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
