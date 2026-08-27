#!/usr/bin/env python3
"""Check the scraped data against what an estrofe should look like.

An estrofe of Os Lusíadas is an oitava — eight verse lines. Anything else is
worth a human look: either the source page carries an editorial caption inside
the verse panel, or the page itself is missing a line.
"""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "docs" / "data"

# Estrofes per canto in the standard editions, used as a completeness check.
CANONICAL = {1: 106, 2: 113, 3: 143, 4: 104, 5: 100, 6: 99, 7: 87, 8: 99, 9: 95, 10: 156}


def main():
    index_file = DATA / "index.json"
    if not index_file.exists():
        sys.exit("No scraped data yet — run scripts/scrape.py first.")

    problems, anomalies = [], []
    total = 0
    for entry in json.loads(index_file.read_text(encoding="utf-8"))["cantos"]:
        n = entry["canto"]
        data = json.loads((DATA / f"canto-{n}.json").read_text(encoding="utf-8"))
        numbers = [e["n"] for e in data["estrofes"]]
        total += len(numbers)

        expected = CANONICAL.get(n)
        if expected and len(numbers) != expected:
            problems.append(f"Canto {entry['roman']}: {len(numbers)} estrofes, expected {expected}")
        if numbers != list(range(1, len(numbers) + 1)):
            missing = sorted(set(range(1, max(numbers) + 1)) - set(numbers))
            problems.append(f"Canto {entry['roman']}: non-contiguous, missing {missing}")

        for e in data["estrofes"]:
            if any(line.strip().isdigit() for line in e["lines"]):
                problems.append(f"{entry['roman']}.{e['n']}: a bare number leaked into the verses")
            if len(e["lines"]) != 8:
                anomalies.append(f"{entry['roman']}.{e['n']}: {len(e['lines'])} lines")

    print(f"{total} estrofes across {len(CANONICAL)} cantos "
          f"(expected {sum(CANONICAL.values())})")

    if anomalies:
        print(f"\n{len(anomalies)} estrofe(s) not eight lines — these mirror the source page:")
        for a in anomalies:
            print(f"  - {a}")
        print("  Nine lines usually means an editorial caption sits inside the verse\n"
              "  panel; seven means the source page is itself missing a verse.")

    if problems:
        print(f"\n{len(problems)} problem(s):")
        for p in problems:
            print(f"  - {p}")
        return 1
    print("\nNo structural problems.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
