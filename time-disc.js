/**
 * Time Disc Navigator
 * 
 * A semicircle that touches top and bottom of viewport.
 * Only a thin arc visible at the screen edge.
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

  const VISIBLE_WIDTH = 28;
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
    
    // Circle radius: must touch top (y=0) and bottom (y=h) of viewport
    // Circle center is at (cx, h/2), radius = h/2
    // The visible edge is where x intersects our visible strip
    const radius = h / 2;
    
    svg.setAttribute('width', VISIBLE_WIDTH);
    svg.setAttribute('height', h);
    svg.setAttribute('viewBox', `0 0 ${VISIBLE_WIDTH} ${h}`);

    let content = '';

    // Circle center X position (off-screen)
    // For the edge to show VISIBLE_WIDTH pixels, center is at: 
    // Desktop (left): cx = -(radius - VISIBLE_WIDTH)
    // Mobile (right): cx = VISIBLE_WIDTH + (radius - VISIBLE_WIDTH) = radius
    const cx = isMobile ? radius : -(radius - VISIBLE_WIDTH);
    const cy = centerY;

    // Draw arc from top to bottom
    // Top point: (cx + sqrt(r² - (0-cy)²), 0) but we need the edge point
    // At y=0: x = cx + sqrt(r² - r²) = cx (circle touches at center-x level)
    // Actually at y=0, dy = -r, so x = cx (tangent point)
    
    // Calculate visible arc points
    const topY = 0;
    const bottomY = h;
    
    // At top (y=0): dy = 0 - cy = -radius, x = cx (tangent)
    // At bottom (y=h): dy = h - cy = radius, x = cx (tangent)
    // At center (y=h/2): dy = 0, x = cx + radius (rightmost) or cx - radius (leftmost)
    
    if (isMobile) {
      // Right edge - draw left side of circle
      // Arc from (cx, 0) around to (cx, h), bulging left
      const leftX = cx - radius; // Leftmost point at center
      content += `<path class="disc-bg" d="
        M ${cx} ${topY}
        A ${radius} ${radius} 0 0 0 ${cx} ${bottomY}
        L ${VISIBLE_WIDTH} ${bottomY}
        L ${VISIBLE_WIDTH} ${topY}
        Z
      " />`;
    } else {
      // Left edge - draw right side of circle  
      // Arc from (cx, 0) around to (cx, h), bulging right
      const rightX = cx + radius; // Rightmost point at center
      content += `<path class="disc-bg" d="
        M ${cx} ${topY}
        A ${radius} ${radius} 0 0 1 ${cx} ${bottomY}
        L 0 ${bottomY}
        L 0 ${topY}
        Z
      " />`;
    }

    // Find current entry
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

    // Draw ticks along the arc
    entries.forEach(e => {
      if (!e.el) return;
      
      const rect = e.el.getBoundingClientRect();
      const elY = rect.top + rect.height / 2;
      
      if (elY < -50 || elY > h + 50) return;
      
      // Calculate X on the circle at this Y
      const dy = elY - cy;
      const dx = Math.sqrt(Math.max(0, radius * radius - dy * dy));
      
      let arcX, x1, x2, labelX, anchor;
      if (isMobile) {
        // Left side of circle
        arcX = cx - dx;
        x1 = arcX;
        x2 = arcX + TICK_LENGTH;
        labelX = x2 + 3;
        anchor = 'start';
      } else {
        // Right side of circle
        arcX = cx + dx;
        x2 = arcX;
        x1 = arcX - TICK_LENGTH;
        labelX = x1 - 3;
        anchor = 'end';
      }
      
      const isCurrent = e === currentEntry && currentDist < 150;
      const tickClass = isCurrent ? 'disc-tick current' : 'disc-tick';

      content += `<line class="${tickClass}" data-id="${e.slice.id}" data-year="${e.year}" x1="${x1}" y1="${elY}" x2="${x2}" y2="${elY}" />`;

      // Year label  
      const yearText = typeof window.formatYear === 'function' ? window.formatYear(e.year) : e.year;
      const labelClass = isCurrent ? 'disc-label current' : 'disc-label';
      content += `<text class="${labelClass}" x="${labelX}" y="${elY + 3}" text-anchor="${anchor}">${yearText}</text>`;
    });

    // Needle at center (full width of visible area)
    content += `<line class="disc-needle" x1="0" y1="${centerY}" x2="${VISIBLE_WIDTH}" y2="${centerY}" />`;

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
      window.scrollTo({ top: dragStartScroll + deltaY * 3, behavior: 'auto' });
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
