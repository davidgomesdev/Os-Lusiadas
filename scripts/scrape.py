#!/usr/bin/env python3
"""Scrape "Os Lusíadas" (Luís de Camões, 1572 — public domain) from oslusiadas.org.

Pages are server-side rendered at /<canto>/<estrofe>.html where <canto> is a
lowercase roman numeral (i..x) and <estrofe> is a decimal number, e.g.
https://oslusiadas.org/i/17.html

Outputs:
  texts/canto-<n>/<estrofe>.txt   one plain-text file per estrofe
  texts/canto-<n>.txt             the whole canto in one file
  docs/data/canto-<n>.json        the data the web reader consumes
  docs/data/index.json            canto list + estrofe counts
"""

import argparse
import json
import re
import sys
import time
import urllib.error
import urllib.request
from html.parser import HTMLParser
from pathlib import Path

BASE = "https://oslusiadas.org"
ROMAN = ["i", "ii", "iii", "iv", "v", "vi", "vii", "viii", "ix", "x"]
ROMAN_UPPER = [r.upper() for r in ROMAN]

ROOT = Path(__file__).resolve().parent.parent
TEXTS = ROOT / "texts"
DATA = ROOT / "docs" / "data"

UA = "Mozilla/5.0 (compatible; os-lusiadas-archiver/1.0)"


def fetch(url, retries=4, delay=1.0):
    """GET a URL as text, retrying on transient network/5xx errors."""
    last = None
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=30) as resp:
                raw = resp.read()
                charset = resp.headers.get_content_charset()
            for enc in filter(None, [charset, "utf-8", "iso-8859-1"]):
                try:
                    return raw.decode(enc)
                except UnicodeDecodeError:
                    continue
            return raw.decode("utf-8", "replace")
        except urllib.error.HTTPError as e:
            if e.code == 404:
                raise
            last = e
        except Exception as e:  # noqa: BLE001 - network layer is broad by nature
            last = e
        time.sleep(delay * (2 ** attempt))
    raise RuntimeError(f"failed to fetch {url}: {last}")


class EstrofeParser(HTMLParser):
    """Pulls the verse lines out of <div class="uk-panel ... estrofe">.

    The panel opens with a <div class="uk-panel-badge ...">N</div> holding the
    estrofe number; the verses follow, separated by <br>.
    """

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts = []
        self._depth = 0      # nesting depth inside the estrofe panel (0 = outside)
        self._skip = 0       # nesting depth inside the badge (0 = not skipping)

    def handle_starttag(self, tag, attrs):
        classes = dict(attrs).get("class", "").split()
        if self._depth:
            if tag == "div":
                self._depth += 1
                if self._skip or "uk-panel-badge" in classes:
                    self._skip += 1
            elif self._skip:
                pass
            elif tag == "br":
                self.parts.append("\n")
        elif tag == "div" and "estrofe" in classes:
            self._depth = 1

    def handle_endtag(self, tag):
        if self._depth and tag == "div":
            if self._skip:
                self._skip -= 1
            self._depth -= 1

    def handle_data(self, data):
        if self._depth and not self._skip:
            self.parts.append(data)


class DropdownParser(HTMLParser):
    """Collects the estrofe numbers from the "Estâncias / Estrofes" dropdown.

    Its links are relative ("./" for the first, "<n>.html" after that), so the
    number is read from the link text rather than the href.
    """

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.numbers = set()
        self._in_dropdown = 0
        self._in_link = False
        self._text = []

    def handle_starttag(self, tag, attrs):
        classes = dict(attrs).get("class", "").split()
        if tag == "div":
            if self._in_dropdown:
                self._in_dropdown += 1
            elif "uk-dropdown" in classes:
                self._in_dropdown = 1
        elif tag == "a" and self._in_dropdown:
            self._in_link = True
            self._text = []

    def handle_endtag(self, tag):
        if tag == "div" and self._in_dropdown:
            self._in_dropdown -= 1
        elif tag == "a" and self._in_link:
            self._in_link = False
            label = "".join(self._text).strip()
            if label.isdigit():
                self.numbers.add(int(label))

    def handle_data(self, data):
        if self._in_link:
            self._text.append(data)


def clean_lines(raw):
    """Normalise a raw text blob into a list of verse lines."""
    raw = raw.replace("\xa0", " ")
    lines = [re.sub(r"[ \t]+", " ", ln).strip() for ln in raw.split("\n")]
    return [ln for ln in lines if ln]


def extract_estrofe(html):
    """Return the verse lines of an estrofe page."""
    p = EstrofeParser()
    p.feed(html)
    return clean_lines("".join(p.parts)) or None


def estrofe_url(roman, num):
    """The first estrofe lives at /<roman>/ ; the rest at /<roman>/<n>.html"""
    return f"{BASE}/{roman}/" if num == 1 else f"{BASE}/{roman}/{num}.html"


def discover_estrofes(canto_roman):
    """Find every estrofe number of a canto from the dropdown links.

    The page is server-side rendered, so the links the "Estâncias / Estrofes"
    button reveals are already in the HTML we fetch.
    """
    p = DropdownParser()
    p.feed(fetch(estrofe_url(canto_roman, 1)))
    if not p.numbers:
        raise RuntimeError(
            f"no estrofe links found for canto {canto_roman.upper()}; "
            "the site markup may have changed"
        )
    return sorted(p.numbers)


def scrape_canto(idx, roman, delay):
    n = idx + 1
    numbers = discover_estrofes(roman)
    print(f"Canto {roman.upper()}: {len(numbers)} estrofes (1..{max(numbers)})", flush=True)

    out_dir = TEXTS / f"canto-{n}"
    out_dir.mkdir(parents=True, exist_ok=True)
    estrofes = []
    for num in numbers:
        url = estrofe_url(roman, num)
        lines = extract_estrofe(fetch(url))
        if not lines:
            print(f"  !! could not extract text from {url}", file=sys.stderr)
            continue
        (out_dir / f"{num:03d}.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
        estrofes.append({"n": num, "lines": lines})
        print(f"  {roman.upper()}.{num} ok", flush=True)
        time.sleep(delay)

    (TEXTS / f"canto-{n}.txt").write_text(
        f"OS LUSÍADAS — CANTO {ROMAN_UPPER[idx]}\n\n"
        + "\n\n".join(f"{e['n']}\n" + "\n".join(e["lines"]) for e in estrofes)
        + "\n",
        encoding="utf-8",
    )

    DATA.mkdir(parents=True, exist_ok=True)
    (DATA / f"canto-{n}.json").write_text(
        json.dumps(
            {"canto": n, "roman": ROMAN_UPPER[idx], "count": len(estrofes), "estrofes": estrofes},
            ensure_ascii=False,
            indent=1,
        ),
        encoding="utf-8",
    )
    return len(estrofes)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--cantos", default="1-10", help="e.g. 1-10 or 1,3,7 (default: all)")
    ap.add_argument("--delay", type=float, default=0.5, help="seconds between requests")
    args = ap.parse_args()

    wanted = set()
    for part in args.cantos.split(","):
        part = part.strip()
        if "-" in part:
            a, b = part.split("-")
            wanted.update(range(int(a), int(b) + 1))
        elif part:
            wanted.add(int(part))

    counts = {}
    for idx, roman in enumerate(ROMAN):
        if idx + 1 not in wanted:
            continue
        counts[idx + 1] = scrape_canto(idx, roman, args.delay)

    index_path = DATA / "index.json"
    index = {}
    if index_path.exists():
        index = json.loads(index_path.read_text(encoding="utf-8"))
    cantos = {str(c["canto"]): c for c in index.get("cantos", [])}
    for n, count in counts.items():
        cantos[str(n)] = {"canto": n, "roman": ROMAN_UPPER[n - 1], "count": count}
    index_path.write_text(
        json.dumps(
            {"cantos": [cantos[k] for k in sorted(cantos, key=int)]},
            ensure_ascii=False,
            indent=1,
        ),
        encoding="utf-8",
    )
    total = sum(counts.values())
    print(f"\nDone: {len(counts)} cantos, {total} estrofes.")


if __name__ == "__main__":
    main()
