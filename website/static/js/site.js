/* EURADON – Mega-Menü, Kopfzeile beim Scrollen, sanftes Einblenden.
   Ohne JavaScript bleibt alles sichtbar und bedienbar (mobiles Menü, alle Inhalte). */
(function () {
  var doc = document.documentElement;
  var reduce = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  /* ---------- Mega-Menü ---------- */
  var head = document.getElementById('site-head');
  var tops = head ? head.querySelectorAll('button.nav-top') : [];
  var current = null, openTimer = null, closeTimer = null;
  var canHover = window.matchMedia && window.matchMedia('(hover: hover)').matches;

  function panelOf(btn) { return document.getElementById(btn.getAttribute('aria-controls')); }
  function openMenu(btn) {
    clearTimeout(closeTimer);
    if (current && current !== btn) closeMenu(true);
    var panel = panelOf(btn);
    panel.hidden = false;
    requestAnimationFrame(function () { panel.classList.add('is-open'); });
    btn.setAttribute('aria-expanded', 'true');
    current = btn;
  }
  function closeMenu(now) {
    if (!current) return;
    var btn = current, panel = panelOf(btn);
    var done = function () {
      panel.classList.remove('is-open');
      btn.setAttribute('aria-expanded', 'false');
      if (current === btn) current = null;
      setTimeout(function () { if (!panel.classList.contains('is-open')) panel.hidden = true; }, reduce ? 0 : 180);
    };
    if (now) done(); else closeTimer = setTimeout(done, 220);
  }
  tops.forEach(function (btn) {
    var panel = panelOf(btn);
    btn.addEventListener('click', function () {
      clearTimeout(openTimer);
      if (current === btn) closeMenu(true); else openMenu(btn);
    });
    if (canHover) {
      // kleine Verzögerung, damit das Menü beim Überfahren nicht flackert
      btn.addEventListener('mouseenter', function () { clearTimeout(closeTimer); openTimer = setTimeout(function () { openMenu(btn); }, current ? 0 : 140); });
      btn.addEventListener('mouseleave', function () { clearTimeout(openTimer); closeMenu(false); });
      panel.addEventListener('mouseenter', function () { clearTimeout(closeTimer); });
      panel.addEventListener('mouseleave', function () { closeMenu(false); });
    }
  });
  document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape' && current) { var b = current; closeMenu(true); b.focus(); }
  });
  // Tastatur: Tab führt vom geöffneten Menüpunkt in sein Panel und am Ende zum nächsten Menüpunkt
  var topList = Array.prototype.slice.call(head ? head.querySelectorAll('.nav-top') : []);
  tops.forEach(function (btn) {
    var panel = panelOf(btn);
    var links = function () { return panel.querySelectorAll('a[href]'); };
    btn.addEventListener('keydown', function (e) {
      if (e.key === 'Tab' && !e.shiftKey && btn.getAttribute('aria-expanded') === 'true') { e.preventDefault(); links()[0].focus(); }
      if (e.key === 'ArrowDown') { e.preventDefault(); openMenu(btn); links()[0].focus(); }
    });
    panel.addEventListener('keydown', function (e) {
      if (e.key !== 'Tab') return;
      var ls = links();
      if (e.shiftKey && document.activeElement === ls[0]) { e.preventDefault(); btn.focus(); }
      else if (!e.shiftKey && document.activeElement === ls[ls.length - 1]) {
        e.preventDefault(); closeMenu(true);
        var next = topList[topList.indexOf(btn) + 1];
        (next || btn).focus();
      }
    });
  });
  document.addEventListener('click', function (e) { if (current && head && !head.contains(e.target)) closeMenu(true); });
  if (head) head.addEventListener('focusout', function (e) { if (current && !head.contains(e.relatedTarget)) closeMenu(true); });

  /* ---------- Kopfzeile wird beim Scrollen schmaler ---------- */
  if (head) {
    var onScroll = function () { head.classList.toggle('is-scrolled', window.scrollY > 40); };
    window.addEventListener('scroll', onScroll, { passive: true });
    onScroll();
  }

  /* ---------- Sanftes Einblenden beim Scrollen ---------- */
  if (reduce || !('IntersectionObserver' in window)) return;
  var targets = [];
  document.querySelectorAll('main .section-head, main .event, main .note, main .profile, main .cols2, main .timeline, main .table-wrap, main .faq, main .map-layout').forEach(function (el) { targets.push(el); });
  document.querySelectorAll('main .paths > *, main .forms > *, main .members > *').forEach(function (el) {
    var i = Array.prototype.indexOf.call(el.parentNode.children, el) % 3;
    el.style.transitionDelay = (i * 90) + 'ms';
    targets.push(el);
  });
  doc.classList.add('js-reveal');
  var io = new IntersectionObserver(function (entries) {
    entries.forEach(function (en) {
      if (en.isIntersecting) { en.target.classList.add('is-in'); io.unobserve(en.target); }
    });
  }, { rootMargin: '0px 0px -8% 0px', threshold: 0.08 });
  targets.forEach(function (el) { el.classList.add('reveal'); io.observe(el); });

  /* Kartenpunkte erscheinen nacheinander, sobald die Karte sichtbar wird */
  var map = document.getElementById('map');
  if (map) {
    map.classList.add('pins-wait');
    var mo = new IntersectionObserver(function (entries) {
      if (entries[0].isIntersecting) {
        map.querySelectorAll('.pin').forEach(function (p, i) { p.style.animationDelay = (i * 70) + 'ms'; });
        map.classList.remove('pins-wait'); map.classList.add('pins-drop'); mo.disconnect();
      }
    }, { threshold: 0.25 });
    mo.observe(map);
  }
})();
