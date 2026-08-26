#!/usr/bin/env python3
"""Generate the GitHub Pages site: one reader page per canto, plus the index.

Reads docs/data/index.json (written by scrape.py) for the estrofe counts;
falls back to listing all ten cantos without counts if it is missing.
"""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs"
ROMAN = ["I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X"]

HEAD = """<!doctype html>
<html lang="pt">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>{title}</title>
<meta name="description" content="{desc}">
<link rel="stylesheet" href="{prefix}assets/reader.css">
</head>
"""

CANTO_BODY = """<body class="reader" data-canto="{n}" data-roman="{roman}">
<header class="bar">
  <a href="./">&larr; Cantos</a>
  <span class="title">Canto {roman}</span>
  <button id="jump" type="button">Ir para&hellip;</button>
  <span class="pos" id="pos">&hellip;</span>
</header>
<div class="progress"><i id="bar"></i></div>
<button class="nav-zone prev" type="button" aria-label="Estrofe anterior"></button>
<button class="nav-zone next" type="button" aria-label="Estrofe seguinte"></button>
<main class="track" id="track"><div class="msg">A carregar&hellip;</div></main>
<p class="hint">Desliza, usa as setas &larr; &rarr;, ou toca nas margens. A leitura fica guardada.</p>
<script src="assets/reader.js"></script>
</body>
</html>
"""


def build_canto(n, roman):
    html = HEAD.format(
        title=f"Os Lusíadas — Canto {roman}",
        desc=f"Canto {roman} de Os Lusíadas, de Luís de Camões, num leitor de estrofes.",
        prefix="",
    ) + CANTO_BODY.format(n=n, roman=roman)
    (DOCS / f"canto-{n}.html").write_text(html, encoding="utf-8")


def build_index(counts):
    items = []
    for i, roman in enumerate(ROMAN, start=1):
        count = counts.get(i)
        meta = f"{count} estrofes" if count else "por recolher"
        items.append(
            f'  <li><a href="canto-{i}.html"><span class="num">{roman}</span>'
            f'<span>Canto {roman}</span><span class="meta">{meta}</span></a></li>'
        )
    total = sum(counts.values()) if counts else 0
    total_line = f"{total} estrofes" if total else "textos por recolher"

    html = HEAD.format(
        title="Os Lusíadas — Luís de Camões",
        desc="Os Lusíadas, de Luís de Camões, em leitor de estrofes canto a canto.",
        prefix="",
    ) + f"""<body>
<main class="home">
  <h1>Os Lusíadas</h1>
  <p class="author">Luís de Camões &middot; 1572 &middot; {total_line}</p>
  <a class="resume" id="resume" href="#" hidden>Continuar a leitura<small id="resume-where"></small></a>
  <ul class="cantos">
{chr(10).join(items)}
  </ul>
</main>
<script>
(function () {{
  var raw;
  try {{ raw = localStorage.getItem('lusiadas:last'); }} catch (e) {{ return; }}
  if (!raw) return;
  try {{
    var last = JSON.parse(raw);
    if (!last || !last.canto) return;
    var link = document.getElementById('resume');
    link.href = 'canto-' + last.canto + '.html#' + last.estrofe;
    document.getElementById('resume-where').textContent =
      'Canto ' + last.roman + ', estrofe ' + last.estrofe;
    link.hidden = false;
  }} catch (e) {{ /* ignore a corrupt checkpoint */ }}
}})();
</script>
</body>
</html>
"""
    (DOCS / "index.html").write_text(html, encoding="utf-8")


def main():
    counts = {}
    index_file = DOCS / "data" / "index.json"
    if index_file.exists():
        for entry in json.loads(index_file.read_text(encoding="utf-8")).get("cantos", []):
            counts[entry["canto"]] = entry.get("count")
    for i, roman in enumerate(ROMAN, start=1):
        build_canto(i, roman)
    build_index(counts)
    (DOCS / ".nojekyll").touch()
    print(f"Built {len(ROMAN)} canto pages + index in {DOCS}")


if __name__ == "__main__":
    main()
