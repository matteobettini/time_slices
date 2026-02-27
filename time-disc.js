/**
 * Time Disc Navigator
 * A scrollbar-like time navigation widget for Time Slices
 * 
 * Dependencies: Expects these globals from index.html:
 * - SLICES: array of slice objects
 * - activeThread: current thread filter (or null)
 * - slicesReady: Promise that resolves when slices are loaded
 * - formatYear: function to format year numbers
 * - highlightAndScroll: function to scroll to and highlight an entry
 */

(function() {
  'use strict';

  const timeDiscContainer = document.getElementById('timeDiscContainer');
  const timeDisc = document.getElementById('timeDisc');
  const timeDiscSvg = document.getElementById('timeDiscSvg');
  const timeDiscYearEl = document.getElementById('timeDiscYear');

  if (!timeDiscContainer || !timeDisc || !timeDiscSvg) {
    console.warn('Time Disc: required elements not found');
    return;
  }

  let discEntries = []; // { year, angle, slice, tickEl, labelEl, entryEl }
  let discIsDragging = false;
  let discDragStartY = 0;
  let discLastNeedleEntry = null;
  let discScrollSyncEnabled = true;

  // Disc geometry - large disc, only edge visible
  const DISC_RADIUS = 2000; // Large radius so visible edge is nearly straight
  const DISC_VISIBLE = 20; // How much of disc edge is visible (px)
  const TICK_LENGTH = 12;
  const LABEL_OFFSET = 24;

  function buildTimeDisc() {
    if (!window.SLICES || !window.SLICES.length) return;
    
    // Get entries to show (filtered by thread if active)
    const entriesToShow = window.activeThread
      ? window.SLICES.filter(s => (s.threads || []).includes(window.activeThread))
      : window.SLICES;
    
    if (!entriesToShow.length) {
      discEntries = [];
      timeDiscSvg.innerHTML = '';
      return;
    }
    
    // Sort by year
    const sorted = [...entriesToShow].sort((a, b) => parseInt(a.year) - parseInt(b.year));
    const minYear = parseInt(sorted[0].year);
    const maxYear = parseInt(sorted[sorted.length - 1].year);
    const yearSpan = maxYear - minYear || 1;
    
    // Calculate viewport height for scaling
    const viewportHeight = window.innerHeight;
    const isMobile = window.innerWidth <= 768;
    
    // SVG dimensions - disc center is off-screen
    const svgWidth = DISC_VISIBLE + LABEL_OFFSET + 50;
    const svgHeight = viewportHeight;
    const centerX = isMobile ? svgWidth + DISC_RADIUS - DISC_VISIBLE : -DISC_RADIUS + DISC_VISIBLE;
    const centerY = svgHeight / 2;
    
    // Set up SVG
    timeDiscSvg.setAttribute('width', svgWidth);
    timeDiscSvg.setAttribute('height', svgHeight);
    timeDiscSvg.setAttribute('viewBox', `0 0 ${svgWidth} ${svgHeight}`);
    
    // Position disc element
    timeDisc.style.width = svgWidth + 'px';
    timeDisc.style.height = svgHeight + 'px';
    timeDisc.style.transform = 'translateY(-50%)';
    
    // Build SVG content
    let svgContent = '';
    
    // Disc background arc (the visible slice)
    const arcAngleSpan = (viewportHeight / (2 * Math.PI * DISC_RADIUS)) * 360 * 1.2;
    const startAngle = isMobile ? 180 - arcAngleSpan/2 : -arcAngleSpan/2;
    const endAngle = isMobile ? 180 + arcAngleSpan/2 : arcAngleSpan/2;
    
    // Draw arc background
    const arcStartRad = (startAngle * Math.PI) / 180;
    const arcEndRad = (endAngle * Math.PI) / 180;
    const arcX1 = centerX + DISC_RADIUS * Math.cos(arcStartRad);
    const arcY1 = centerY + DISC_RADIUS * Math.sin(arcStartRad);
    const arcX2 = centerX + DISC_RADIUS * Math.cos(arcEndRad);
    const arcY2 = centerY + DISC_RADIUS * Math.sin(arcEndRad);
    
    svgContent += `<path class="disc-bg" d="M ${centerX} ${centerY} L ${arcX1} ${arcY1} A ${DISC_RADIUS} ${DISC_RADIUS} 0 0 1 ${arcX2} ${arcY2} Z" />`;
    
    // Map entries to angles spanning the visible viewport
    discEntries = [];
    
    sorted.forEach((slice) => {
      const year = parseInt(slice.year);
      const t = (year - minYear) / yearSpan; // 0 to 1
      
      // Map to Y position on screen (with padding)
      const padding = 80;
      const yPos = padding + t * (viewportHeight - 2 * padding);
      
      // Convert Y position to angle on the disc
      const angleT = (yPos - padding) / (viewportHeight - 2 * padding);
      const angle = isMobile 
        ? 180 - arcAngleSpan/2 + angleT * arcAngleSpan
        : -arcAngleSpan/2 + angleT * arcAngleSpan;
      
      const angleRad = (angle * Math.PI) / 180;
      
      // Tick mark coordinates
      const innerR = DISC_RADIUS - TICK_LENGTH;
      const outerR = DISC_RADIUS;
      const x1 = centerX + innerR * Math.cos(angleRad);
      const y1 = centerY + innerR * Math.sin(angleRad);
      const x2 = centerX + outerR * Math.cos(angleRad);
      const y2 = centerY + outerR * Math.sin(angleRad);
      
      svgContent += `<line class="disc-entry-tick" data-year="${year}" data-id="${slice.id}" x1="${x1}" y1="${y1}" x2="${x2}" y2="${y2}" />`;
      
      // Year label - positioned outside the arc
      const labelR = DISC_RADIUS + 8;
      const labelX = centerX + labelR * Math.cos(angleRad);
      const labelY = centerY + labelR * Math.sin(angleRad);
      const textAnchor = isMobile ? 'end' : 'start';
      
      const yearText = typeof window.formatYear === 'function' ? window.formatYear(year) : year;
      svgContent += `<text class="disc-year-label" data-year="${year}" x="${labelX}" y="${labelY}" text-anchor="${textAnchor}" dominant-baseline="middle">${yearText}</text>`;
      
      discEntries.push({
        year,
        angle,
        yPos,
        slice,
        tickEl: null,
        labelEl: null,
        entryEl: document.querySelector(`#entry-${slice.id}`)
      });
    });
    
    timeDiscSvg.innerHTML = svgContent;
    
    // Store element references
    discEntries.forEach(entry => {
      entry.tickEl = timeDiscSvg.querySelector(`.disc-entry-tick[data-year="${entry.year}"]`);
      entry.labelEl = timeDiscSvg.querySelector(`.disc-year-label[data-year="${entry.year}"]`);
    });
    
    // Update indicator
    updateDiscIndicator();
  }

  function updateDiscIndicator() {
    // Find entry closest to center of viewport
    const viewportCenter = window.innerHeight / 2;
    let closest = null;
    let closestDist = Infinity;
    
    discEntries.forEach(entry => {
      if (!entry.entryEl) return;
      if (entry.entryEl.classList.contains('thread-hidden')) return;
      
      const rect = entry.entryEl.getBoundingClientRect();
      const entryCenter = rect.top + rect.height / 2;
      const dist = Math.abs(entryCenter - viewportCenter);
      
      if (dist < closestDist) {
        closestDist = dist;
        closest = entry;
      }
    });
    
    // Update year display
    if (closest && timeDiscYearEl) {
      const yearText = typeof window.formatYear === 'function' ? window.formatYear(closest.year) : closest.year;
      timeDiscYearEl.textContent = yearText;
      
      // Update tick/label highlighting
      discEntries.forEach(entry => {
        const isAtNeedle = entry === closest;
        if (entry.tickEl) entry.tickEl.classList.toggle('at-needle', isAtNeedle);
        if (entry.labelEl) entry.labelEl.classList.toggle('at-needle', isAtNeedle);
      });
      
      // Haptic on change during drag
      if (discIsDragging && closest !== discLastNeedleEntry && navigator.vibrate) {
        navigator.vibrate(10);
      }
      discLastNeedleEntry = closest;
    }
  }

  function scrollToDiscPosition(yPos) {
    // Find entry closest to this Y position
    let closest = null;
    let closestDist = Infinity;
    
    discEntries.forEach(entry => {
      const dist = Math.abs(entry.yPos - yPos);
      if (dist < closestDist) {
        closestDist = dist;
        closest = entry;
      }
    });
    
    if (closest && closest.entryEl) {
      // Calculate scroll position to bring this entry to viewport center
      const entryRect = closest.entryEl.getBoundingClientRect();
      const entryCenter = entryRect.top + entryRect.height / 2;
      const viewportCenter = window.innerHeight / 2;
      const scrollDelta = entryCenter - viewportCenter;
      
      window.scrollBy({ top: scrollDelta, behavior: 'auto' });
      updateDiscIndicator();
    }
  }

  // Drag handling - vertical drag to scroll
  function initDiscDrag() {
    function onDragStart(e) {
      discIsDragging = true;
      discScrollSyncEnabled = false;
      timeDiscContainer.classList.add('active');
      timeDisc.classList.add('dragging');
      
      const clientY = e.touches ? e.touches[0].clientY : e.clientY;
      discDragStartY = clientY;
    }
    
    function onDragMove(e) {
      if (!discIsDragging) return;
      e.preventDefault();
      
      const clientY = e.touches ? e.touches[0].clientY : e.clientY;
      
      // Scroll the page based on drag position
      scrollToDiscPosition(clientY);
    }
    
    function onDragEnd() {
      if (!discIsDragging) return;
      discIsDragging = false;
      timeDiscContainer.classList.remove('active');
      timeDisc.classList.remove('dragging');
      
      // Re-enable scroll sync after a delay
      setTimeout(() => {
        discScrollSyncEnabled = true;
      }, 300);
    }
    
    // Mouse events
    timeDiscContainer.addEventListener('mousedown', onDragStart);
    document.addEventListener('mousemove', onDragMove);
    document.addEventListener('mouseup', onDragEnd);
    
    // Touch events
    timeDiscContainer.addEventListener('touchstart', onDragStart, { passive: true });
    document.addEventListener('touchmove', onDragMove, { passive: false });
    document.addEventListener('touchend', onDragEnd);
    
    // Click on tick to jump to entry
    timeDiscSvg.addEventListener('click', (e) => {
      const tick = e.target.closest('.disc-entry-tick');
      if (tick) {
        const id = tick.dataset.id;
        const entry = document.querySelector(`#entry-${id}`);
        if (entry) {
          if (navigator.vibrate) navigator.vibrate(10);
          if (typeof window.highlightAndScroll === 'function') {
            window.highlightAndScroll(entry);
          } else {
            entry.scrollIntoView({ behavior: 'smooth', block: 'center' });
          }
        }
      }
    });
  }

  // Scroll listener (throttled)
  let discScrollTimer = null;
  window.addEventListener('scroll', () => {
    if (discScrollTimer || !discScrollSyncEnabled) return;
    discScrollTimer = setTimeout(() => {
      discScrollTimer = null;
      if (!timeDiscContainer.classList.contains('hidden')) {
        updateDiscIndicator();
      }
    }, 50);
  }, { passive: true });

  // Rebuild on resize (debounced)
  let discResizeTimer = null;
  window.addEventListener('resize', () => {
    clearTimeout(discResizeTimer);
    discResizeTimer = setTimeout(buildTimeDisc, 200);
  });

  // Export functions for integration with main app
  window.buildTimeDisc = buildTimeDisc;
  window.showTimeDisc = function() {
    timeDiscContainer.classList.remove('hidden');
  };
  window.hideTimeDisc = function() {
    timeDiscContainer.classList.add('hidden');
  };

  // Initialize after slices load
  if (window.slicesReady) {
    window.slicesReady.then(() => {
      buildTimeDisc();
      initDiscDrag();
    });
  } else {
    // Fallback: try to init on DOMContentLoaded
    document.addEventListener('DOMContentLoaded', () => {
      setTimeout(() => {
        buildTimeDisc();
        initDiscDrag();
      }, 500);
    });
  }

})();
