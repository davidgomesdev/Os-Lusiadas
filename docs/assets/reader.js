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
        '<div class="n">Canto ' + roman + ' &middot; Estrofe ' + e.n + '</div>' +
        '<p>' + text + '</p></div></article>';
    }).join('');
    track.innerHTML = html;
  }

  function goTo(index, smooth) {
    if (!total) return;
    current = Math.max(0, Math.min(total - 1, index));
    track.scrollTo({ left: current * track.clientWidth, behavior: smooth ? 'smooth' : 'auto' });
    update();
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
      window.addEventListener('resize', function () { goTo(current, false); });
      document.addEventListener('keydown', function (ev) {
        if (ev.key === 'ArrowRight' || ev.key === 'PageDown' || ev.key === ' ') {
          ev.preventDefault(); goTo(current + 1, true);
        } else if (ev.key === 'ArrowLeft' || ev.key === 'PageUp') {
          ev.preventDefault(); goTo(current - 1, true);
        } else if (ev.key === 'Home') { goTo(0, true); }
        else if (ev.key === 'End') { goTo(total - 1, true); }
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
