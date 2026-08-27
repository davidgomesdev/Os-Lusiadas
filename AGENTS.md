# AGENTS.md

Orientation for coding agents working in this repository. Written in English
even though `README.md` is in Portuguese: the README addresses readers of the
site, this file addresses whoever is editing the code.

## Goal

Archive the complete text of *Os Lusíadas* (Luís de Camões, 1572 — public
domain) from oslusiadas.org, and publish it on GitHub Pages as a reader that
works like a swipe deck: one estrofe per screen, with the reading position
remembered.

Two properties matter more than any feature:

1. **The archive is faithful to the source.** `texts/` is what the site served.
   Do not correct, complete, or normalise the verse from another edition.
2. **The site is static.** No build step beyond two Python scripts, no runtime
   dependencies, no framework. It is plain HTML/CSS/JS served from `docs/`.

## Layout

```
scripts/scrape.py      fetches oslusiadas.org -> texts/ + docs/data/
scripts/build_site.py  generates docs/index.html + docs/canto-<n>.html
scripts/verify.py      checks the scraped data; run after any scrape
texts/                 the archive: one .txt per estrofe, one per canto
docs/                  what GitHub Pages serves
  data/canto-<n>.json  what the reader fetches at runtime
  data/index.json      canto list + estrofe counts, drives the home page
  assets/reader.js     the whole reader; no bundler, no dependencies
.github/workflows/     pages.yml deploys; scrape.yml re-scrapes on demand
```

Everything is standard library Python 3 and vanilla browser JS. Keep it that
way — adding a dependency means adding a toolchain to a repository that
currently needs none.

## How the scrape works

The source is server-side rendered, so a plain HTTP GET is enough; no browser
or JS execution is involved.

- **URLs.** `/<canto>/<estrofe>.html`, canto as a lowercase roman numeral
  (`i`..`x`). The first estrofe of a canto is the directory index, `/<roman>/`,
  *not* `/<roman>/1.html` — see `estrofe_url()`.
- **Finding the estrofes.** The "Estâncias / Estrofes" button opens a
  `div.uk-dropdown` listing every estrofe of the canto. Its links are relative
  (`./` for the first, `<n>.html` after), so `DropdownParser` reads the number
  from the link *text*, not the href. Do not reintroduce an href pattern here.
- **Extracting the verse.** `EstrofeParser` targets `div.…estrofe`, treats
  `<br>` as a line break, and skips the nested `div.uk-panel-badge` that holds
  the estrofe number — otherwise the number lands in the text as a stray line.

The site uses UIkit 2, so class names like `uk-panel-box` and `uk-dropdown` are
load-bearing. If a scrape suddenly returns nothing, check whether that markup
changed before touching the parsers.

Be polite to the origin server: `--delay` defaults to 0.5s and a full run is
~1100 requests, roughly 12–15 minutes. Do not parallelise it.

## Known data anomalies — do not "fix" these

`verify.py` reports five estrofes that are not eight lines. All five mirror the
source page; none is a parser bug. `README.md` has the table. In short: four
carry an editorial caption inside the verse panel with no markup separating it
from the verse, and II.19 is genuinely missing a verse on oslusiadas.org.

If a future change makes these disappear, that is a regression to investigate,
not a success. And if you are ever asked to complete II.19, do not write the
missing verse from memory or another edition — that fabricates archive data.

## How the reader works

`docs/canto-<n>.html` is a thin shell: `<body data-canto data-roman>`, an empty
`#track`, and `assets/reader.js`. The script fetches `data/canto-<n>.json` and
renders every estrofe as a `.page` inside a horizontal CSS scroll-snap track.
Swiping is native scrolling; keyboard, tap zones, and the jump prompt all go
through `goTo()`.

Two subtleties that were bugs once and will be again if removed:

- **`seek()` re-asserts a jump across several frames.** Scrolling to a far page
  (canto X has 156) gets clamped while the track is still laying out, which
  parks the reader on the first estrofe. It retries until `scrollLeft` lands.
- **`onScroll` ignores events while `pending > 0`.** Otherwise a programmatic
  scroll is read back as a user swipe and fights the jump it was told to make.
- **`.resume[hidden]` must stay in the CSS.** `.resume` sets `display: block`,
  which on its own overrides the `hidden` attribute, so the home page offers
  "Continuar a leitura" to someone who has never opened a canto.

Estrofe cards carry only `Estrofe <n>`. The canto is named once per page, in
the header, so repeating it on all 156 cards was noise.

The checkpoint lives in `localStorage` under `lusiadas:canto:<n>` (per canto)
and `lusiadas:last` (for the home page's "Continuar a leitura"). Every read and
write is wrapped in try/catch — private browsing throws rather than returning
null. The URL hash tracks the current estrofe via `replaceState`, so sharing a
link works without flooding session history; a `hashchange` listener follows a
pasted or back/forward hash.

## How the cantos are labelled

Neither page repeats "Canto I" beside a bare roman numeral. `build_site.py`
reads the first verse of estrofe 1 out of `docs/data/canto-<n>.json` and uses it
as the canto's caption: the index rows are numeral + opening verse + count, and
the reader header is numeral + opening verse (dropped under 30rem). The numeral
carries an `aria-label="Canto <roman>"`, so the word survives for screen readers
without being drawn twice.

This means the index depends on the scraped JSON for more than counts. With no
data the caption falls back to "por recolher" rather than breaking the build.

The truncation is load-bearing: `.cantos` needs `grid-template-columns:
minmax(0, 1fr)` and the flex chain needs `min-width: 0`, or the grid column
sizes itself to the full un-truncated verse and the page scrolls sideways on a
phone. `.portrait` is given an explicit height for the same reason — a failed
load would otherwise reflow the masthead around a block of alt text.

## Working on this

- After scraping: `python3 scripts/verify.py` (expects 1102 estrofes, 5
  anomalies) and `python3 scripts/build_site.py`.
- After editing `build_site.py`: regenerate and commit the `docs/*.html` it
  produces; they are checked in, not built at deploy time by anything else.
- After editing `reader.js`: test in a real browser against a *large* canto.
  Small fixtures hide the layout-timing bugs above; canto X is the honest test.
- Publishing is *Settings → Pages → Source: GitHub Actions*; `pages.yml`
  deploys `docs/` on every push to `main`.
- `scrape.yml` (workflow_dispatch) re-runs the scrape on a GitHub runner and
  commits the result — useful when the environment running the agent cannot
  reach oslusiadas.org.
