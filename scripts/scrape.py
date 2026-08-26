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


class Collector(HTMLParser):
    """Collects hrefs and per-block text from a page."""

    SKIP = {"script", "style", "head", "title", "noscript"}

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.hrefs = []
        self.blocks = []          # list of (tag, [lines])
        self._stack = []          # open tags we are accumulating text for
        self._skip_depth = 0

    def handle_starttag(self, tag, attrs):
        if tag in self.SKIP:
            self._skip_depth += 1
            return
        if tag == "a":
            for k, v in attrs:
                if k == "href" and v:
                    self.hrefs.append(v)
        if tag in ("p", "div", "blockquote", "pre", "td", "li", "section", "article"):
            self._stack.append([tag, []])
        if tag == "br":
            for frame in self._stack:
                frame[1].append("\n")

    def handle_endtag(self, tag):
        if tag in self.SKIP:
            self._skip_depth = max(0, self._skip_depth - 1)
            return
        for i in range(len(self._stack) - 1, -1, -1):
            if self._stack[i][0] == tag:
                frame = self._stack.pop(i)
                self.blocks.append((frame[0], "".join(frame[1])))
                break

    def handle_data(self, data):
        if self._skip_depth:
            return
        for frame in self._stack:
            frame[1].append(data)


def clean_lines(raw):
    """Normalise a raw text blob into a list of verse lines."""
    raw = raw.replace("\xa0", " ")
    lines = [re.sub(r"[ \t]+", " ", ln).strip() for ln in raw.split("\n")]
    return [ln for ln in lines if ln]


def looks_like_estrofe(lines):
    """An estrofe is an oitava: 8 verse lines of roughly comparable length."""
    if not 6 <= len(lines) <= 10:
        return False
    if any(len(ln) > 120 for ln in lines):
        return False
    # Reject navigation blocks: mostly very short, digit-only or single-word items.
    short = sum(1 for ln in lines if len(ln) < 12)
    return short <= len(lines) // 2


def extract_estrofe(html):
    """Pull the 8 verse lines of an estrofe out of a page."""
    c = Collector()
    c.feed(html)
    candidates = []
    for tag, raw in c.blocks:
        lines = clean_lines(raw)
        if looks_like_estrofe(lines):
            # Prefer the innermost (smallest) matching block.
            candidates.append((len("".join(lines)), tag, lines))
    if not candidates:
        return None
    candidates.sort(key=lambda t: t[0])
    return candidates[0][2]


def discover_estrofes(canto_roman):
    """Find every estrofe number of a canto.

    The "Estâncias / Estrofes" button opens a div of links; the page is
    server-side rendered, so those links are present in the HTML we fetch.
    """
    html = fetch(f"{BASE}/{canto_roman}/1.html")
    c = Collector()
    c.feed(html)
    pat = re.compile(rf"(?:^|/){re.escape(canto_roman)}/(\d+)\.html$", re.I)
    nums = set()
    for href in c.hrefs:
        m = pat.search(href.split("?")[0].split("#")[0])
        if m:
            nums.add(int(m.group(1)))
    if not nums:
        raise RuntimeError(
            f"no estrofe links found for canto {canto_roman.upper()}; "
            "the site markup may have changed"
        )
    return sorted(nums)


def scrape_canto(idx, roman, delay):
    n = idx + 1
    numbers = discover_estrofes(roman)
    print(f"Canto {roman.upper()}: {len(numbers)} estrofes (1..{max(numbers)})", flush=True)

    out_dir = TEXTS / f"canto-{n}"
    out_dir.mkdir(parents=True, exist_ok=True)
    estrofes = []
    for num in numbers:
        url = f"{BASE}/{roman}/{num}.html"
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
