/**
 * Time Disc Navigator
 * 
 * A simple bar with ticks spaced by time distance.
 * Drag to scroll through entries.
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
  let dragStartScroll = 0;

  const BAR_WIDTH = 24;
  const TICK_LENGTH = 10;

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
    const isMobile = window.innerWidth <= 768;
    const h = window.innerHeight;
    const centerY = h / 2;
    
    svg.setAttribute('width', BAR_WIDTH);
    svg.setAttribute('height', h);
    svg.setAttribute('viewBox', `0 0 ${BAR_WIDTH} ${h}`);

    let content = '';

    // Simple bar background
    content += `<rect class="disc-bg" x="0" y="0" width="${BAR_WIDTH}" height="${h}" rx="4" />`;

    // Find min/max years for proportional spacing
    const minYear = entries.length > 0 ? entries[0].year : 0;
    const maxYear = entries.length > 0 ? entries[entries.length - 1].year : 1;
    const yearSpan = maxYear - minYear || 1;

    // Find current entry (closest to center)
    let currentEntry = null;
    let currentDist = Infinity;
    entries.forEach(e => {
      if (!e.el) return;
      const rect = e.el.getBoundingClientRect();
      const dist = Math.abs(rect.top + rect.height / 2 - centerY);
      if (dist < currentDist) {
        currentDist = dist;
        currentEntry = e;
      }
    });

    // Draw ticks - Y position proportional to year (compressed to fit better)
    const padding = 60;
    const usableHeight = h - padding * 2;
    
    entries.forEach(e => {
      if (!e.el) return;
      
      // Calculate Y based on year proportion (not DOM position)
      const yearT = (e.year - minYear) / yearSpan;
      const tickY = padding + yearT * usableHeight;
      
      let x1, x2, labelX, anchor;
      if (isMobile) {
        x1 = 2;
        x2 = x1 + TICK_LENGTH;
        labelX = x2 + 4;
        anchor = 'start';
      } else {
        x2 = BAR_WIDTH - 2;
        x1 = x2 - TICK_LENGTH;
        labelX = x1 - 4;
        anchor = 'end';
      }
      
      const isCurrent = e === currentEntry;
      const tickClass = isCurrent ? 'disc-tick current' : 'disc-tick';

      content += `<line class="${tickClass}" data-id="${e.slice.id}" data-year="${e.year}" x1="${x1}" y1="${tickY}" x2="${x2}" y2="${tickY}" />`;

      // Year label  
      const yearText = typeof window.formatYear === 'function' ? window.formatYear(e.year) : e.year;
      const labelClass = isCurrent ? 'disc-label current' : 'disc-label';
      content += `<text class="${labelClass}" x="${labelX}" y="${tickY + 3}" text-anchor="${anchor}">${yearText}</text>`;
    });

    // Needle at center
    content += `<line class="disc-needle" x1="0" y1="${centerY}" x2="${BAR_WIDTH}" y2="${centerY}" />`;

    // Update year display
    if (currentEntry && yearDisplay) {
      yearDisplay.textContent = typeof window.formatYear === 'function' ? window.formatYear(currentEntry.year) : currentEntry.year;
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
      // Higher multiplier for faster scrolling
      window.scrollTo({ top: dragStartScroll + deltaY * 5, behavior: 'auto' });
      render();
    }

    function onEnd() {
      if (!isDragging) return;
      isDragging = false;
      container.classList.remove('active');
      
      // Snap to closest entry
      snapToClosestEntry();
    }
    
    function snapToClosestEntry() {
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
      
      if (closest && closest.el) {
        const rect = closest.el.getBoundingClientRect();
        const elCenter = rect.top + rect.height / 2;
        const scrollDelta = elCenter - centerY;
        
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
