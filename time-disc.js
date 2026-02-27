/**
 * Time Disc Navigator
 * 
 * A scrollbar-like strip where entry ticks move with the page scroll.
 * The needle in the center is fixed - ticks scroll past it.
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
  let scrollSyncEnabled = true;

  const STRIP_WIDTH = 40;
  const TICK_WIDTH = 20;

  function build() {
    console.log('Time Disc build() called, SLICES:', window.SLICES?.length);
    
    if (!window.SLICES || !window.SLICES.length) {
      console.log('Time Disc: No slices yet');
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
    const height = window.innerHeight;
    const isMobile = window.innerWidth <= 768;

    // SVG is viewport height
    svg.setAttribute('width', STRIP_WIDTH);
    svg.setAttribute('height', height);
    svg.style.width = STRIP_WIDTH + 'px';
    svg.style.height = height + 'px';

    // Store entry data with their DOM element positions
    entries = sorted.map(slice => ({
      year: parseInt(slice.year),
      slice,
      el: document.querySelector(`#entry-${slice.id}`),
      tickEl: null,
      labelEl: null
    }));

    // Initial render
    render();
    
    console.log('Time Disc: Built with', entries.length, 'entries');
  }

  function render() {
    const height = window.innerHeight;
    const centerY = height / 2;
    const isMobile = window.innerWidth <= 768;

    let content = '';

    // Background strip
    content += `<rect class="disc-bg" x="0" y="0" width="${STRIP_WIDTH}" height="${height}" />`;

    // Calculate tick positions based on actual DOM element positions
    entries.forEach(e => {
      if (!e.el) return;
      
      const rect = e.el.getBoundingClientRect();
      const elCenterY = rect.top + rect.height / 2;
      
      // Map element position to a Y position on the strip
      // Element at viewport center = tick at strip center
      const tickY = elCenterY;
      
      // Only draw if in viewport (with some margin)
      if (tickY < -50 || tickY > height + 50) return;
      
      // Tick mark
      const x1 = isMobile ? 0 : STRIP_WIDTH - TICK_WIDTH;
      const x2 = isMobile ? TICK_WIDTH : STRIP_WIDTH;
      
      const isCurrent = Math.abs(tickY - centerY) < 50;
      const tickClass = isCurrent ? 'disc-tick current' : 'disc-tick';

      content += `<line class="${tickClass}" data-id="${e.slice.id}" data-year="${e.year}" x1="${x1}" y1="${tickY}" x2="${x2}" y2="${tickY}" />`;

      // Year label
      const labelX = isMobile ? TICK_WIDTH + 6 : STRIP_WIDTH - TICK_WIDTH - 6;
      const anchor = isMobile ? 'start' : 'end';
      const yearText = typeof window.formatYear === 'function' ? window.formatYear(e.year) : e.year;
      const labelClass = isCurrent ? 'disc-label current' : 'disc-label';
      
      content += `<text class="${labelClass}" data-year="${e.year}" x="${labelX}" y="${tickY + 4}" text-anchor="${anchor}">${yearText}</text>`;
      
      // Update year display for current
      if (isCurrent && yearDisplay) {
        yearDisplay.textContent = yearText;
      }
    });

    // Center needle (fixed indicator)
    content += `<line class="disc-needle" x1="0" y1="${centerY}" x2="${STRIP_WIDTH}" y2="${centerY}" />`;

    svg.innerHTML = content;
  }

  function scrollToY(clientY) {
    // Find entry closest to this Y position on screen
    let closest = null;
    let closestDist = Infinity;

    entries.forEach(e => {
      if (!e.el) return;
      const rect = e.el.getBoundingClientRect();
      const elY = rect.top + rect.height / 2;
      const dist = Math.abs(elY - clientY);
      
      if (dist < closestDist) {
        closestDist = dist;
        closest = e;
      }
    });

    if (closest && closest.el) {
      // Scroll to put this entry at viewport center
      const rect = closest.el.getBoundingClientRect();
      const elCenter = rect.top + rect.height / 2;
      const viewportCenter = window.innerHeight / 2;
      const scrollDelta = elCenter - viewportCenter;
      
      window.scrollBy({ top: scrollDelta, behavior: 'auto' });
    }
  }

  function initDrag() {
    function onStart(e) {
      isDragging = true;
      scrollSyncEnabled = false;
      container.classList.add('active');
      e.preventDefault();
    }

    function onMove(e) {
      if (!isDragging) return;
      e.preventDefault();
      const clientY = e.touches ? e.touches[0].clientY : e.clientY;
      scrollToY(clientY);
    }

    function onEnd() {
      if (!isDragging) return;
      isDragging = false;
      container.classList.remove('active');
      setTimeout(() => { scrollSyncEnabled = true; }, 200);
    }

    container.addEventListener('mousedown', onStart);
    document.addEventListener('mousemove', onMove);
    document.addEventListener('mouseup', onEnd);

    container.addEventListener('touchstart', onStart, { passive: false });
    document.addEventListener('touchmove', onMove, { passive: false });
    document.addEventListener('touchend', onEnd);

    svg.addEventListener('click', (e) => {
      const tick = e.target.closest('.disc-tick');
      if (tick && !isDragging) {
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

  // Re-render on scroll (ticks move with content)
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

  // Initialize drag handlers
  initDrag();

  // Build if SLICES exists
  if (window.SLICES && window.SLICES.length) {
    build();
  }

})();
