/**
 * Time Disc Navigator
 * Vertical timeline scrubber on the screen edge
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
  const PADDING_TOP = 120;
  const PADDING_BOTTOM = 120;

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
    const minYear = parseInt(sorted[0].year);
    const maxYear = parseInt(sorted[sorted.length - 1].year);
    const yearSpan = maxYear - minYear || 1;

    const height = window.innerHeight;
    const isMobile = window.innerWidth <= 768;
    const usableHeight = height - PADDING_TOP - PADDING_BOTTOM;

    // Set SVG dimensions explicitly
    svg.setAttribute('width', STRIP_WIDTH);
    svg.setAttribute('height', height);
    svg.setAttribute('viewBox', `0 0 ${STRIP_WIDTH} ${height}`);
    svg.style.width = STRIP_WIDTH + 'px';
    svg.style.height = height + 'px';

    let content = '';

    // Background
    content += `<rect class="disc-bg" x="0" y="0" width="${STRIP_WIDTH}" height="${height}" />`;

    // Build entries
    entries = [];

    sorted.forEach(slice => {
      const year = parseInt(slice.year);
      const t = (year - minYear) / yearSpan;
      const y = PADDING_TOP + t * usableHeight;

      // Tick mark
      const x1 = isMobile ? 0 : STRIP_WIDTH - TICK_WIDTH;
      const x2 = isMobile ? TICK_WIDTH : STRIP_WIDTH;

      content += `<line class="disc-tick" data-id="${slice.id}" data-year="${year}" x1="${x1}" y1="${y}" x2="${x2}" y2="${y}" />`;

      // Year label
      const labelX = isMobile ? TICK_WIDTH + 6 : STRIP_WIDTH - TICK_WIDTH - 6;
      const anchor = isMobile ? 'start' : 'end';
      const yearText = typeof window.formatYear === 'function' ? window.formatYear(year) : year;
      
      content += `<text class="disc-label" data-year="${year}" x="${labelX}" y="${y + 4}" text-anchor="${anchor}">${yearText}</text>`;

      entries.push({
        year,
        y,
        t,
        slice,
        el: null // Will be set after DOM query
      });
    });

    // Center needle
    const needleY = height / 2;
    content += `<line class="disc-needle" x1="0" y1="${needleY}" x2="${STRIP_WIDTH}" y2="${needleY}" />`;

    svg.innerHTML = content;

    // Store refs after DOM is updated
    entries.forEach(e => {
      e.el = document.querySelector(`#entry-${e.slice.id}`);
      e.tickEl = svg.querySelector(`.disc-tick[data-year="${e.year}"]`);
      e.labelEl = svg.querySelector(`.disc-label[data-year="${e.year}"]`);
    });

    updateHighlight();
  }

  function updateHighlight() {
    const viewportCenter = window.innerHeight / 2;
    let closest = null;
    let closestDist = Infinity;

    entries.forEach(e => {
      if (!e.el || e.el.classList.contains('thread-hidden')) return;
      const rect = e.el.getBoundingClientRect();
      const dist = Math.abs(rect.top + rect.height / 2 - viewportCenter);
      if (dist < closestDist) {
        closestDist = dist;
        closest = e;
      }
    });

    entries.forEach(e => {
      const isCurrent = e === closest;
      if (e.tickEl) e.tickEl.classList.toggle('current', isCurrent);
      if (e.labelEl) e.labelEl.classList.toggle('current', isCurrent);
    });

    if (closest && yearDisplay) {
      const yearText = typeof window.formatYear === 'function' ? window.formatYear(closest.year) : closest.year;
      yearDisplay.textContent = yearText;
    }
  }

  function scrollToY(clientY) {
    const height = window.innerHeight;
    const t = Math.max(0, Math.min(1, (clientY - PADDING_TOP) / (height - PADDING_TOP - PADDING_BOTTOM)));
    const maxScroll = document.documentElement.scrollHeight - window.innerHeight;
    window.scrollTo({ top: t * maxScroll, behavior: 'auto' });
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
      updateHighlight();
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

  // Scroll sync
  let scrollTimer = null;
  window.addEventListener('scroll', () => {
    if (!scrollSyncEnabled || isDragging) return;
    if (scrollTimer) return;
    scrollTimer = setTimeout(() => {
      scrollTimer = null;
      if (!container.classList.contains('hidden')) updateHighlight();
    }, 50);
  }, { passive: true });

  // Resize
  let resizeTimer = null;
  window.addEventListener('resize', () => {
    clearTimeout(resizeTimer);
    resizeTimer = setTimeout(build, 200);
  });

  // Export build function globally
  window.buildTimeDisc = build;
  window.showTimeDisc = () => container.classList.remove('hidden');
  window.hideTimeDisc = () => container.classList.add('hidden');

  // Initialize drag handlers immediately
  initDrag();

  // Try to build now if SLICES already exists
  if (window.SLICES && window.SLICES.length) {
    build();
  }

})();
