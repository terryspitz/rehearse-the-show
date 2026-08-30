#!/usr/bin/env python3
"""Up-res and clean a low-resolution score scan before OMR.

Audiveris estimates staff interline spacing and its symbol classifiers expect
roughly 20 px. A scan at 8 px interline is far outside that range, which is a
scale problem rather than an information problem — interpolation adds no detail
but does put the engine back in its operating window.

The second half matters as much: a JPEG scan carries ringing artefacts around
every glyph, where a bitonal fax-encoded scan does not. Sauvola local
thresholding removes that ringing and produces the clean black-and-white input
Audiveris is happiest with.

Usage:
    python spike/upres.py out.pdf page*.png --interline 20
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))
from gt_staves import staff_lines


def measure_interline(path: str) -> float:
    lines = staff_lines(path)
    d = np.diff(lines)
    if not len(d):
        return 0.0
    inner = d[(d > 2) & (d < np.median(d[d > 2]) * 2.2)]
    return float(np.median(inner)) if len(inner) else 0.0


def sauvola(gray: np.ndarray, window: int = 41, k: float = 0.28, r: float = 128.0) -> np.ndarray:
    """Local adaptive threshold via integral images. Returns a boolean ink mask."""
    img = gray.astype(np.float64)
    h, w = img.shape
    pad = window // 2
    window = 2 * pad + 1                      # force odd so the box lands square
    p = np.pad(img, pad, mode="edge")

    def integral(a):
        return np.pad(a.cumsum(0).cumsum(1), ((1, 0), (1, 0)))

    def box(ii):
        return (ii[window:window + h, window:window + w] + ii[:h, :w]
                - ii[window:window + h, :w] - ii[:h, window:window + w])

    n = window * window
    mean = box(integral(p)) / n
    var = np.maximum(box(integral(p ** 2)) / n - mean ** 2, 0)
    thresh = mean * (1 + k * (np.sqrt(var) / r - 1))
    return img < thresh


def process(path: Path, scale: float, binarize: bool) -> Image.Image:
    im = Image.open(path).convert("L")
    w, h = im.size
    im = im.resize((round(w * scale), round(h * scale)), Image.LANCZOS)
    if not binarize:
        return im
    ink = sauvola(np.asarray(im))
    return Image.fromarray(np.where(ink, 0, 255).astype(np.uint8), "L").convert("1")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("out", help="output PDF")
    ap.add_argument("pages", nargs="+", help="page images, in order")
    ap.add_argument("--interline", type=float, default=20.0,
                    help="target staff interline in px (Audiveris likes ~20)")
    ap.add_argument("--scale", type=float, default=0, help="fixed scale, overrides --interline")
    ap.add_argument("--no-binarize", action="store_true")
    args = ap.parse_args()

    first = measure_interline(args.pages[0])
    scale = args.scale or (args.interline / first if first else 1.0)
    print(f"  measured interline {first:.1f} px -> scaling {scale:.2f}x "
          f"(target {args.interline:.0f} px)"
          f"{'' if args.no_binarize else ', Sauvola binarization'}")

    imgs = [process(Path(p), scale, not args.no_binarize) for p in args.pages]
    print(f"  {len(imgs)} pages, output size {imgs[0].size}")
    imgs[0].save(args.out, save_all=True, append_images=imgs[1:], resolution=300.0)
    print(f"  wrote {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
