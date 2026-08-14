/* ============================================================
   CETIN HTML DECK — ENGINE
   Inline this whole file inside <script> at the end of <body>.
   Features: fixed-stage scaling · slide-right transition · deep links (#N)
             chapter roll-over · video hand-off · edit mode · save-as-copy
   ============================================================ */
(function () {
  'use strict';

  var stage   = document.getElementById('stage');
  var slides  = Array.prototype.slice.call(document.querySelectorAll('.slide'));
  var rail    = document.getElementById('rail');
  var posEl   = document.getElementById('pos');
  var hint    = document.getElementById('hint');
  var current = 0;
  var nextBtn = null;          /* declared before paint() uses it */
  var animating = false;

  /* --- 1. Scale the fixed stage uniformly (letterbox, never reflow) --- */
  function fitStage() {
    var vw = window.innerWidth, vh = window.innerHeight;
    var scale = Math.min(vw / 1920, vh / 1080);
    stage.style.transform = 'translate(' + ((vw - 1920 * scale) / 2) + 'px,' +
                            ((vh - 1080 * scale) / 2) + 'px) scale(' + scale + ')';
  }
  window.addEventListener('resize', fitStage);
  fitStage();

  /* --- 2. Paint state --- */
  function writeHash() {
    try { window.history.replaceState(null, '', '#' + (current + 1)); } catch (e) { /* file:// */ }
  }
  function paint() {
    posEl.textContent = (current + 1) + ' / ' + slides.length;
    rail.style.width = ((current + 1) / slides.length * 100) + '%';
    if (nextBtn) { nextBtn.classList.toggle('on', current === slides.length - 1); }
    writeHash();
  }

  /* --- 3. Transition --- */
  function show(idx, dir) {
    if (idx < 0 || idx >= slides.length || idx === current || animating) { return; }
    animating = true;
    var outgoing = slides[current], incoming = slides[idx];

    /* audio must not run on over the next slide */
    outgoing.querySelectorAll('video').forEach(function (v) { if (!v.paused) { v.pause(); } });

    incoming.classList.remove('active', 'exit-left', 'exit-right', 'stage-left');
    incoming.style.transition = 'none';
    if (dir < 0) { incoming.classList.add('stage-left'); }
    void incoming.offsetWidth;                 /* commit the parked position */
    incoming.style.transition = '';

    incoming.querySelectorAll('.anim').forEach(function (el) {
      if (el.tagName === 'VIDEO') { return; }  /* restarting this flickers the frame */
      el.style.animation = 'none'; void el.offsetWidth; el.style.animation = '';
    });

    outgoing.classList.remove('active');
    outgoing.classList.add(dir > 0 ? 'exit-left' : 'exit-right');
    incoming.classList.remove('stage-left');
    incoming.classList.add('active');

    current = idx; paint();
    setTimeout(function () {
      outgoing.classList.remove('exit-left', 'exit-right');
      animating = false;
    }, 640);
  }

  /* --- 4. Chapter roll-over: the decks are split per chapter --- */
  var NAV = window.DECK_NAV || {};
  if (NAV.nextFile || NAV.isLast) {
    nextBtn = document.createElement('a');
    nextBtn.className = 'next-ch';
    nextBtn.href = NAV.nextFile || 'index.html';
    nextBtn.innerHTML =
      '<span class="nc-txt">' + (NAV.nextFile ? 'Next chapter' : 'Back to contents') +
      (NAV.nextLabel ? '<span class="nc-sub">' + NAV.nextLabel + '</span>' : '') + '</span>' +
      '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" ' +
      'stroke-linecap="round" stroke-linejoin="round"><path d="M5 12h13"/><path d="M13 6l6 6-6 6"/></svg>';
    document.body.appendChild(nextBtn);
  }
  function nextSlide() {
    if (current === slides.length - 1) {
      window.location.href = NAV.nextFile || 'index.html'; return;
    }
    show(current + 1, 1);
  }
  function prevSlide() {
    if (current === 0) { if (NAV.prevFile) { window.location.href = NAV.prevFile; } return; }
    show(current - 1, -1);
  }
  document.getElementById('next').addEventListener('click', nextSlide);
  document.getElementById('prev').addEventListener('click', prevSlide);

  /* --- 5. Keyboard --- */
  document.addEventListener('keydown', function (e) {
    if (document.body.classList.contains('editing') && e.target && e.target.isContentEditable) { return; }
    if (e.target && e.target.tagName === 'VIDEO') { return; }   /* let the video own Space */
    switch (e.key) {
      case 'ArrowRight': case ' ': case 'PageDown': e.preventDefault(); nextSlide(); break;
      case 'ArrowLeft':  case 'PageUp':             e.preventDefault(); prevSlide(); break;
      case 'Home': show(0, -1); break;
      case 'End':  show(slides.length - 1, 1); break;
      case 'e': case 'E': toggleEdit(); break;
    }
  });

  /* --- 6. Touch: swipe left = forward --- */
  var tx = 0, ty = 0;
  document.addEventListener('touchstart', function (e) {
    tx = e.changedTouches[0].clientX; ty = e.changedTouches[0].clientY;
  }, { passive: true });
  document.addEventListener('touchend', function (e) {
    var dx = e.changedTouches[0].clientX - tx, dy = e.changedTouches[0].clientY - ty;
    if (Math.abs(dx) > 55 && Math.abs(dx) > Math.abs(dy)) { dx < 0 ? nextSlide() : prevSlide(); }
  }, { passive: true });

  /* --- 7. Edit mode (browser only) --- */
  function toggleEdit() {
    var on = document.body.classList.toggle('editing');
    var sel = 'h1, .lede, .cbody, .chead, .cs, .ch, .sl, .sv, .callout, .tl-label, .ed, ' +
              '.div-sub, .title-sub, .ag, .bullets li, td, .vq, .db, .at, .dt, .dd';
    slides.forEach(function (s) {
      s.querySelectorAll(sel).forEach(function (el) { el.contentEditable = on ? 'true' : 'false'; });
    });
    hint.textContent = on
      ? 'EDIT MODE — click any text · ⌘/Ctrl+S downloads an edited copy · E to exit'
      : '← → to navigate · E to edit';
    hint.style.opacity = 1;
  }

  /* --- 8. Save: contenteditable only changes the live page, so serialise and download --- */
  document.addEventListener('keydown', function (e) {
    if (!((e.metaKey || e.ctrlKey) && (e.key === 's' || e.key === 'S'))) { return; }
    e.preventDefault();
    var clone = document.documentElement.cloneNode(true);
    clone.querySelectorAll('[contenteditable]').forEach(function (el) { el.removeAttribute('contenteditable'); });
    var cb = clone.querySelector('body'); if (cb) { cb.classList.remove('editing'); }
    clone.querySelectorAll('.slide').forEach(function (s) {
      s.removeAttribute('style');
      s.classList.remove('active', 'exit-left', 'exit-right', 'stage-left');
    });
    clone.querySelectorAll('.anim').forEach(function (el) { el.removeAttribute('style'); });
    var cs = clone.querySelector('#stage'); if (cs) { cs.removeAttribute('style'); }
    var name = (window.location.pathname.split('/').pop() || 'deck').replace(/\.html?$/i, '') + '-edited.html';
    var url = URL.createObjectURL(new Blob(['<!DOCTYPE html>\n' + clone.outerHTML], { type: 'text/html' }));
    var a = document.createElement('a'); a.href = url; a.download = name;
    document.body.appendChild(a); a.click(); a.remove();
    setTimeout(function () { URL.revokeObjectURL(url); }, 4000);
    hint.textContent = 'SAVED AS ' + name.toUpperCase(); hint.style.opacity = 1;
    setTimeout(function () { hint.style.opacity = 0; }, 4200);
  });

  setTimeout(function () {
    if (!document.body.classList.contains('editing')) { hint.style.opacity = 0; }
  }, 5200);

  /* --- 9. Deep linking: file.html#9 opens slide 9 --- */
  function hashIndex() {
    var m = /^#s?(\d+)$/.exec(window.location.hash || '');
    if (!m) { return 0; }
    var i = parseInt(m[1], 10) - 1;
    return (i >= 0 && i < slides.length) ? i : 0;
  }
  window.addEventListener('hashchange', function () {
    var i = hashIndex();
    if (i !== current) { show(i, i > current ? 1 : -1); }
  });
  function jump(idx) {
    slides.forEach(function (s, i) {
      s.style.transition = 'none';
      s.classList.remove('active', 'exit-left', 'exit-right', 'stage-left');
      if (i < idx) { s.classList.add('stage-left'); }
    });
    slides[idx].classList.add('active');
    void slides[idx].offsetWidth;
    slides.forEach(function (s) { s.style.transition = ''; });
    current = idx; paint();
  }
  jump(hashIndex());
})();
