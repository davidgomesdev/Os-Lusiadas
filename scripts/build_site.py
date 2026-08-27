#!/usr/bin/env python3
"""Generate the GitHub Pages site: one reader page per canto, plus the index.

Reads docs/data/index.json (written by scrape.py) for the estrofe counts and
docs/data/canto-<n>.json for each canto's opening verse, which labels the canto
in place of the redundant "Canto I" caption.  Falls back to listing all ten
cantos bare if the data is missing.
"""

import html
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs"
ROMAN = ["I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X"]

PORTRAIT = (
    '<img class="portrait" src="assets/camoes.jpg" width="256" height="286" '
    'alt="Retrato de Luís de Camões, por Fernão Gomes" '
    'title="Luís de Camões, por Fernão Gomes (séc. XVI)">'
)

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
  <span class="mark" aria-label="Canto {roman}">{roman}</span>
  <span class="incipit">{incipit}</span>
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


def canto_data():
    """Per-canto {count, incipit}, read from whatever the scraper left behind."""
    info = {}
    index_file = DOCS / "data" / "index.json"
    if index_file.exists():
        for entry in json.loads(index_file.read_text(encoding="utf-8")).get("cantos", []):
            info[entry["canto"]] = {"count": entry.get("count"), "incipit": ""}
    for n in range(1, len(ROMAN) + 1):
        path = DOCS / "data" / f"canto-{n}.json"
        if not path.exists():
            continue
        estrofes = json.loads(path.read_text(encoding="utf-8")).get("estrofes") or []
        if estrofes and estrofes[0].get("lines"):
            info.setdefault(n, {"count": len(estrofes), "incipit": ""})
            # Some cantos open mid-speech; drop the dangling quote mark.
            first = estrofes[0]["lines"][0].lstrip('"\u00ab\u201c ')
            info[n]["incipit"] = first.rstrip(" ,;:")
    return info


def build_canto(n, roman, incipit):
    body = CANTO_BODY.format(n=n, roman=roman, incipit=html.escape(incipit))
    page = HEAD.format(
        title=f"Os Lusíadas — Canto {roman}",
        desc=f"Canto {roman} de Os Lusíadas, de Luís de Camões, num leitor de estrofes.",
        prefix="",
    ) + body
    (DOCS / f"canto-{n}.html").write_text(page, encoding="utf-8")


def build_index(info):
    items = []
    for i, roman in enumerate(ROMAN, start=1):
        entry = info.get(i) or {}
        count = entry.get("count")
        incipit = entry.get("incipit") or ""
        meta = f"{count} estrofes" if count else "por recolher"
        label = (
            f'<span class="incipit">{html.escape(incipit)}&hellip;</span>'
            if incipit else '<span class="incipit">por recolher</span>'
        )
        items.append(
            f'  <li><a href="canto-{i}.html">'
            f'<span class="num" aria-label="Canto {roman}">{roman}</span>'
            f'{label}<span class="meta">{meta}</span></a></li>'
        )
    total = sum(e.get("count") or 0 for e in info.values())
    total_line = f"{total} estrofes" if total else "textos por recolher"

    page = HEAD.format(
        title="Os Lusíadas — Luís de Camões",
        desc="Os Lusíadas, de Luís de Camões, em leitor de estrofes canto a canto.",
        prefix="",
    ) + f"""<body>
<main class="home">
  <div class="masthead">
    {PORTRAIT}
    <div>
      <h1>Os Lusíadas</h1>
      <p class="author">Luís de Camões &middot; 1572 &middot; {total_line}</p>
    </div>
  </div>
  <a class="resume" id="resume" href="#" hidden>Continuar a leitura<small id="resume-where"></small></a>
  <ul class="cantos">
{chr(10).join(items)}
  </ul>
  <p class="credit">Retrato de Camões por Fernão Gomes (séc.&nbsp;XVI), via Wikimedia Commons &mdash; domínio público.</p>
</main>
<script>
(function () {{
  var link = document.getElementById('resume');
  var raw;
  try {{ raw = localStorage.getItem('lusiadas:last'); }} catch (e) {{ return; }}
  if (!raw) return;                     /* nunca leu nada: fica escondido */
  try {{
    var last = JSON.parse(raw);
    if (!last || !last.canto || !last.estrofe) return;
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
    (DOCS / "index.html").write_text(page, encoding="utf-8")


def main():
    info = canto_data()
    for i, roman in enumerate(ROMAN, start=1):
        build_canto(i, roman, (info.get(i) or {}).get("incipit", ""))
    build_index(info)
    (DOCS / ".nojekyll").touch()
    print(f"Built {len(ROMAN)} canto pages + index in {DOCS}")


if __name__ == "__main__":
    main()
