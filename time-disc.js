/**
 * Time Disc Navigator
 * 
 * A large semicircular disc, mostly off-screen.
 * Only a thin arc is visible at the screen edge.
 * Ticks scroll around the arc as page scrolls.
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

  const VISIBLE_WIDTH = 30; // How much of disc edge is visible

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
    
    // Disc radius - large enough that visible arc spans most of viewport
    const DISC_RADIUS = viewportHeight * 0.9;
    const TICK_LENGTH = 15;
    
    // SVG dimensions
    const svgWidth = VISIBLE_WIDTH + 20;
    const svgHeight = viewportHeight;
    
    // Disc center is off-screen
    const cx = isMobile ? svgWidth + DISC_RADIUS - VISIBLE_WIDTH : -DISC_RADIUS + VISIBLE_WIDTH;
    const cy = viewportHeight / 2;
    
    svg.setAttribute('width', svgWidth);
    svg.setAttribute('height', svgHeight);
    svg.setAttribute('viewBox', `0 0 ${svgWidth} ${svgHeight}`);

    let content = '';

    // Draw the visible arc of the disc
    // Arc from top to bottom of viewport
    const arcTop = cy - DISC_RADIUS * 0.95;
    const arcBottom = cy + DISC_RADIUS * 0.95;
    
    // Calculate arc angles
    const topAngle = Math.asin((arcTop - cy) / DISC_RADIUS);
    const bottomAngle = Math.asin((arcBottom - cy) / DISC_RADIUS);
    
    if (isMobile) {
      // Right side - arc curves left
      const x1 = cx + DISC_RADIUS * Math.cos(topAngle);
      const y1 = cy + DISC_RADIUS * Math.sin(topAngle);
      const x2 = cx + DISC_RADIUS * Math.cos(bottomAngle);
      const y2 = cy + DISC_RADIUS * Math.sin(bottomAngle);
      content += `<path class="disc-bg" d="M ${cx} ${cy} L ${x1} ${y1} A ${DISC_RADIUS} ${DISC_RADIUS} 0 0 0 ${x2} ${y2} Z" />`;
    } else {
      // Left side - arc curves right
      const x1 = cx + DISC_RADIUS * Math.cos(Math.PI - topAngle);
      const y1 = cy - DISC_RADIUS * Math.sin(Math.PI - topAngle);
      const x2 = cx + DISC_RADIUS * Math.cos(Math.PI - bottomAngle);
      const y2 = cy - DISC_RADIUS * Math.sin(Math.PI - bottomAngle);
      content += `<path class="disc-bg" d="M ${cx} ${cy} L ${x1} ${y1} A ${DISC_RADIUS} ${DISC_RADIUS} 0 0 1 ${x2} ${y2} Z" />`;
    }

    let currentEntry = null;
    let currentDist = Infinity;

    // Find current entry
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

    // Draw ticks
    entries.forEach(e => {
      if (!e.el) return;
      
      const rect = e.el.getBoundingClientRect();
      const elCenterY = rect.top + rect.height / 2;
      
      // Skip if way off screen
      if (elCenterY < -200 || elCenterY > viewportHeight + 200) return;
      
      // Map Y position to angle on the arc
      const yOffset = elCenterY - cy;
      const angle = Math.asin(Math.max(-0.99, Math.min(0.99, yOffset / DISC_RADIUS)));
      
      // Tick coordinates
      const innerR = DISC_RADIUS - TICK_LENGTH;
      const outerR = DISC_RADIUS - 2;
      
      let x1, y1, x2, y2, labelX, labelY, textAngle;
      
      if (isMobile) {
        x1 = cx + innerR * Math.cos(angle);
        y1 = cy + innerR * Math.sin(angle);
        x2 = cx + outerR * Math.cos(angle);
        y2 = cy + outerR * Math.sin(angle);
        labelX = cx + (innerR - 15) * Math.cos(angle);
        labelY = cy + (innerR - 15) * Math.sin(angle);
        textAngle = (angle * 180 / Math.PI);
      } else {
        const drawAngle = Math.PI - angle;
        x1 = cx + innerR * Math.cos(drawAngle);
        y1 = cy - innerR * Math.sin(drawAngle);
        x2 = cx + outerR * Math.cos(drawAngle);
        y2 = cy - outerR * Math.sin(drawAngle);
        labelX = cx + (innerR - 15) * Math.cos(drawAngle);
        labelY = cy - (innerR - 15) * Math.sin(drawAngle);
        textAngle = (-angle * 180 / Math.PI);
      }
      
      const isCurrent = e === currentEntry && currentDist < 150;
      const tickClass = isCurrent ? 'disc-tick current' : 'disc-tick';

      content += `<line class="${tickClass}" data-id="${e.slice.id}" data-year="${e.year}" x1="${x1}" y1="${y1}" x2="${x2}" y2="${y2}" />`;

      // Year label
      const yearText = typeof window.formatYear === 'function' ? window.formatYear(e.year) : e.year;
      const labelClass = isCurrent ? 'disc-label current' : 'disc-label';
      content += `<text class="${labelClass}" x="${labelX}" y="${labelY}" text-anchor="middle" dominant-baseline="middle" transform="rotate(${textAngle}, ${labelX}, ${labelY})">${yearText}</text>`;
    });

    // Needle at center
    const needleY = cy;
    if (isMobile) {
      content += `<line class="disc-needle" x1="${svgWidth - VISIBLE_WIDTH - 5}" y1="${needleY}" x2="${svgWidth}" y2="${needleY}" />`;
    } else {
      content += `<line class="disc-needle" x1="0" y1="${needleY}" x2="${VISIBLE_WIDTH + 5}" y2="${needleY}" />`;
    }

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
