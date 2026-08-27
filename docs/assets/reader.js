/* Swipe reader for one canto, with a persisted reading checkpoint. */
(function () {
  var canto = Number(document.body.dataset.canto);
  var roman = document.body.dataset.roman;
  var KEY = 'lusiadas:canto:' + canto;
  var LAST = 'lusiadas:last';

  var track = document.getElementById('track');
  var pos = document.getElementById('pos');
  var bar = document.getElementById('bar');
  var current = 0;      // index into the estrofes array
  var total = 0;
  var numbers = [];     // estrofe numbers, parallel to the pages

  function store(key, value) {
    try { localStorage.setItem(key, value); } catch (e) { /* private mode */ }
  }
  function load(key) {
    try { return localStorage.getItem(key); } catch (e) { return null; }
  }

  function save() {
    if (!total) return;
    store(KEY, String(numbers[current]));
    store(LAST, JSON.stringify({ canto: canto, roman: roman, estrofe: numbers[current] }));
  }

  function render(list) {
    total = list.length;
    numbers = list.map(function (e) { return e.n; });
    var html = list.map(function (e) {
      var text = e.lines.map(function (l) {
        return l.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
      }).join('\n');
      return '<article class="page"><div class="estrofe" id="e' + e.n + '">' +
        '<div class="n">Estrofe ' + e.n + '</div>' +
        '<p>' + text + '</p></div></article>';
    }).join('');
    track.innerHTML = html;
  }

  var pending = 0;  // frames to keep re-asserting a programmatic scroll

  function goTo(index, smooth) {
    if (!total) return;
    current = Math.max(0, Math.min(total - 1, index));
    update();
    seek(smooth);
  }

  /* A jump to a far page can be clamped while the pages are still laying out,
     which would otherwise leave us parked on the first estrofe. Re-assert the
     target over the next few frames until the track actually lands on it. */
  function seek(smooth) {
    pending = 8;
    (function step() {
      if (pending <= 0) return;
      pending--;
      var w = track.clientWidth;
      if (w) {
        var target = current * w;
        if (Math.abs(track.scrollLeft - target) > 1) {
          track.scrollTo({ left: target, behavior: smooth ? 'smooth' : 'auto' });
        } else {
          pending = 0;
          return;
        }
      }
      requestAnimationFrame(step);
    })();
  }

  function update() {
    if (!total) return;
    pos.textContent = numbers[current] + ' / ' + numbers[total - 1];
    bar.style.width = ((current + 1) / total * 100) + '%';
    if (location.hash !== '#' + numbers[current]) {
      history.replaceState(null, '', '#' + numbers[current]);
    }
    save();
  }

  /* Which page is in view after a swipe or a resize. */
  var settle;
  function onScroll() {
    clearTimeout(settle);
    settle = setTimeout(function () {
      if (pending > 0) return;  // our own scroll, not the reader's swipe
      var w = track.clientWidth;
      if (!w) return;
      var i = Math.round(track.scrollLeft / w);
      if (i !== current) { current = Math.max(0, Math.min(total - 1, i)); update(); }
    }, 90);
  }

  function startIndex() {
    var fromHash = Number((location.hash || '').slice(1));
    var target = fromHash || Number(load(KEY)) || numbers[0];
    var i = numbers.indexOf(target);
    return i === -1 ? 0 : i;
  }

  function fail(message) {
    track.innerHTML = '<div class="msg">' + message + '</div>';
  }

  fetch('data/canto-' + canto + '.json')
    .then(function (r) {
      if (!r.ok) throw new Error(r.status + ' ' + r.statusText);
      return r.json();
    })
    .then(function (data) {
      if (!data.estrofes || !data.estrofes.length) throw new Error('no estrofes in data file');
      render(data.estrofes);
      goTo(startIndex(), false);

      track.addEventListener('scroll', onScroll, { passive: true });
      window.addEventListener('resize', function () { seek(false); });
      document.addEventListener('keydown', function (ev) {
        if (ev.key === 'ArrowRight' || ev.key === 'PageDown' || ev.key === ' ') {
          ev.preventDefault(); goTo(current + 1, true);
        } else if (ev.key === 'ArrowLeft' || ev.key === 'PageUp') {
          ev.preventDefault(); goTo(current - 1, true);
        } else if (ev.key === 'Home') { goTo(0, true); }
        else if (ev.key === 'End') { goTo(total - 1, true); }
      });
      /* Someone pasted a different estrofe into the address bar, or used
         back/forward: follow it without reloading. */
      window.addEventListener('hashchange', function () {
        var i = numbers.indexOf(Number((location.hash || '').slice(1)));
        if (i !== -1 && i !== current) goTo(i, true);
      });
      document.querySelector('.nav-zone.prev').addEventListener('click', function () { goTo(current - 1, true); });
      document.querySelector('.nav-zone.next').addEventListener('click', function () { goTo(current + 1, true); });
      document.getElementById('jump').addEventListener('click', function () {
        var answer = prompt('Ir para a estrofe (1–' + numbers[total - 1] + '):', numbers[current]);
        if (answer === null) return;
        var i = numbers.indexOf(Number(answer));
        if (i === -1) { alert('Estrofe inexistente neste canto.'); return; }
        goTo(i, true);
      });
    })
    .catch(function (err) {
      fail('Não foi possível carregar <code>data/canto-' + canto + '.json</code>.<br>' +
        'Corre <code>python3 scripts/scrape.py</code> para gerar os textos.<br><br><small>' +
        String(err.message || err) + '</small>');
    });
})();
