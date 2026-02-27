/**
 * Time Disc Navigator
 * A rotatable disc widget for navigating Time Slices
 * 
 * The disc rotates when dragged, and the page scrolls dynamically with it.
 * Entry markers are painted on the disc and rotate with it.
 * A fixed needle in the center indicates the current position.
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

  let discEntries = []; // { year, angle, slice, entryEl }
  let discRotation = 0; // Current rotation in degrees
  let discIsDragging = false;
  let discDragStartY = 0;
  let discDragStartRotation = 0;
  let discLastNeedleEntry = null;
  let discScrollSyncEnabled = true;
  let minYear = 0;
  let maxYear = 0;

  // Disc geometry
  const DISC_RADIUS = 800;
  const DISC_VISIBLE_WIDTH = 24;
  const TICK_LENGTH = 10;

  // Map scroll position to rotation (full page scroll = 180° rotation)
  function getRotationFromScroll() {
    const scrollTop = window.scrollY;
    const maxScroll = document.documentElement.scrollHeight - window.innerHeight;
    if (maxScroll <= 0) return 0;
    const t = scrollTop / maxScroll;
    return t * 180; // 0° to 180°
  }

  // Map rotation to scroll position
  function getScrollFromRotation(rotation) {
    const maxScroll = document.documentElement.scrollHeight - window.innerHeight;
    const t = Math.max(0, Math.min(180, rotation)) / 180;
    return t * maxScroll;
  }

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
    minYear = parseInt(sorted[0].year);
    maxYear = parseInt(sorted[sorted.length - 1].year);
    const yearSpan = maxYear - minYear || 1;
    
    const isMobile = window.innerWidth <= 768;
    
    // SVG setup - we draw a large circle, mostly off-screen
    const svgSize = DISC_RADIUS * 2 + 100;
    const centerX = isMobile ? svgSize - DISC_VISIBLE_WIDTH : DISC_VISIBLE_WIDTH;
    const centerY = svgSize / 2;
    
    timeDiscSvg.setAttribute('width', svgSize);
    timeDiscSvg.setAttribute('height', svgSize);
    timeDiscSvg.setAttribute('viewBox', `0 0 ${svgSize} ${svgSize}`);
    
    // Position the disc so only the edge is visible
    const discLeft = isMobile ? -(svgSize - DISC_VISIBLE_WIDTH - 50) : -(svgSize - DISC_VISIBLE_WIDTH - 50);
    timeDisc.style.width = svgSize + 'px';
    timeDisc.style.height = svgSize + 'px';
    timeDisc.style.marginLeft = (isMobile ? '' : discLeft + 'px');
    timeDisc.style.marginRight = (isMobile ? discLeft + 'px' : '');
    
    // Build SVG content
    let svgContent = '';
    
    // Solid disc background
    svgContent += `<circle class="disc-bg" cx="${centerX}" cy="${centerY}" r="${DISC_RADIUS}" />`;
    
    // Entry markers - positioned around the disc edge
    // Entries span from -90° (top) to +90° (bottom) on the visible edge
    discEntries = [];
    
    sorted.forEach((slice) => {
      const year = parseInt(slice.year);
      const t = (year - minYear) / yearSpan; // 0 to 1
      
      // Map to angle: -90° (top) to +90° (bottom)
      const angle = -90 + t * 180;
      const angleRad = (angle * Math.PI) / 180;
      
      // Tick mark at the edge
      const innerR = DISC_RADIUS - TICK_LENGTH;
      const outerR = DISC_RADIUS - 1;
      const x1 = centerX + innerR * Math.cos(angleRad);
      const y1 = centerY + innerR * Math.sin(angleRad);
      const x2 = centerX + outerR * Math.cos(angleRad);
      const y2 = centerY + outerR * Math.sin(angleRad);
      
      svgContent += `<line class="disc-entry-tick" data-year="${year}" data-id="${slice.id}" x1="${x1}" y1="${y1}" x2="${x2}" y2="${y2}" />`;
      
      // Year label inside the disc
      const labelR = DISC_RADIUS - TICK_LENGTH - 20;
      const labelX = centerX + labelR * Math.cos(angleRad);
      const labelY = centerY + labelR * Math.sin(angleRad);
      
      const yearText = typeof window.formatYear === 'function' ? window.formatYear(year) : year;
      // Rotate text to follow the curve
      const textRotation = angle + (isMobile ? 180 : 0);
      svgContent += `<text class="disc-year-label" data-year="${year}" x="${labelX}" y="${labelY}" text-anchor="middle" dominant-baseline="middle" transform="rotate(${textRotation}, ${labelX}, ${labelY})">${yearText}</text>`;
      
      discEntries.push({
        year,
        angle,
        t, // 0-1 position in timeline
        slice,
        entryEl: document.querySelector(`#entry-${slice.id}`)
      });
    });
    
    timeDiscSvg.innerHTML = svgContent;
    
    // Store element references
    discEntries.forEach(entry => {
      entry.tickEl = timeDiscSvg.querySelector(`.disc-entry-tick[data-year="${entry.year}"]`);
      entry.labelEl = timeDiscSvg.querySelector(`.disc-year-label[data-year="${entry.year}"]`);
    });
    
    // Set initial rotation from current scroll
    discRotation = getRotationFromScroll();
    applyRotation();
    updateIndicator();
  }

  function applyRotation() {
    // The disc rotates around its center
    // Rotation maps: 0° scroll = disc at 0°, full scroll = disc at 180°
    timeDisc.style.transform = `rotate(${-discRotation}deg)`;
  }

  function updateIndicator() {
    // The needle is fixed at the center (pointing at 0° on the disc)
    // After rotation, find which entry is at the needle
    // Entry at needle: entry.angle + (-discRotation) ≈ 0
    // So: entry.angle ≈ discRotation
    
    let closest = null;
    let closestDist = Infinity;
    
    discEntries.forEach(entry => {
      // Entry's angle after rotation
      const visualAngle = entry.angle - discRotation;
      // Distance from 0° (the needle position)
      const dist = Math.abs(visualAngle);
      
      if (dist < closestDist) {
        closestDist = dist;
        closest = entry;
      }
    });
    
    // Update year display
    if (closest && timeDiscYearEl) {
      const yearText = typeof window.formatYear === 'function' ? window.formatYear(closest.year) : closest.year;
      timeDiscYearEl.textContent = yearText;
    }
    
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

  function scrollToRotation(rotation) {
    const targetScroll = getScrollFromRotation(rotation);
    window.scrollTo({ top: targetScroll, behavior: 'auto' });
  }

  // Drag handling
  function initDiscDrag() {
    function onDragStart(e) {
      discIsDragging = true;
      discScrollSyncEnabled = false;
      timeDiscContainer.classList.add('active');
      timeDisc.classList.add('dragging');
      
      const clientY = e.touches ? e.touches[0].clientY : e.clientY;
      discDragStartY = clientY;
      discDragStartRotation = discRotation;
      
      e.preventDefault();
    }
    
    function onDragMove(e) {
      if (!discIsDragging) return;
      e.preventDefault();
      
      const clientY = e.touches ? e.touches[0].clientY : e.clientY;
      const deltaY = clientY - discDragStartY;
      
      // Convert vertical drag to rotation
      // Dragging down = rotating forward (increasing rotation)
      // Scale: 500px drag = 180° rotation (full timeline)
      const rotationDelta = (deltaY / 500) * 180;
      
      discRotation = Math.max(0, Math.min(180, discDragStartRotation + rotationDelta));
      applyRotation();
      updateIndicator();
      
      // Scroll the page to match
      scrollToRotation(discRotation);
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
    timeDiscContainer.addEventListener('touchstart', onDragStart, { passive: false });
    document.addEventListener('touchmove', onDragMove, { passive: false });
    document.addEventListener('touchend', onDragEnd);
    
    // Click on tick to jump to entry
    timeDiscSvg.addEventListener('click', (e) => {
      if (discIsDragging) return;
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

  // Scroll listener - sync disc rotation with scroll
  let discScrollTimer = null;
  window.addEventListener('scroll', () => {
    if (!discScrollSyncEnabled) return;
    if (discScrollTimer) return;
    
    discScrollTimer = setTimeout(() => {
      discScrollTimer = null;
      if (!timeDiscContainer.classList.contains('hidden') && !discIsDragging) {
        discRotation = getRotationFromScroll();
        applyRotation();
        updateIndicator();
      }
    }, 16); // ~60fps
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
    document.addEventListener('DOMContentLoaded', () => {
      setTimeout(() => {
        buildTimeDisc();
        initDiscDrag();
      }, 500);
    });
  }

})();
