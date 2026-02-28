/**
 * Time Disc Navigator
 * 
 * Fixed needle in center. Ticks move naturally like a wheel.
 * No CSS transitions - genuine movement only.
 * Bar and timeline stay in sync with non-linear mapping.
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

  // Smaller on mobile
  const isMobile = window.innerWidth <= 768;
  const BAR_WIDTH = isMobile ? 50 : 80;
  const TICK_LENGTH = isMobile ? 12 : 18;
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

    // Background - soft glow that extends beyond container, fades naturally
    content += `<defs>
      <linearGradient id="barFadeH" x1="0%" y1="0%" x2="100%" y2="0%">
        <stop offset="0%" style="stop-color:#1a1a1a;stop-opacity:0.4"/>
        <stop offset="30%" style="stop-color:#1a1a1a;stop-opacity:0.15"/>
        <stop offset="60%" style="stop-color:#1a1a1a;stop-opacity:0.05"/>
        <stop offset="100%" style="stop-color:#1a1a1a;stop-opacity:0"/>
      </linearGradient>
      <linearGradient id="glowFadeH" x1="0%" y1="0%" x2="100%" y2="0%">
        <stop offset="0%" style="stop-color:#666666;stop-opacity:0.1"/>
        <stop offset="20%" style="stop-color:#666666;stop-opacity:0.05"/>
        <stop offset="50%" style="stop-color:#666666;stop-opacity:0.02"/>
        <stop offset="100%" style="stop-color:#666666;stop-opacity:0"/>
      </linearGradient>
      <linearGradient id="vertFade" x1="0%" y1="0%" x2="0%" y2="100%">
        <stop offset="0%" style="stop-color:white;stop-opacity:0"/>
        <stop offset="10%" style="stop-color:white;stop-opacity:1"/>
        <stop offset="90%" style="stop-color:white;stop-opacity:1"/>
        <stop offset="100%" style="stop-color:white;stop-opacity:0"/>
      </linearGradient>
      <mask id="vertMask">
        <rect x="-50" y="0" width="${BAR_WIDTH + 200}" height="${h}" fill="url(#vertFade)" />
      </mask>
    </defs>`;
    content += `<g mask="url(#vertMask)">`;
    content += `<rect class="disc-glow" x="0" y="0" width="${BAR_WIDTH + 150}" height="${h}" fill="url(#glowFadeH)" />`;
    content += `<rect class="disc-bg" x="0" y="0" width="${BAR_WIDTH + 120}" height="${h}" fill="url(#barFadeH)" />`;
    content += `</g>`;

    // Ticks group - no transition, direct transform
    content += `<g id="ticksGroup">`;
    
    // Background ticks: 100 years (small), 500 years (medium with label), 1000 years (big with label)
    // Extend range by 500 years on each side
    const roundedMin = Math.floor((minYear - 500) / 100) * 100;
    const roundedMax = Math.ceil((maxYear + 500) / 100) * 100;
    
    for (let year = roundedMin; year <= roundedMax; year += 100) {
      const yearRatio = (year - minYear) / yearSpan;
      const tickY = yearRatio * trackHeight;
      
      const is1k = year % 1000 === 0;
      const is500 = year % 500 === 0;
      
      let tickLen, tickClass;
      if (is1k) {
        tickLen = TICK_LENGTH;
        tickClass = 'disc-bg-tick major';
      } else if (is500) {
        tickLen = TICK_LENGTH * 0.7;
        tickClass = 'disc-bg-tick medium';
      } else {
        tickLen = TICK_LENGTH * 0.5;
        tickClass = 'disc-bg-tick minor';
      }
      
      content += `<line class="${tickClass}" x1="0" y1="${tickY}" x2="${tickLen}" y2="${tickY}" />`;
      
      // Labels for 500 and 1000 year ticks (and year 0)
      if (is1k || is500 || year === 0) {
        const labelX = (TICK_LENGTH + TICK_LENGTH + 35) / 2;
        const bgLabelText = typeof window.formatYear === 'function' ? window.formatYear(year) : year;
        const labelClass = (is1k || year === 0) ? 'disc-bg-label major' : 'disc-bg-label medium';
        content += `<text class="${labelClass}" x="${labelX}" y="${tickY}" text-anchor="middle" dy="0.35em">${bgLabelText}</text>`;
      }
    }
    
    // Entry ticks (on top of background ticks)
    entries.forEach(e => {
      const yearRatio = (e.year - minYear) / yearSpan;
      const tickY = yearRatio * trackHeight;
      
      const x1 = 0;
      const x2 = TICK_LENGTH;
      const labelX = (x2 + TICK_LENGTH + 35) / 2; // Center between tick end and needle start

      content += `<line class="disc-tick" data-id="${e.slice.id}" data-year="${e.year}" data-index="${e.index}" x1="${x1}" y1="${tickY}" x2="${x2}" y2="${tickY}" />`;

      const yearText = typeof window.formatYear === 'function' ? window.formatYear(e.year) : e.year;
      content += `<text class="disc-label" x="${labelX}" y="${tickY}" text-anchor="middle" dy="0.35em">${yearText}</text>`;
    });
    
    content += `</g>`;

    // Fixed needle at center - clipped to bar width
    const needleStart = TICK_LENGTH + 35;
    content += `<clipPath id="needleClip"><rect x="0" y="0" width="${BAR_WIDTH}" height="${h}" /></clipPath>`;
    content += `<line class="disc-needle" x1="${needleStart}" y1="${centerY}" x2="${BAR_WIDTH}" y2="${centerY}" clip-path="url(#needleClip)" />`;

    svg.innerHTML = content;
    ticksGroup = svg.getElementById('ticksGroup');
  }

  // Get interpolated position between entries based on viewport
  function getCurrentPosition() {
    const centerY = window.innerHeight / 2;
    
    // Find the two entries we're between
    let before = null;
    let after = null;
    
    for (let i = 0; i < entries.length; i++) {
      const e = entries[i];
      if (!e.el) continue;
      const rect = e.el.getBoundingClientRect();
      const elCenter = rect.top + rect.height / 2;
      
      if (elCenter <= centerY) {
        before = { entry: e, y: elCenter };
      }
      if (elCenter > centerY && !after) {
        after = { entry: e, y: elCenter };
        break;
      }
    }
    
    // Edge cases
    if (!before && after) return { year: after.entry.year, entry: after.entry };
    if (before && !after) return { year: before.entry.year, entry: before.entry };
    if (!before && !after) return entries.length ? { year: entries[0].year, entry: entries[0] } : null;
    
    // Interpolate between the two
    const t = (centerY - before.y) / (after.y - before.y);
    const year = before.entry.year + t * (after.entry.year - before.entry.year);
    
    // Find closest entry for highlighting
    const closestEntry = t < 0.5 ? before.entry : after.entry;
    
    return { year, entry: closestEntry };
  }

  let lastCurrentEntry = null;

  function updatePosition() {
    if (!ticksGroup || !entries.length) return;

    const h = window.innerHeight;
    const centerY = h / 2;
    const minYear = entries[0].year;
    const maxYear = entries[entries.length - 1].year;
    const yearSpan = maxYear - minYear || 1;
    const trackHeight = h * TRACK_SCALE;

    const pos = getCurrentPosition();
    if (!pos) return;

    // Vibrate when current entry changes
    if (pos.entry !== lastCurrentEntry) {
      if (navigator.vibrate) navigator.vibrate(10);
      lastCurrentEntry = pos.entry;
    }

    const currentYearRatio = (pos.year - minYear) / yearSpan;
    const currentTickY = currentYearRatio * trackHeight;
    
    // Direct transform - no transition
    const translateY = centerY - currentTickY;
    ticksGroup.setAttribute('transform', `translate(0, ${translateY})`);

    // Update current styling
    const ticks = ticksGroup.querySelectorAll('.disc-tick');
    const labels = ticksGroup.querySelectorAll('.disc-label');
    
    ticks.forEach((tick, i) => {
      tick.classList.toggle('current', entries[i] === pos.entry);
    });
    labels.forEach((label, i) => {
      label.classList.toggle('current', entries[i] === pos.entry);
    });

    // Update year display
    if (yearDisplay) {
      const displayYear = Math.round(pos.year);
      yearDisplay.textContent = typeof window.formatYear === 'function' ? window.formatYear(displayYear) : displayYear;
    }
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
      
      const h = window.innerHeight;
      const trackHeight = h * TRACK_SCALE;
      const maxScroll = document.documentElement.scrollHeight - window.innerHeight;
      
      // Scale factor: bar movement to page scroll
      const scaleFactor = maxScroll / trackHeight;
      const scrollDelta = deltaY * scaleFactor;
      
      window.scrollBy({ top: scrollDelta, behavior: 'auto' });
    }

    function onEnd() {
      if (!isDragging) return;
      isDragging = false;
      container.classList.remove('active');
      
      // Snap to closest entry
      const pos = getCurrentPosition();
      if (pos && pos.entry && pos.entry.el) {
        const rect = pos.entry.el.getBoundingClientRect();
        const centerY = window.innerHeight / 2;
        const scrollDelta = rect.top + rect.height / 2 - centerY;
        window.scrollBy({ top: scrollDelta, behavior: 'smooth' });
        if (navigator.vibrate) navigator.vibrate(10);
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
