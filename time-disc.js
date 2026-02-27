/**
 * Time Disc Navigator
 * A rotatable disc widget for navigating Time Slices
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

  let discEntries = [];
  let discRotation = 0;
  let discIsDragging = false;
  let discDragStartY = 0;
  let discDragStartRotation = 0;
  let discLastNeedleEntry = null;
  let discScrollSyncEnabled = true;

  // Geometry - smaller radius for tighter curve visibility
  const DISC_RADIUS = 400;
  const VISIBLE_WIDTH = 28;
  const TICK_LENGTH = 14;

  function getRotationFromScroll() {
    const scrollTop = window.scrollY;
    const maxScroll = document.documentElement.scrollHeight - window.innerHeight;
    if (maxScroll <= 0) return 0;
    return (scrollTop / maxScroll) * 180;
  }

  function getScrollFromRotation(rotation) {
    const maxScroll = document.documentElement.scrollHeight - window.innerHeight;
    return (Math.max(0, Math.min(180, rotation)) / 180) * maxScroll;
  }

  function buildTimeDisc() {
    if (!window.SLICES || !window.SLICES.length) return;
    
    const entriesToShow = window.activeThread
      ? window.SLICES.filter(s => (s.threads || []).includes(window.activeThread))
      : window.SLICES;
    
    if (!entriesToShow.length) {
      discEntries = [];
      timeDiscSvg.innerHTML = '';
      return;
    }
    
    const sorted = [...entriesToShow].sort((a, b) => parseInt(a.year) - parseInt(b.year));
    const minYear = parseInt(sorted[0].year);
    const maxYear = parseInt(sorted[sorted.length - 1].year);
    const yearSpan = maxYear - minYear || 1;
    
    const isMobile = window.innerWidth <= 768;
    const viewportHeight = window.innerHeight;
    
    // SVG dimensions
    const svgSize = DISC_RADIUS * 2;
    
    // Center position - disc center is off-screen
    // For left edge: center is at x = -DISC_RADIUS + VISIBLE_WIDTH
    // For right edge: center is at x = svgSize + DISC_RADIUS - VISIBLE_WIDTH
    const centerX = DISC_RADIUS;
    const centerY = DISC_RADIUS;
    
    timeDiscSvg.setAttribute('width', svgSize);
    timeDiscSvg.setAttribute('height', svgSize);
    timeDiscSvg.setAttribute('viewBox', `0 0 ${svgSize} ${svgSize}`);
    
    // Position disc - offset so only edge shows
    timeDisc.style.width = svgSize + 'px';
    timeDisc.style.height = svgSize + 'px';
    
    if (isMobile) {
      // Right side: shift right so only left edge of disc shows
      timeDisc.style.left = 'auto';
      timeDisc.style.right = (-DISC_RADIUS + VISIBLE_WIDTH) + 'px';
    } else {
      // Left side: shift left so only right edge of disc shows
      timeDisc.style.left = (-DISC_RADIUS + VISIBLE_WIDTH) + 'px';
      timeDisc.style.right = 'auto';
    }
    
    // Build SVG
    let svgContent = '';
    
    // Solid disc background
    svgContent += `<circle class="disc-bg" cx="${centerX}" cy="${centerY}" r="${DISC_RADIUS}" />`;
    
    // Entry markers around the edge
    discEntries = [];
    
    sorted.forEach((slice) => {
      const year = parseInt(slice.year);
      const t = (year - minYear) / yearSpan;
      
      // Angle: entries go from -90° (top) to +90° (bottom)
      // For left-edge disc: right side is visible, so 0° points right
      // For right-edge disc: left side is visible, so 180° points left
      const baseAngle = isMobile ? (90 - t * 180) : (-90 + t * 180);
      const angleRad = (baseAngle * Math.PI) / 180;
      
      // Tick at edge
      const x1 = centerX + (DISC_RADIUS - TICK_LENGTH) * Math.cos(angleRad);
      const y1 = centerY + (DISC_RADIUS - TICK_LENGTH) * Math.sin(angleRad);
      const x2 = centerX + (DISC_RADIUS - 2) * Math.cos(angleRad);
      const y2 = centerY + (DISC_RADIUS - 2) * Math.sin(angleRad);
      
      svgContent += `<line class="disc-entry-tick" data-year="${year}" data-id="${slice.id}" x1="${x1}" y1="${y1}" x2="${x2}" y2="${y2}" />`;
      
      // Year label
      const labelR = DISC_RADIUS - TICK_LENGTH - 18;
      const labelX = centerX + labelR * Math.cos(angleRad);
      const labelY = centerY + labelR * Math.sin(angleRad);
      const yearText = typeof window.formatYear === 'function' ? window.formatYear(year) : year;
      
      // Rotate text to be readable
      let textAngle = baseAngle;
      if (!isMobile && (textAngle < -90 || textAngle > 90)) textAngle += 180;
      if (isMobile && (textAngle < -90 || textAngle > 90)) textAngle += 180;
      
      svgContent += `<text class="disc-year-label" data-year="${year}" x="${labelX}" y="${labelY}" 
        text-anchor="middle" dominant-baseline="middle" 
        transform="rotate(${textAngle}, ${labelX}, ${labelY})">${yearText}</text>`;
      
      discEntries.push({
        year,
        angle: baseAngle,
        t,
        slice,
        entryEl: document.querySelector(`#entry-${slice.id}`)
      });
    });
    
    timeDiscSvg.innerHTML = svgContent;
    
    // Store refs
    discEntries.forEach(entry => {
      entry.tickEl = timeDiscSvg.querySelector(`.disc-entry-tick[data-year="${entry.year}"]`);
      entry.labelEl = timeDiscSvg.querySelector(`.disc-year-label[data-year="${entry.year}"]`);
    });
    
    // Initial state
    discRotation = getRotationFromScroll();
    applyRotation();
    updateIndicator();
  }

  function applyRotation() {
    const isMobile = window.innerWidth <= 768;
    // Rotate disc - negative for desktop (clockwise = scroll down), positive for mobile
    const rotDir = isMobile ? 1 : -1;
    timeDisc.style.transform = `rotate(${rotDir * discRotation}deg)`;
  }

  function updateIndicator() {
    const isMobile = window.innerWidth <= 768;
    
    // Find entry at needle (needle is at 0° = horizontal right for desktop, horizontal left for mobile)
    // After rotation, entry at needle has: entry.angle + rotation ≈ 0 (desktop) or entry.angle - rotation ≈ 0 (mobile)
    let closest = null;
    let closestDist = Infinity;
    
    discEntries.forEach(entry => {
      const visualAngle = isMobile 
        ? entry.angle + discRotation 
        : entry.angle + discRotation;
      const dist = Math.abs(visualAngle);
      
      if (dist < closestDist) {
        closestDist = dist;
        closest = entry;
      }
    });
    
    if (closest && timeDiscYearEl) {
      const yearText = typeof window.formatYear === 'function' ? window.formatYear(closest.year) : closest.year;
      timeDiscYearEl.textContent = yearText;
    }
    
    discEntries.forEach(entry => {
      const isAtNeedle = entry === closest;
      if (entry.tickEl) entry.tickEl.classList.toggle('at-needle', isAtNeedle);
      if (entry.labelEl) entry.labelEl.classList.toggle('at-needle', isAtNeedle);
    });
    
    if (discIsDragging && closest !== discLastNeedleEntry && navigator.vibrate) {
      navigator.vibrate(10);
    }
    discLastNeedleEntry = closest;
  }

  function scrollToRotation(rotation) {
    window.scrollTo({ top: getScrollFromRotation(rotation), behavior: 'auto' });
  }

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
      
      // Dragging down = more rotation = scroll down
      // Sensitivity: 400px drag = full 180° rotation
      const rotationDelta = (deltaY / 400) * 180;
      discRotation = Math.max(0, Math.min(180, discDragStartRotation + rotationDelta));
      
      applyRotation();
      updateIndicator();
      scrollToRotation(discRotation);
    }
    
    function onDragEnd() {
      if (!discIsDragging) return;
      discIsDragging = false;
      timeDiscContainer.classList.remove('active');
      timeDisc.classList.remove('dragging');
      
      setTimeout(() => { discScrollSyncEnabled = true; }, 300);
    }
    
    timeDiscContainer.addEventListener('mousedown', onDragStart);
    document.addEventListener('mousemove', onDragMove);
    document.addEventListener('mouseup', onDragEnd);
    
    timeDiscContainer.addEventListener('touchstart', onDragStart, { passive: false });
    document.addEventListener('touchmove', onDragMove, { passive: false });
    document.addEventListener('touchend', onDragEnd);
    
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

  // Scroll sync
  let scrollTimer = null;
  window.addEventListener('scroll', () => {
    if (!discScrollSyncEnabled || discIsDragging) return;
    if (scrollTimer) return;
    
    scrollTimer = setTimeout(() => {
      scrollTimer = null;
      if (!timeDiscContainer.classList.contains('hidden')) {
        discRotation = getRotationFromScroll();
        applyRotation();
        updateIndicator();
      }
    }, 16);
  }, { passive: true });

  // Resize
  let resizeTimer = null;
  window.addEventListener('resize', () => {
    clearTimeout(resizeTimer);
    resizeTimer = setTimeout(buildTimeDisc, 200);
  });

  // Exports
  window.buildTimeDisc = buildTimeDisc;
  window.showTimeDisc = function() { timeDiscContainer.classList.remove('hidden'); };
  window.hideTimeDisc = function() { timeDiscContainer.classList.add('hidden'); };

  // Init
  if (window.slicesReady) {
    window.slicesReady.then(() => { buildTimeDisc(); initDiscDrag(); });
  } else {
    document.addEventListener('DOMContentLoaded', () => {
      setTimeout(() => { buildTimeDisc(); initDiscDrag(); }, 500);
    });
  }

})();
