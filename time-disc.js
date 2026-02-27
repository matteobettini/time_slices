/**
 * Time Disc Navigator
 * 
 * A large semicircular disc, mostly off-screen.
 * Only a thin arc is visible at the screen edge.
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

  const VISIBLE_WIDTH = 35;
  const TICK_LENGTH = 12;

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
    const viewportHeight = window.innerHeight;
    const centerY = viewportHeight / 2;
    
    // Large radius so the arc is subtle
    const DISC_RADIUS = viewportHeight * 1.5;
    
    // SVG size
    const svgWidth = VISIBLE_WIDTH + 10;
    const svgHeight = viewportHeight;
    
    svg.setAttribute('width', svgWidth);
    svg.setAttribute('height', svgHeight);
    svg.setAttribute('viewBox', `0 0 ${svgWidth} ${svgHeight}`);

    let content = '';

    // Disc center position (off-screen)
    // For left side: center is far to the left
    // For right side: center is far to the right
    const cx = isMobile ? (svgWidth + DISC_RADIUS - VISIBLE_WIDTH) : (-DISC_RADIUS + VISIBLE_WIDTH);
    const cy = viewportHeight / 2;

    // Draw arc using a path
    // We want an arc that spans from top to bottom of viewport
    const arcStartY = 0;
    const arcEndY = viewportHeight;
    
    // Calculate X positions on the arc for top and bottom
    const dyTop = arcStartY - cy;
    const dyBottom = arcEndY - cy;
    
    // x = cx + sqrt(r^2 - dy^2) for right side of circle
    // x = cx - sqrt(r^2 - dy^2) for left side of circle
    const dxTop = Math.sqrt(Math.max(0, DISC_RADIUS * DISC_RADIUS - dyTop * dyTop));
    const dxBottom = Math.sqrt(Math.max(0, DISC_RADIUS * DISC_RADIUS - dyBottom * dyBottom));
    
    let arcX1, arcX2;
    if (isMobile) {
      // Right edge - we want the left side of the circle
      arcX1 = cx - dxTop;
      arcX2 = cx - dxBottom;
    } else {
      // Left edge - we want the right side of the circle  
      arcX1 = cx + dxTop;
      arcX2 = cx + dxBottom;
    }
    
    // Draw filled arc
    const largeArc = 0; // We want the smaller arc
    const sweep = isMobile ? 1 : 0;
    content += `<path class="disc-bg" d="M ${cx},${cy} L ${arcX1},${arcStartY} A ${DISC_RADIUS},${DISC_RADIUS} 0 ${largeArc},${sweep} ${arcX2},${arcEndY} Z" />`;

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

    // Draw ticks
    entries.forEach(e => {
      if (!e.el) return;
      
      const rect = e.el.getBoundingClientRect();
      const elCenterY = rect.top + rect.height / 2;
      
      // Skip if off screen
      if (elCenterY < -100 || elCenterY > viewportHeight + 100) return;
      
      // Calculate X position on the arc for this Y
      const dy = elCenterY - cy;
      const dx = Math.sqrt(Math.max(0, DISC_RADIUS * DISC_RADIUS - dy * dy));
      
      let tickX1, tickX2, labelX;
      if (isMobile) {
        tickX1 = cx - dx + 2;
        tickX2 = cx - dx + 2 + TICK_LENGTH;
        labelX = tickX2 + 5;
      } else {
        tickX2 = cx + dx - 2;
        tickX1 = cx + dx - 2 - TICK_LENGTH;
        labelX = tickX1 - 5;
      }
      
      const isCurrent = e === currentEntry && currentDist < 150;
      const tickClass = isCurrent ? 'disc-tick current' : 'disc-tick';

      content += `<line class="${tickClass}" data-id="${e.slice.id}" data-year="${e.year}" x1="${tickX1}" y1="${elCenterY}" x2="${tickX2}" y2="${elCenterY}" />`;

      // Year label
      const yearText = typeof window.formatYear === 'function' ? window.formatYear(e.year) : e.year;
      const labelClass = isCurrent ? 'disc-label current' : 'disc-label';
      const anchor = isMobile ? 'start' : 'end';
      content += `<text class="${labelClass}" x="${labelX}" y="${elCenterY + 4}" text-anchor="${anchor}">${yearText}</text>`;
    });

    // Needle at center
    const needleDx = Math.sqrt(DISC_RADIUS * DISC_RADIUS);
    if (isMobile) {
      content += `<line class="disc-needle" x1="0" y1="${centerY}" x2="${VISIBLE_WIDTH + 5}" y2="${centerY}" />`;
    } else {
      content += `<line class="disc-needle" x1="0" y1="${centerY}" x2="${VISIBLE_WIDTH + 5}" y2="${centerY}" />`;
    }

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
