"""Stage 4a — FILMSTRIP SLICER.  one generated canvas -> N consecutive frames.

The generator can only give us ONE image per scene. To get CHARACTER MOTION
cheaply we ask it for a single canvas that contains several CONSECUTIVE frames
of the same shot (a "camera strip" / flipbook / sprite sheet), then slice that
canvas here into real frames.  One farm call then yields a whole animated
shot instead of one static picture.

Layouts
  row     N panels left -> right           (a wide strip, e.g. 8:1 canvas)
  col     N panels top -> bottom
  grid:RxC  R rows x C cols, row-major    (e.g. 2x2 in a 16:9 canvas)
  auto    picked from the canvas aspect vs the target frame aspect

How the cells are found (in this order, first match wins)
  1. the CONTENT BBOX — a uniform black border around the canvas is ignored
  2. interior GUTTERS — thin dark lines between the cells split the bbox into
     real panels (a gutter is excluded from both neighbours)
  3. equal division of the content bbox (always works)

usage:
  python slice_filmstrip.py --image strip.png --out clip_frames/scene-03 \
      --frames 4 --grid 2x2 --target 1920x960
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import vlib as V

V.setup_env()
import numpy as np  # noqa: E402
from PIL import Image  # noqa: E402


def _luma(a: np.ndarray) -> np.ndarray:
    if a.ndim == 2:
        return a.astype(float)
    return (0.299 * a[:, :, 0] + 0.587 * a[:, :, 1] + 0.114 * a[:, :, 2])


def content_bbox(gray: np.ndarray):
    """The region that is not a uniform black border -> (x0, y0, x1, y1)."""
    g = gray.astype(float)
    gmax = float(g.max())
    thr = max(6.0, gmax * 0.10)
    cols = g.max(axis=0) > thr
    rows = g.max(axis=1) > thr
    if not cols.any() or not rows.any():
        return 0, 0, gray.shape[1], gray.shape[0]
    xs = np.where(cols)[0]
    ys = np.where(rows)[0]
    return int(xs[0]), int(ys[0]), int(xs[-1]) + 1, int(ys[-1]) + 1


def dark_runs(gray: np.ndarray, axis: int):
    """Runs of near-black lines along `axis` -> [(start, end), ...]."""
    prof = _luma(gray).mean(axis=axis)
    thr = max(24.0, float(prof.min()) * 2.2)
    dark = prof <= thr
    runs = []
    i = 0
    n = len(dark)
    while i < n:
        if dark[i]:
            j = i
            while j < n and dark[j]:
                j += 1
            if (j - i) <= max(2, int(0.03 * n)):
                runs.append((int(i), int(j)))
            i = j
        else:
            i += 1
    return runs


def _subsets(items: list, k: int):
    if k == 0:
        yield []
        return
    if len(items) < k:
        return
    for i in range(len(items)):
        for rest in _subsets(items[i + 1:], k - 1):
            yield [items[i]] + rest


def segments(span, runs, count):
    """Split `span` = (start, end) into `count` segments using interior gutters."""
    inner = [(a, b) for (a, b) in runs if a > span[0] + 2 and b < span[1] - 2]
    if len(inner) >= count - 1:
        best = None
        for combo in _subsets(inner, count - 1):
            edges = []
            prev = span[0]
            for (a, b) in combo:
                edges.append((prev, a))
                prev = b
            edges.append((prev, span[1]))
            widths = [e[1] - e[0] for e in edges]
            if min(widths) <= (span[1] - span[0]) * 0.08:
                continue
            score = max(widths) - min(widths)
            if best is None or score < best[0]:
                best = (score, edges)
        if best:
            return best[1], f"{len(inner)} gutter(s) found"
    w = span[1] - span[0]
    return ([(span[0] + round(i * w / count), span[0] + round((i + 1) * w / count))
             for i in range(count)], "divided equally")


def auto_layout(img_w: int, img_h: int, frames: int, target_w: int, target_h: int,
                grid: str | None):
    """-> (layout, cols, rows)"""
    a_t = target_w / max(1, target_h)
    a_i = img_w / max(1, img_h)
    if grid:
        c, r = (int(x) for x in grid.lower().replace("x", " ").split())
        if c * r == frames:
            return ("grid", c, r)
    if a_i >= frames * a_t * 0.72:
        return ("row", frames, 1)
    if a_i <= a_t / frames * 0.72:
        return ("col", 1, frames)
    best = None
    for rows in range(1, frames + 1):
        if frames % rows:
            continue
        cols = frames // rows
        score = abs((cols * a_t) / rows - a_i)
        if best is None or score < best[0]:
            best = (score, ("grid", cols, rows))
    return best[1]


def energy_anchor(img: Image.Image) -> float:
    """Where the subject sits in this cell, as a fraction of its width.

    A strip cell is often 4:1 while the frame is 2:1, so the crop has to be
    anchored on the subject - a centre crop would cut the character out.  The
    anchor is the horizontal centroid of the edge energy (the outlines).
    """
    g = np.asarray(img.convert("L"), dtype=float)
    if g.shape[1] < 4:
        return 0.5
    gx = np.abs(np.diff(g, axis=1)).sum(axis=0)
    if gx.sum() <= 0:
        return 0.5
    k = max(1, len(gx) // 24)
    sm = np.convolve(gx, np.ones(k) / k, mode="same")
    if sm.sum() <= 0:
        return 0.5
    xs = np.arange(len(sm), dtype=float)
    return float((sm * xs).sum() / sm.sum() / max(1.0, len(sm) - 1.0))


def crop_to_aspect(img: Image.Image, tw: int, th: int, anchor_x: float | None = None) -> Image.Image:
    w, h = img.size
    a_img = w / h
    a_t = tw / th
    if a_img > a_t:                      # too wide -> crop the sides
        nw = int(round(h * a_t))
        if anchor_x is None:
            x = (w - nw) // 2
        else:
            x = int(round(anchor_x * w - nw / 2.0))
            x = max(0, min(w - nw, x))
        img = img.crop((x, 0, x + nw, h))
    else:                                # too tall -> crop top/bottom
        nh = int(round(w / a_t))
        y = int((h - nh) * 0.42)         # keep a bit above centre (heads)
        img = img.crop((0, y, w, y + nh))
    return img.resize((tw, th), Image.LANCZOS)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--image", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--frames", type=int, required=True)
    ap.add_argument("--layout", default="auto", choices=["auto", "row", "col", "grid"])
    ap.add_argument("--grid", default="", help="COLUMNSxROWS, e.g. 4x2")
    ap.add_argument("--cols", type=int, default=0, help="explicit column count (overrides --grid)")
    ap.add_argument("--rows", type=int, default=0, help="explicit row count (overrides --grid)")
    ap.add_argument("--anchor", type=float, default=-1.0,
                    help="fixed crop anchor (0..1 of the cell width); -1 = auto")
    ap.add_argument("--target", default="1920x960", help="WxH of every output frame")
    ap.add_argument("--gutter", default="auto", choices=["auto", "off"])
    ap.add_argument("--report", default="")
    args = ap.parse_args()

    src = Path(args.image)
    outdir = Path(args.out)
    tw, th = (int(v) for v in args.target.lower().split("x"))
    if not src.exists():
        print(f"[slice] image not found: {src}", file=sys.stderr)
        return 2
    outdir.mkdir(parents=True, exist_ok=True)

    im = Image.open(src).convert("RGB")
    iw, ih = im.size
    if args.cols and args.rows:
        layout, cols, rows = "grid", int(args.cols), int(args.rows)
    else:
        layout, cols, rows = auto_layout(iw, ih, args.frames, tw, th, args.grid)
    if args.layout in ("row", "col"):
        layout = args.layout
        cols, rows = (args.frames, 1) if layout == "row" else (1, args.frames)

    gray = np.asarray(im.convert("L"))
    x0, y0, x1, y1 = content_bbox(gray)
    notes = [f"content bbox {x0},{y0}-{x1},{y1} of {iw}x{ih}"]
    vruns = dark_runs(gray, 0) if args.gutter == "auto" else []
    hruns = dark_runs(gray, 1) if args.gutter == "auto" else []

    if layout == "grid":
        xsegs, xnote = segments((x0, x1), vruns, cols)
        ysegs, ynote = segments((y0, y1), hruns, rows)
        notes += [f"columns: {xnote}", f"rows: {ynote}"]
        cells = []
        for r in range(rows):
            for c in range(cols):
                cells.append((xsegs[c][0], ysegs[r][0], xsegs[c][1], ysegs[r][1]))
    elif layout == "row":
        xsegs, xnote = segments((x0, x1), vruns, args.frames)
        notes.append(f"columns: {xnote}")
        cells = [(a, y0, b, y1) for (a, b) in xsegs]
    else:  # col
        ysegs, ynote = segments((y0, y1), hruns, args.frames)
        notes.append(f"rows: {ynote}")
        cells = [(x0, a, x1, b) for (a, b) in ysegs]

    written = []
    colours = []
    anchors = []
    for i, (a, b, c, d) in enumerate(cells, 1):
        cell = im.crop((int(a), int(b), int(c), int(d)))
        ax = args.anchor if args.anchor >= 0 else energy_anchor(cell)
        anchors.append(round(ax, 3))
        cell = crop_to_aspect(cell, tw, th, anchor_x=ax)
        p = outdir / f"frame-{i:02d}.png"
        cell.save(p)
        written.append(str(p))
        arr = np.asarray(cell.convert("RGB"), dtype=float)
        colours.append([int(arr[:, :, k].mean()) for k in range(3)])

    report = {"image": str(src), "canvas": [iw, ih], "layout": layout,
              "cols": cols, "rows": rows, "frames": args.frames,
              "target": [tw, th], "cells": cells, "notes": notes,
              "crop_anchors": anchors, "mean_rgb": colours, "written": written}
    if args.report:
        V.jdump(report, Path(args.report))
    V.jdump(report, outdir / "slice_report.json")
    print(f"[slice] {src.name}  {iw}x{ih} -> {layout} {cols}x{rows}  "
          f"{len(written)} frames -> {outdir}")
    for n in notes:
        print(f"[slice]   {n}")
    print(f"[slice]   mean rgb per frame: {colours}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
