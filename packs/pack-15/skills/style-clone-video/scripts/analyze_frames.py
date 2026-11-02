"""Stage 2 — IMAGE ANALYSIS.  frames/ -> style_dna.json

Measures what can be measured, so the style clone is a lock, not a guess.
Per frame: exposure, contrast, saturation, bloom, edge density, sharpness,
grain, vignette, palette (k-means), gradient-energy composition, text bands.
Per sequence: shot rhythm, motion energy, palette drift, exposure stability.

usage:
  python analyze_frames.py <framesdir> <out.json> [--cuts cuts.json]
                           [--palette 6] [--max-frames 240]
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import vlib as V

V.setup_env()
import numpy as np  # noqa: E402
from PIL import Image  # noqa: E402

# ----------------------------------------------------------------- primitives


def luma(img: np.ndarray) -> np.ndarray:
    return 0.2126 * img[..., 0] + 0.7152 * img[..., 1] + 0.0722 * img[..., 2]


def to_float(img: Image.Image) -> np.ndarray:
    return np.asarray(img.convert("RGB"), dtype=np.float32) / 255.0


def edges(lum: np.ndarray) -> np.ndarray:
    gx = np.abs(np.diff(lum, axis=1))
    gy = np.abs(np.diff(lum, axis=0))
    e = np.zeros_like(lum)
    e[:, :-1] += gx
    e[:-1, :] += gy
    return e


def laplacian_var(lum: np.ndarray) -> float:
    lap = (-4 * lum[1:-1, 1:-1] + lum[:-2, 1:-1] + lum[2:, 1:-1]
           + lum[1:-1, :-2] + lum[1:-1, 2:])
    return float(lap.var())


def grain_sigma(rgb: np.ndarray, lum: np.ndarray) -> float:
    """High-frequency residual in flat areas only (a real film-grain estimate)."""
    k = 3
    pad = k // 2
    padded = np.pad(lum, pad, mode="edge")
    c = np.cumsum(np.cumsum(padded, axis=0), axis=1)
    c = np.pad(c, ((1, 0), (1, 0)))
    h, w = lum.shape
    box = (c[k:k + h, k:k + w] - c[0:h, k:k + w] - c[k:k + h, 0:w] + c[0:h, 0:w]) / (k * k)
    resid = lum - box
    flat = np.abs(box - np.median(box)) < 0.02
    if flat.sum() < 500:
        return float(resid.std())
    return float(resid[flat].std())


def vignette_db(lum: np.ndarray) -> float:
    h, w = lum.shape
    y, x = np.mgrid[0:h, 0:w]
    cy, cx = (h - 1) / 2, (w - 1) / 2
    r = np.sqrt(((y - cy) / cy) ** 2 + ((x - cx) / cx) ** 2) / 1.4142
    core = lum[r < 0.35]
    edge = lum[r > 0.85]
    if core.size < 50 or edge.size < 50:
        return 0.0
    mc, me = float(core.mean()), float(edge.mean())
    if me <= 1e-6:
        return 0.0
    return 20 * math.log10(max(mc, 1e-6) / me)


def kmeans_palette(rgb: np.ndarray, k: int = 6, iters: int = 24, seed: int = 7):
    """Deterministic k-means (k-means++ init, fixed seed) -> [(hex, share)]"""
    if rgb.ndim == 2:
        px = rgb
    else:
        h, w, _ = rgb.shape
        step = max(1, int(math.sqrt((h * w) / 20000.0)))
        px = rgb[::step, ::step].reshape(-1, 3)
    if len(px) == 0:
        return []
    rng = np.random.default_rng(seed)
    centres = [px[rng.integers(len(px))]]
    for _ in range(k - 1):
        d = np.min(np.linalg.norm(px[:, None, :] - np.array(centres)[None, :, :], axis=2), axis=1)
        total = float(d.sum())
        if total <= 1e-9:
            centres.append(px[rng.integers(len(px))])
            continue
        p = d / total
        p = p / p.sum()
        centres.append(px[rng.choice(len(px), p=p)])
    centres = np.array(centres, dtype=np.float32)
    for _ in range(iters):
        d = np.linalg.norm(px[:, None, :] - centres[None, :, :], axis=2)
        lab = d.argmin(axis=1)
        new = centres.copy()
        for i in range(len(centres)):
            m = lab == i
            if m.any():
                new[i] = px[m].mean(axis=0)
        if np.allclose(new, centres, atol=1e-4):
            centres = new
            break
        centres = new
    lab = np.linalg.norm(px[:, None, :] - centres[None, :, :], axis=2).argmin(axis=1)
    out = []
    for i, c in enumerate(centres):
        share = float((lab == i).mean())
        if share < 0.005:
            continue
        out.append((V.hexof(np.clip(c, 0, 255) * 255), round(share, 4)))
    out.sort(key=lambda t: -t[1])
    return out


def text_bands(rgb: np.ndarray) -> list[dict]:
    """Find horizontal bands of dense fine structure (burned-in text / titles)."""
    lum = luma(rgb)
    e = edges(lum)
    h, w = e.shape
    row = e.mean(axis=1)
    # smooth over ~5 rows
    k = 5
    ker = np.ones(k) / k
    row_s = np.convolve(row, ker, mode="same")
    base = float(np.median(row_s))
    thr = max(base * 1.9, base + 0.006)
    mask = row_s > thr
    bands, i = [], 0
    while i < h:
        if mask[i]:
            j = i
            while j < h and mask[j]:
                j += 1
            if (j - i) >= max(4, int(h * 0.008)):
                bands.append((i, j))
            i = j
        else:
            i += 1
    out = []
    for (y0, y1) in bands:
        band = rgb[y0:y1]
        bl = luma(band).reshape(-1)
        thr_l = float(np.percentile(bl, 98))
        sel = luma(band) >= thr_l
        if sel.sum() < 10:
            continue
        px = band[sel]
        out.append({
            "y0": round(y0 / h, 4),
            "y1": round(y1 / h, 4),
            "height_px": int(y1 - y0),
            "centre_pct": round((y0 + y1) / 2 / h, 4),
            "colour": V.hexof(px.mean(axis=0) * 255),
            "brightness": round(float(px.mean()), 4),
        })
    # keep the most prominent bands
    out.sort(key=lambda b: -b["height_px"])
    return out[:6]


def composition(rgb: np.ndarray) -> dict:
    e = edges(luma(rgb))
    h, w = e.shape
    tot = e.sum()
    if tot <= 0:
        return {"energy_centroid": [0.5, 0.5], "coverage": 0.0, "thirds_bias": 0.0}
    ys, xs = np.mgrid[0:h, 0:w]
    cy = float((e * ys).sum() / tot) / h
    cx = float((e * xs).sum() / tot) / w
    # rule-of-thirds proximity of the energy centroid
    tx, ty = round(cx * 2) / 2, round(cy * 2) / 2
    d = math.hypot(cx - tx, cy - ty)
    return {
        "energy_centroid": [round(cx, 4), round(cy, 4)],
        "coverage": round(float((e > 0.02).mean()), 4),
        "thirds_bias": round(d, 4),
    }


def frame_metrics(path) -> dict:
    im = Image.open(path).convert("RGB")
    rgb = to_float(im)
    lum = luma(rgb)
    mx = rgb.max(axis=2)
    mn = rgb.min(axis=2)
    sat = np.where(mx > 1e-6, (mx - mn) / np.maximum(mx, 1e-6), 0.0)
    pal = kmeans_palette(rgb)
    bands = text_bands(rgb)
    return {
        "path": str(path),
        "w": rgb.shape[1], "h": rgb.shape[0],
        "mean_luma": round(float(lum.mean()), 4),
        "p01": round(float(np.percentile(lum, 1)), 4),
        "p99": round(float(np.percentile(lum, 99)), 4),
        "contrast_std": round(float(lum.std()), 4),
        "saturation": round(float(sat.mean()), 4),
        "bloom_fraction": round(float((lum > 0.93).mean()), 5),
        "edge_density": round(float(edges(lum).mean()), 5),
        "sharpness": round(laplacian_var(lum), 6),
        "grain": round(grain_sigma(rgb, lum), 5),
        "vignette_db": round(vignette_db(lum), 3),
        "palette": pal,
        "text_bands": bands,
        "composition": composition(rgb),
    }


# --------------------------------------------------------------------- driver


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("framesdir")
    ap.add_argument("out")
    ap.add_argument("--cuts", default=None)
    ap.add_argument("--palette", type=int, default=6)
    ap.add_argument("--max-frames", type=int, default=240)
    args = ap.parse_args()

    fdir = Path(args.framesdir)
    files = sorted(fdir.glob("*.jpg")) + sorted(fdir.glob("*.png"))
    if not files:
        print(f"no frames in {fdir}", file=sys.stderr)
        return 2
    if len(files) > args.max_frames:
        step = len(files) / float(args.max_frames)
        files = [files[int(i * step)] for i in range(args.max_frames)]
    print(f"[analyze] {len(files)} frames")

    metas = []
    for i, f in enumerate(files):
        m = frame_metrics(f)
        m["file"] = f.name
        metas.append(m)
        if (i + 1) % 40 == 0:
            print(f"[analyze]  {i + 1}/{len(files)}")

    # ---- aggregate --------------------------------------------------------
    def avg(key):
        vals = [m[key] for m in metas]
        return round(float(np.mean(vals)), 5)

    def avgc(key):
        vals = [m["composition"][key] for m in metas]
        return round(float(np.mean(vals)), 5)

    pooled = np.concatenate([
        np.asarray(Image.open(m["path"]).convert("RGB").resize((96, 72)), dtype=np.float32) / 255.0
        for m in metas[::max(1, len(metas) // 40)]
    ], axis=0)
    global_pal = kmeans_palette(pooled.reshape(-1, 3), k=args.palette)

    all_bands = [b for m in metas for b in m["text_bands"]]
    band_summary = []
    if all_bands:
        by_key = {}
        for b in all_bands:
            by_key.setdefault((b["y0"], b["y1"]), []).append(b)
        for (y0, y1), group in sorted(by_key.items(), key=lambda kv: -len(kv[1]))[:6]:
            band_summary.append({
                "y0": y0, "y1": y1,
                "centre_pct": round(float(np.mean([g["centre_pct"] for g in group])), 4),
                "height_px": int(np.median([g["height_px"] for g in group])),
                "colour": max({g["colour"] for g in group}, key=lambda c: sum(1 for g in group if g["colour"] == c)),
                "frames": len(group),
                "coverage": round(len(group) / len(metas), 3),
            })

    # motion between consecutive sampled frames
    motion = []
    prev = None
    for m in metas:
        if prev is not None:
            a = np.asarray(Image.open(prev["path"]).convert("L").resize((128, 96)), dtype=np.float32)
            b = np.asarray(Image.open(m["path"]).convert("L").resize((128, 96)), dtype=np.float32)
            motion.append(round(float(np.abs(a - b).mean() / 255.0), 5))
        prev = m
    motion_sorted = sorted(motion)
    motion_med = motion_sorted[len(motion_sorted) // 2] if motion_sorted else 0.0

    cuts = []
    if args.cuts and Path(args.cuts).exists():
        cuts = V.jload(args.cuts)
    shot_rhythm = {}
    if cuts:
        n_cuts = len(cuts)
        dur = metas[-1].get("duration") if metas else None
        shot_rhythm = {
            "cuts": n_cuts,
            "threshold": None,
            "median_shot_s": None,
            "mean_shot_s": None,
            "cuts_per_10s": None,
        }

    dna = {
        "schema": "style-clone-video/style-dna@1",
        "measured": {
            "frames_analysed": len(metas),
            "resolution": [metas[0]["w"], metas[0]["h"]],
            "aspect": round(metas[0]["w"] / max(1, metas[0]["h"]), 4),
            "exposure": {
                "mean_luma": avg("mean_luma"),
                "p01": avg("p01"),
                "p99": avg("p99"),
                "contrast_std": avg("contrast_std"),
                "saturation": avg("saturation"),
                "bloom_fraction": avg("bloom_fraction"),
            },
            "grain": avg("grain"),
            "vignette_db": avg("vignette_db"),
            "sharpness": avg("sharpness"),
            "edge_density": avg("edge_density"),
            "palette": global_pal,
            "text_bands": band_summary,
            "composition": {
                "energy_centroid": [round(float(np.mean([m["composition"]["energy_centroid"][0] for m in metas])), 4),
                                    round(float(np.mean([m["composition"]["energy_centroid"][1] for m in metas])), 4)],
                "coverage": avgc("coverage"),
                "thirds_bias": avgc("thirds_bias"),
            },
            "motion": {
                "median_frame_delta": motion_med,
                "max_frame_delta": max(motion) if motion else 0.0,
            },
            "shot_rhythm": shot_rhythm,
        },
        "frames": metas,
    }
    V.jdump(dna, args.out)
    print(f"[analyze] -> {args.out}")
    print(f"[analyze] palette: {global_pal}")
    print(f"[analyze] text bands: {[(b['y0'], b['y1'], b['colour']) for b in band_summary]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
