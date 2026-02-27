/**
 * Time Disc Navigator
 * 
 * A circular disc where entry ticks move with the page scroll.
 * The needle in the center is fixed - ticks scroll past it.
 * Drag the disc to scroll the page.
 */

(function() {
  'use strict';

  const container = document.getElementById('timeDiscContainer');
  const disc = document.getElementById('timeDisc');
  const svg = document.getElementById('timeDiscSvg');
  const yearDisplay = document.getElementById('timeDiscYear');

  if (!container || !disc || !svg) {
    console.error('Time Disc: Missing DOM elements');
    return;
  }

  let entries = [];
  let isDragging = false;
  let dragStartY = 0;
  let dragStartScroll = 0;

  const DISC_RADIUS = 120;
  const TICK_INNER = 95;
  const TICK_OUTER = 115;

  function build() {
    if (!window.SLICES || !window.SLICES.length) {
      return;
    }

    const slices = window.activeThread
      ? window.SLICES.filter(s => (s.threads || []).includes(window.activeThread))
      : window.SLICES;

    if (!slices.length) {
      entries = [];
      svg.innerHTML = '';
      return;
    }

    const sorted = [...slices].sort((a, b) => parseInt(a.year) - parseInt(b.year));
    const isMobile = window.innerWidth <= 768;

    // SVG centered on disc
    const size = DISC_RADIUS * 2 + 20;
    svg.setAttribute('width', size);
    svg.setAttribute('height', size);
    svg.setAttribute('viewBox', `0 0 ${size} ${size}`);

    // Store entry data
    entries = sorted.map(slice => ({
      year: parseInt(slice.year),
      slice,
      el: document.querySelector(`#entry-${slice.id}`)
    }));

    // Initial render
    render();
  }

  function render() {
    const isMobile = window.innerWidth <= 768;
    const size = DISC_RADIUS * 2 + 20;
    const cx = size / 2;
    const cy = size / 2;
    const viewportHeight = window.innerHeight;
    const centerY = viewportHeight / 2;

    let content = '';

    // Disc background
    content += `<circle class="disc-bg" cx="${cx}" cy="${cy}" r="${DISC_RADIUS}" />`;

    let currentEntry = null;
    let currentDist = Infinity;

    // Find current entry first
    entries.forEach(e => {
      if (!e.el) return;
      const rect = e.el.getBoundingClientRect();
      const elCenterY = rect.top + rect.height / 2;
      const dist = Math.abs(elCenterY - centerY);
      if (dist < currentDist) {
        currentDist = dist;
        currentEntry = e;
      }
    });

    // Draw ticks around the disc
    // Map viewport position to angle on disc
    // Entries scroll from top (angle -90°) through center (0°) to bottom (+90°)
    entries.forEach(e => {
      if (!e.el) return;
      
      const rect = e.el.getBoundingClientRect();
      const elCenterY = rect.top + rect.height / 2;
      
      // Map Y position to angle: viewport maps to -90° to +90° arc on right side
      const t = (elCenterY - centerY) / (viewportHeight / 2); // -1 to 1 roughly
      const angle = t * 90; // -90° to +90°
      
      // Skip if too far off screen
      if (Math.abs(angle) > 100) return;
      
      const angleRad = (angle * Math.PI) / 180;
      
      // Tick coordinates (on right side of disc for desktop, left for mobile)
      const direction = isMobile ? Math.PI : 0; // 0 = right, PI = left
      const tickAngle = direction + angleRad;
      
      const x1 = cx + TICK_INNER * Math.cos(tickAngle);
      const y1 = cy + TICK_INNER * Math.sin(tickAngle);
      const x2 = cx + TICK_OUTER * Math.cos(tickAngle);
      const y2 = cy + TICK_OUTER * Math.sin(tickAngle);
      
      const isCurrent = e === currentEntry && currentDist < 150;
      const tickClass = isCurrent ? 'disc-tick current' : 'disc-tick';

      content += `<line class="${tickClass}" data-id="${e.slice.id}" data-year="${e.year}" x1="${x1}" y1="${y1}" x2="${x2}" y2="${y2}" />`;

      // Year label (only for current or nearby)
      if (Math.abs(angle) < 60) {
        const labelR = TICK_INNER - 12;
        const labelX = cx + labelR * Math.cos(tickAngle);
        const labelY = cy + labelR * Math.sin(tickAngle);
        const yearText = typeof window.formatYear === 'function' ? window.formatYear(e.year) : e.year;
        const labelClass = isCurrent ? 'disc-label current' : 'disc-label';
        
        // Rotate text to follow curve
        const textAngle = angle + (isMobile ? 180 : 0);
        content += `<text class="${labelClass}" data-year="${e.year}" x="${labelX}" y="${labelY}" text-anchor="middle" dominant-baseline="middle" transform="rotate(${textAngle}, ${labelX}, ${labelY})">${yearText}</text>`;
      }
    });

    // Center needle (horizontal line at 0°)
    const needleAngle = isMobile ? Math.PI : 0;
    const nx1 = cx + (TICK_INNER - 10) * Math.cos(needleAngle);
    const ny1 = cy + (TICK_INNER - 10) * Math.sin(needleAngle);
    const nx2 = cx + (TICK_OUTER + 5) * Math.cos(needleAngle);
    const ny2 = cy + (TICK_OUTER + 5) * Math.sin(needleAngle);
    content += `<line class="disc-needle" x1="${nx1}" y1="${ny1}" x2="${nx2}" y2="${ny2}" />`;

    // Update year display
    if (currentEntry && yearDisplay) {
      const yearText = typeof window.formatYear === 'function' ? window.formatYear(currentEntry.year) : currentEntry.year;
      yearDisplay.textContent = yearText;
    }

    svg.innerHTML = content;
  }

  function initDrag() {
    function onStart(e) {
      isDragging = true;
      container.classList.add('active');
      
      const clientY = e.touches ? e.touches[0].clientY : e.clientY;
      dragStartY = clientY;
      dragStartScroll = window.scrollY;
      
      e.preventDefault();
    }

    function onMove(e) {
      if (!isDragging) return;
      e.preventDefault();
      
      const clientY = e.touches ? e.touches[0].clientY : e.clientY;
      const deltaY = dragStartY - clientY;
      
      window.scrollTo({
        top: dragStartScroll + deltaY * 3,
        behavior: 'auto'
      });
      
      render();
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
      if (isDragging) return;
      const tick = e.target.closest('.disc-tick');
      if (tick) {
        const id = tick.dataset.id;
        const el = document.querySelector(`#entry-${id}`);
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

  // Re-render on scroll
  let scrollTimer = null;
  window.addEventListener('scroll', () => {
    if (scrollTimer) return;
    scrollTimer = requestAnimationFrame(() => {
      scrollTimer = null;
      if (!container.classList.contains('hidden')) {
        render();
      }
    });
  }, { passive: true });

  // Rebuild on resize
  let resizeTimer = null;
  window.addEventListener('resize', () => {
    clearTimeout(resizeTimer);
    resizeTimer = setTimeout(build, 200);
  });

  // Exports
  window.buildTimeDisc = build;
  window.showTimeDisc = () => container.classList.remove('hidden');
  window.hideTimeDisc = () => container.classList.add('hidden');

  initDrag();

  if (window.SLICES && window.SLICES.length) {
    build();
  }

})();
