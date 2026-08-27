/* Theme switch: system default, paper, plain white, dark.
   The <head> applies the stored choice before first paint; this only wires
   the button, so a page without one still honours the saved theme. */
(function () {
  var KEY = 'lusiadas:theme';
  var MODES = [
    { id: 'auto', label: 'Sistema' },
    { id: 'paper', label: 'Papel' },
    { id: 'white', label: 'Branco' },
    { id: 'dark', label: 'Escuro' }
  ];

  function read() {
    try { return localStorage.getItem(KEY); } catch (e) { return null; }
  }
  function write(value) {
    try { localStorage.setItem(KEY, value); } catch (e) { /* private mode */ }
  }
  function indexOf(id) {
    for (var i = 0; i < MODES.length; i++) { if (MODES[i].id === id) return i; }
    return 0;
  }

  var current = indexOf(read());
  var btn = document.getElementById('theme');

  function paint() {
    var mode = MODES[current];
    if (mode.id === 'auto') {
      delete document.documentElement.dataset.theme;
    } else {
      document.documentElement.dataset.theme = mode.id;
    }
    if (btn) {
      btn.textContent = mode.label;
      btn.setAttribute('aria-label', 'Tema: ' + mode.label + '. Tocar para mudar.');
    }
  }

  paint();
  if (btn) {
    btn.addEventListener('click', function () {
      current = (current + 1) % MODES.length;
      write(MODES[current].id);
      paint();
    });
  }
})();
