/**
 * Time Disc Navigator
 * 
 * A curved edge with ticks that scroll with content.
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

  const VISIBLE_WIDTH = 40;
  const TICK_LENGTH = 15;

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
    
    // Simple curved background using quadratic bezier
    // Creates a subtle curve bulging outward
    const curveDepth = 20; // How much the curve bulges
    
    svg.setAttribute('width', VISIBLE_WIDTH);
    svg.setAttribute('height', h);
    svg.setAttribute('viewBox', `0 0 ${VISIBLE_WIDTH} ${h}`);

    let content = '';

    // Draw curved background
    if (isMobile) {
      // Right side - curve bulges left
      content += `<path class="disc-bg" d="
        M ${VISIBLE_WIDTH} 0 
        L ${VISIBLE_WIDTH} ${h}
        L ${VISIBLE_WIDTH - curveDepth} ${h}
        Q 0 ${h/2} ${VISIBLE_WIDTH - curveDepth} 0
        Z
      " />`;
    } else {
      // Left side - curve bulges right
      content += `<path class="disc-bg" d="
        M 0 0 
        L 0 ${h}
        L ${curveDepth} ${h}
        Q ${VISIBLE_WIDTH} ${h/2} ${curveDepth} 0
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

    // Draw ticks along the curve
    entries.forEach(e => {
      if (!e.el) return;
      
      const rect = e.el.getBoundingClientRect();
      const elY = rect.top + rect.height / 2;
      
      // Skip if off screen
      if (elY < -50 || elY > h + 50) return;
      
      // Calculate x position on the curve at this y
      // Quadratic curve: x = curveDepth at top/bottom, x = VISIBLE_WIDTH at center
      const t = Math.abs(elY - centerY) / (h / 2); // 0 at center, 1 at edges
      const curveX = curveDepth + (1 - t * t) * (VISIBLE_WIDTH - curveDepth - curveDepth);
      
      let x1, x2, labelX, anchor;
      if (isMobile) {
        x2 = VISIBLE_WIDTH - curveDepth + curveX * 0.5;
        x1 = x2 - TICK_LENGTH;
        labelX = x1 - 4;
        anchor = 'end';
      } else {
        x1 = curveDepth - curveX * 0.3;
        x2 = x1 + TICK_LENGTH;
        labelX = x2 + 4;
        anchor = 'start';
      }
      
      const isCurrent = e === currentEntry && currentDist < 150;
      const tickClass = isCurrent ? 'disc-tick current' : 'disc-tick';

      content += `<line class="${tickClass}" data-id="${e.slice.id}" data-year="${e.year}" x1="${x1}" y1="${elY}" x2="${x2}" y2="${elY}" />`;

      // Year label  
      const yearText = typeof window.formatYear === 'function' ? window.formatYear(e.year) : e.year;
      const labelClass = isCurrent ? 'disc-label current' : 'disc-label';
      content += `<text class="${labelClass}" x="${labelX}" y="${elY + 4}" text-anchor="${anchor}">${yearText}</text>`;
    });

    // Needle at center
    if (isMobile) {
      content += `<line class="disc-needle" x1="${VISIBLE_WIDTH - 30}" y1="${centerY}" x2="${VISIBLE_WIDTH}" y2="${centerY}" />`;
    } else {
      content += `<line class="disc-needle" x1="0" y1="${centerY}" x2="30" y2="${centerY}" />`;
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
