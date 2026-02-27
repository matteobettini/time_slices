/**
 * Time Disc Navigator - Complete Rewrite
 * 
 * Simple approach:
 * - A vertical strip on the left edge (right on mobile)
 * - Contains tick marks for each entry, positioned vertically by year
 * - Dragging up/down scrolls the page
 * - Current entry is highlighted
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
  let scrollSyncEnabled = true;

  const STRIP_WIDTH = 40;
  const TICK_WIDTH = 16;
  const PADDING_TOP = 100;
  const PADDING_BOTTOM = 100;

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
    const minYear = parseInt(sorted[0].year);
    const maxYear = parseInt(sorted[sorted.length - 1].year);
    const yearSpan = maxYear - minYear || 1;

    const height = window.innerHeight;
    const isMobile = window.innerWidth <= 768;

    // Set SVG size
    svg.setAttribute('width', STRIP_WIDTH);
    svg.setAttribute('height', height);
    svg.setAttribute('viewBox', `0 0 ${STRIP_WIDTH} ${height}`);

    // Build content
    let content = '';

    // Background strip
    content += `<rect class="disc-strip-bg" x="0" y="0" width="${STRIP_WIDTH}" height="${height}" />`;

    // Entries
    entries = [];
    const usableHeight = height - PADDING_TOP - PADDING_BOTTOM;

    sorted.forEach(slice => {
      const year = parseInt(slice.year);
      const t = (year - minYear) / yearSpan;
      const y = PADDING_TOP + t * usableHeight;

      // Tick mark
      const x1 = isMobile ? 0 : STRIP_WIDTH - TICK_WIDTH;
      const x2 = isMobile ? TICK_WIDTH : STRIP_WIDTH;

      content += `<line class="disc-tick" data-id="${slice.id}" data-year="${year}" 
        x1="${x1}" y1="${y}" x2="${x2}" y2="${y}" />`;

      // Year label (shown on hover)
      const labelX = isMobile ? TICK_WIDTH + 4 : STRIP_WIDTH - TICK_WIDTH - 4;
      const anchor = isMobile ? 'start' : 'end';

      const yearText = typeof window.formatYear === 'function' ? window.formatYear(year) : year;
      content += `<text class="disc-label" data-year="${year}" x="${labelX}" y="${y + 3}" 
        text-anchor="${anchor}">${yearText}</text>`;

      entries.push({
        year,
        y,
        t,
        slice,
        el: document.querySelector(`#entry-${slice.id}`)
      });
    });

    // Needle (center indicator line)
    const needleY = height / 2;
    const needleX1 = isMobile ? 0 : STRIP_WIDTH - TICK_WIDTH - 8;
    const needleX2 = isMobile ? TICK_WIDTH + 8 : STRIP_WIDTH;
    content += `<line class="disc-needle" x1="${needleX1}" y1="${needleY}" x2="${needleX2}" y2="${needleY}" />`;

    svg.innerHTML = content;

    // Store tick/label refs
    entries.forEach(e => {
      e.tickEl = svg.querySelector(`.disc-tick[data-year="${e.year}"]`);
      e.labelEl = svg.querySelector(`.disc-label[data-year="${e.year}"]`);
    });

    updateHighlight();
  }

  function updateHighlight() {
    // Find entry closest to viewport center
    const viewportCenter = window.innerHeight / 2;
    let closest = null;
    let closestDist = Infinity;

    entries.forEach(e => {
      if (!e.el) return;
      if (e.el.classList.contains('thread-hidden')) return;

      const rect = e.el.getBoundingClientRect();
      const dist = Math.abs(rect.top + rect.height / 2 - viewportCenter);

      if (dist < closestDist) {
        closestDist = dist;
        closest = e;
      }
    });

    // Update styling
    entries.forEach(e => {
      const isCurrent = e === closest;
      if (e.tickEl) e.tickEl.classList.toggle('current', isCurrent);
      if (e.labelEl) e.labelEl.classList.toggle('current', isCurrent);
    });

    // Update year display
    if (closest && yearDisplay) {
      const yearText = typeof window.formatYear === 'function' ? window.formatYear(closest.year) : closest.year;
      yearDisplay.textContent = yearText;
    }
  }

  function scrollToY(clientY) {
    // Map clientY to scroll position
    const height = window.innerHeight;
    const t = Math.max(0, Math.min(1, (clientY - PADDING_TOP) / (height - PADDING_TOP - PADDING_BOTTOM)));
    const maxScroll = document.documentElement.scrollHeight - window.innerHeight;
    const targetScroll = t * maxScroll;

    window.scrollTo({ top: targetScroll, behavior: 'auto' });
  }

  function initDrag() {
    function onStart(e) {
      isDragging = true;
      scrollSyncEnabled = false;
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

      // Direct positioning: finger position = scroll position
      scrollToY(clientY);
      updateHighlight();

      // Haptic feedback when passing entries
      const height = window.innerHeight;
      entries.forEach(entry => {
        const entryScreenY = entry.y;
        if (Math.abs(clientY - entryScreenY) < 10) {
          if (navigator.vibrate) navigator.vibrate(5);
        }
      });
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

    // Click on tick to jump
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
      if (!container.classList.contains('hidden')) {
        updateHighlight();
      }
    }, 50);
  }, { passive: true });

  // Resize
  let resizeTimer = null;
  window.addEventListener('resize', () => {
    clearTimeout(resizeTimer);
    resizeTimer = setTimeout(build, 200);
  });

  // Exports
  window.buildTimeDisc = build;
  window.showTimeDisc = () => container.classList.remove('hidden');
  window.hideTimeDisc = () => container.classList.add('hidden');

  // Init
  if (window.slicesReady) {
    window.slicesReady.then(() => { build(); initDrag(); });
  } else {
    document.addEventListener('DOMContentLoaded', () => {
      setTimeout(() => { build(); initDrag(); }, 500);
    });
  }

})();
