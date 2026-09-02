#!/usr/bin/env python3
"""Count staves per page image, to get ground truth for judging OMR output.

A staff line is a near-horizontal run of dark pixels spanning most of the page
width, so a horizontal projection finds them without any music knowledge. Lines
are grouped into fives to give a staff count per page.

Usage:
    python spike/gt_staves.py page*.png
"""

from __future__ import annotations

import sys

import numpy as np
from PIL import Image

WIDTH_FRACTION = 0.35  # a staff line covers at least this much of the page width


def staff_lines(path: str) -> list[int]:
    im = np.array(Image.open(path).convert("L"))
    rows = (im < 128).sum(axis=1) > WIDTH_FRACTION * im.shape[1]
    lines, run = [], None
    for y, on in enumerate(rows):
        if on and run is None:
            run = y
        elif not on and run is not None:
            lines.append((run + y - 1) // 2)
            run = None
    return lines


def count_staves(path: str) -> tuple[int, int]:
    lines = staff_lines(path)
    groups, cur = [], []
    for y in lines:
        spacing = (cur[1] - cur[0]) if len(cur) > 1 else 12
        if cur and y - cur[-1] > 3 * spacing:
            groups.append(cur)
            cur = []
        cur.append(y)
    if cur:
        groups.append(cur)
    return sum(round(len(g) / 5) for g in groups if len(g) >= 4), len(lines)


def main() -> int:
    if len(sys.argv) < 2:
        print(__doc__)
        return 2
    total = 0
    for path in sys.argv[1:]:
        staves, lines = count_staves(path)
        total += staves
        print(f"{path}  staves={staves:<3} (lines detected: {lines})")
    print(f"total staves: {total}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
