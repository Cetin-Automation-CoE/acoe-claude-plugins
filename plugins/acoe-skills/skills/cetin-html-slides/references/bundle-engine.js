/* ===========================================================
   SINGLE-FILE DECK ENGINE
   1. Injects the deduplicated images from window.IMAGES.
   2. Routes between the contents page (#home) and the deck (#N).
   3. Scales the fixed 1920x1080 stage and animates slide changes.
   =========================================================== */
(function () {
  'use strict';

  /* --- 1. images ------------------------------------------------------- */
  (function injectImages() {
    var map = window.IMAGES || {};
    document.querySelectorAll('[data-img]').forEach(function (el) {
      var uri = map[el.getAttribute('data-img')];
      if (uri) { el.src = uri; }
    });
  })();

  var body    = document.body;
  var stage   = document.getElementById('stage');
  var slides  = Array.prototype.slice.call(document.querySelectorAll('.slide'));
  var rail    = document.getElementById('rail');
  var posEl   = document.getElementById('pos');
  var homeBtn = document.getElementById('homeBtn');
  var current = 0;
  var animating = false;
  var suppressHash = false;

  /* --- 2. stage scaling ------------------------------------------------ */
  function fitStage() {
    var vw = window.innerWidth, vh = window.innerHeight;
    var scale = Math.min(vw / 1920, vh / 1080);
    var x = (vw - 1920 * scale) / 2;
    var y = (vh - 1080 * scale) / 2;
    stage.style.transform = 'translate(' + x + 'px,' + y + 'px) scale(' + scale + ')';
  }
  window.addEventListener('resize', fitStage);
  fitStage();

  /* --- 3. home / deck routing ----------------------------------------- */
  function atHome() { return body.classList.contains('home-open'); }

  function openHome(writeHash) {
    body.classList.add('home-open');
    if (writeHash !== false) { setHash('home'); }
    document.getElementById('home').scrollTop = homeScroll;
  }

  var homeScroll = 0;
  function openDeck(idx, writeHash) {
    if (atHome()) {
      homeScroll = document.getElementById('home').scrollTop;
      body.classList.remove('home-open');
      fitStage();
    }
    if (idx !== current) { jump(idx); } else { paint(writeHash); }
  }

  function setHash(h) {
    suppressHash = true;
    history.replaceState(null, '', '#' + h);
    setTimeout(function () { suppressHash = false; }, 0);
  }

  function paint(writeHash) {
    if (posEl) { posEl.textContent = (current + 1) + ' / ' + slides.length; }
    if (rail)  { rail.style.width = ((current + 1) / slides.length * 100) + '%'; }
    if (writeHash !== false && !atHome()) { setHash(String(current + 1)); }
  }

  function jump(idx) {
    slides[current].classList.remove('active', 'exit-left', 'exit-right', 'stage-left');
    current = idx;
    slides.forEach(function (s, i) {
      s.classList.remove('active', 'exit-left', 'exit-right', 'stage-left');
      if (i === idx) { s.classList.add('active'); }
    });
    restartAnims(slides[idx]);
    paint();
  }

  function restartAnims(slide) {
    slide.querySelectorAll('.anim').forEach(function (el) {
      if (el.tagName === 'VIDEO' || el.tagName === 'IFRAME') { return; }
      el.style.animation = 'none';
      void el.offsetWidth;
      el.style.animation = '';
    });
  }

  function show(idx, dir) {
    if (idx < 0 || idx >= slides.length || idx === current || animating) { return; }
    animating = true;

    var outgoing = slides[current];
    var incoming = slides[idx];

    incoming.classList.remove('active', 'exit-left', 'exit-right', 'stage-left');
    incoming.style.transition = 'none';
    if (dir < 0) { incoming.classList.add('stage-left'); }
    void incoming.offsetWidth;
    incoming.style.transition = '';

    restartAnims(incoming);

    outgoing.querySelectorAll('video').forEach(function (v) { if (!v.paused) { v.pause(); } });

    outgoing.classList.remove('active');
    outgoing.classList.add(dir > 0 ? 'exit-left' : 'exit-right');
    incoming.classList.remove('stage-left');
    incoming.classList.add('active');

    current = idx;
    paint();

    setTimeout(function () {
      outgoing.classList.remove('exit-left', 'exit-right');
      animating = false;
    }, 660);
  }

  function next() {
    if (current === slides.length - 1) { return; }
    show(current + 1, 1);
  }
  function prev() {
    if (current === 0) { openHome(); return; }
    show(current - 1, -1);
  }

  /* --- 4. input -------------------------------------------------------- */
  document.addEventListener('keydown', function (e) {
    if (e.target.isContentEditable) { return; }
    var k = e.key;
    if (atHome()) {
      if (k === 'Enter') { openDeck(0); }
      return;
    }
    if (k === 'ArrowRight' || k === 'PageDown' || k === ' ') { e.preventDefault(); next(); }
    else if (k === 'ArrowLeft' || k === 'PageUp') { e.preventDefault(); prev(); }
    else if (k === 'Home') { openDeck(0); }
    else if (k === 'End') { openDeck(slides.length - 1); }
    else if (k === 'Escape') { openHome(); }
  });

  /* contents links on the home page */
  document.getElementById('home').addEventListener('click', function (e) {
    var a = e.target.closest('a[href^="#"]');
    if (!a) { return; }
    var h = a.getAttribute('href').slice(1);
    if (h === 'home') { return; }
    var n = parseInt(h, 10);
    if (!isNaN(n) && n >= 1 && n <= slides.length) {
      e.preventDefault();
      openDeck(n - 1);
    }
  });

  if (homeBtn) {
    homeBtn.addEventListener('click', function (e) { e.preventDefault(); openHome(); });
  }

  /* click-to-play: swap the poster for the real YouTube embed on demand,
     so a blocked or offline network still leaves a readable slide */
  document.getElementById('viewport').addEventListener('click', function (e) {
    var box = e.target.closest('.ytbox');
    if (box && !box.querySelector('iframe')) {
      e.preventDefault();
      e.stopPropagation();
      var url = box.getAttribute('data-embed');
      box.innerHTML = '<iframe src="' + url + '?autoplay=1&rel=0" title="Demo video" '
        + 'allow="autoplay; encrypted-media; picture-in-picture; fullscreen" '
        + 'allowfullscreen></iframe>';
      return;
    }
  }, true);

  /* click the right/left half of the stage to advance */
  document.getElementById('viewport').addEventListener('click', function (e) {
    if (e.target.closest('a, button, video, iframe, .ytbox, input, [contenteditable="true"]')) { return; }
    (e.clientX > window.innerWidth * 0.5 ? next : prev)();
  });

  /* --- 5. deep links --------------------------------------------------- */
  function fromHash() {
    var h = (location.hash || '').slice(1);
    if (!h || h === 'home') { openHome(false); return; }
    var n = parseInt(h, 10);
    if (!isNaN(n) && n >= 1 && n <= slides.length) { openDeck(n - 1, false); }
    else { openHome(false); }
  }
  window.addEventListener('hashchange', function () { if (!suppressHash) { fromHash(); } });

  slides.forEach(function (s, i) { if (i > 0) { s.classList.remove('active'); } });
  slides[0].classList.add('active');
  fromHash();
  paint(false);
})();
