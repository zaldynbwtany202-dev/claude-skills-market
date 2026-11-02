"""Stage 1 — REFERENCE -> FRAMES.

Turns a reference video into an inspectable frame set:
  probe.json      video spec (size, fps, duration, audio)
  cuts.json       hard-cut list with scene scores
  frames/         sampled frames (timestamp-accurate, VFR safe)
  keyframes/      full-res frames straddling every cut
  sheets/         contact sheets with burned-in timecode
  frames.json     index of every extracted frame with its exact source time

usage:
  python extract_frames.py <video> <outdir> [--fps 2] [--scene 0.25] [--tile 384]
"""
from __future__ import annotations

import argparse
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import vlib as V

V.setup_env()
from PIL import Image, ImageDraw  # noqa: E402


def pick_indices(pts: list[float], fps: float) -> list[int]:
    """Source frame indices closest to each k/fps grid point."""
    if not pts:
        return []
    step = 1.0 / fps if fps > 0 else 1.0
    out, last = [], -1
    k = 0
    while k * step <= pts[-1] + 1e-9:
        target = k * step
        idx = 0
        for i, t in enumerate(pts):
            if t >= target - 1e-6:
                idx = i
                break
        else:
            idx = len(pts) - 1
        if idx != last:
            out.append(idx)
            last = idx
        k += 1
    return out


def _uniform_stride(indices: list[int]) -> int:
    """If indices are 0, S, 2S, ... return S, else 0."""
    if len(indices) < 3 or indices[0] != 0:
        return 0
    step = indices[1] - indices[0]
    if step < 2:
        return 0
    for i, v in enumerate(indices):
        if v != i * step:
            return 0
    return step


def _select_pass(src: Path, indices: list[int], out_dir: Path, prefix: str,
                 start_number: int) -> list[Path]:
    """One ffmpeg pass for a chunk of frames: select 'eq(n,i)+eq(n,j)+...'."""
    expr = "+".join(f"eq(n\\,{i})" for i in indices)
    cmd = [
        V.ffmpeg(), "-hide_banner", "-v", "error", "-y", "-i", str(src),
        "-vf", f"select='{expr}'", "-fps_mode", "passthrough", "-q:v", "2",
        "-start_number", str(start_number), str(out_dir / f"{prefix}%05d.jpg"),
    ]
    V.must_run(cmd)
    return sorted(out_dir.glob(f"{prefix}*.jpg"))


def extract_indices(src: Path, indices: list[int], out_dir: Path, prefix: str) -> list[Path]:
    """Extract exact frame indices.

    ffmpeg cannot parse a select expression with thousands of terms ("Error while
    parsing expression"), so the indices are extracted in chunks of CHUNK frames.
    If a chunk still fails we fall back to one ffmpeg call per frame.
    """
    if not indices:
        return []
    out_dir.mkdir(parents=True, exist_ok=True)
    for old in out_dir.glob(f"{prefix}*.jpg"):
        old.unlink()
    CHUNK = 60
    files: list[Path] = []
    try:
        # Uniform grid -> one short expression, one decode of the whole video.
        stride = _uniform_stride(indices)
        if stride:
            cmd = [
                V.ffmpeg(), "-hide_banner", "-v", "error", "-y", "-i", str(src),
                "-vf", f"select='not(mod(n\\,{stride}))'", "-fps_mode", "passthrough",
                "-q:v", "2", str(out_dir / f"{prefix}%05d.jpg"),
            ]
            V.must_run(cmd)
            files = sorted(out_dir.glob(f"{prefix}*.jpg"))
            if len(files) == len(indices):
                return files
            for old in out_dir.glob(f"{prefix}*.jpg"):
                old.unlink()
            files = []
        for c0 in range(0, len(indices), CHUNK):
            chunk = indices[c0:c0 + CHUNK]
            got = _select_pass(src, chunk, out_dir, prefix, len(files) + 1)
            if len(got) != len(chunk):
                raise RuntimeError(
                    f"chunk {c0 // CHUNK}: expected {len(chunk)} frames, got {len(got)}")
            files = sorted(out_dir.glob(f"{prefix}*.jpg"))
    except Exception as exc:  # noqa: BLE001 - any failure -> per-frame fallback
        print(f"[extract] batch extract failed ({exc}); falling back to per-frame")
        for old in out_dir.glob(f"{prefix}*.jpg"):
            old.unlink()
        files = []
        for i, idx in enumerate(indices):
            one = out_dir / f"{prefix}{i + 1:05d}.jpg"
            V.must_run([
                V.ffmpeg(), "-hide_banner", "-v", "error", "-y", "-i", str(src),
                "-vf", f"select='eq(n\\,{idx})'", "-fps_mode", "passthrough",
                "-frames:v", "1", "-q:v", "2", str(one),
            ])
            files.append(one)
    files = sorted(out_dir.glob(f"{prefix}*.jpg"))
    return files


def make_sheets(frames: list[dict], out_dir: Path, tile_w: int, cols: int = 4, rows: int = 4):
    out_dir.mkdir(parents=True, exist_ok=True)
    for old in out_dir.glob("sheet_*.jpg"):
        old.unlink()
    per = cols * rows
    sheets = []
    for si in range(math.ceil(len(frames) / per)):
        chunk = frames[si * per:(si + 1) * per]
        if not chunk:
            break
        first = Image.open(chunk[0]["path"])
        ar = first.height / first.width
        tw, th = tile_w, max(1, int(round(tile_w * ar)))
        pad, bar = 4, 22
        sheet = Image.new("RGB", (cols * tw + (cols + 1) * pad, rows * (th + bar) + (rows + 1) * pad), (16, 16, 16))
        draw = ImageDraw.Draw(sheet)
        font = V.load_font(15)
        for i, fr in enumerate(chunk):
            r, c = divmod(i, cols)
            x = pad + c * (tw + pad)
            y = pad + r * (th + bar + pad)
            try:
                im = Image.open(fr["path"]).convert("RGB").resize((tw, th), Image.LANCZOS)
            except Exception:
                continue
            sheet.paste(im, (x, y))
            draw.rectangle([x, y + th, x + tw, y + th + bar], fill=(24, 24, 24))
            draw.text((x + 4, y + th + 3), f"{fr['t']:7.3f}s  #{fr['index']}", fill=(235, 235, 235), font=font)
        path = out_dir / f"sheet_{si + 1:02d}.jpg"
        sheet.save(path, quality=88)
        sheets.append(str(path))
    return sheets


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("video")
    ap.add_argument("outdir")
    ap.add_argument("--fps", type=float, default=2.0, help="sampling grid (0 = every frame)")
    ap.add_argument("--scene", type=float, default=0.25, help="scene-score threshold for cuts")
    ap.add_argument("--tile", type=int, default=384)
    ap.add_argument("--cols", type=int, default=4)
    ap.add_argument("--rows", type=int, default=4)
    args = ap.parse_args()

    src = Path(args.video)
    out = Path(args.outdir)
    if not src.exists():
        print(f"no such video: {src}", file=sys.stderr)
        return 2
    out.mkdir(parents=True, exist_ok=True)

    info = V.probe(src)
    V.jdump(info, out / "probe.json")
    print(f"[extract] {src.name}  {info['width']}x{info['height']}  fps={info['fps']}  "
          f"dur={info['duration']:.3f}s  audio={info['has_audio']}")

    cuts = V.scene_cuts(src, args.scene)
    V.jdump(cuts, out / "cuts.json")
    print(f"[extract] {len(cuts)} hard cuts @ scene>{args.scene}")

    pts = V.frame_pts(src)
    if not pts:
        print("[extract] no frame timestamps", file=sys.stderr)
        return 3
    n = len(pts)
    print(f"[extract] {n} frames  first={pts[0]:.3f}  last={pts[-1]:.3f}")

    # ---- sampled frames ----------------------------------------------------
    if args.fps > 0:
        idxs = pick_indices(pts, args.fps)
    else:
        idxs = list(range(n))
    files = extract_indices(src, idxs, out / "frames", "f_")
    frames = []
    for j, idx in enumerate(idxs):
        if j < len(files):
            frames.append({"index": idx, "t": round(pts[idx], 4), "path": str(files[j])})
    V.jdump(frames, out / "frames.json")
    print(f"[extract] {len(frames)} sampled frames -> frames/")

    # ---- keyframes around every cut ---------------------------------------
    key_idx, seen = [], set()
    for c in cuts:
        t = c["t"]
        before = max(0, min(n - 1, next((i for i in range(n - 1, -1, -1) if pts[i] <= t + 1e-6), 0)))
        after = max(0, min(n - 1, next((i for i in range(n) if pts[i] >= t - 1e-6), n - 1)))
        for i in (before, after):
            if i not in seen:
                seen.add(i)
                key_idx.append(i)
    key_idx.sort()
    kfiles = extract_indices(src, key_idx, out / "keyframes", "k_")
    keys = [{"index": i, "t": round(pts[i], 4), "path": str(p)}
            for i, p in zip(key_idx, kfiles)]
    V.jdump(keys, out / "keyframes.json")
    print(f"[extract] {len(keys)} keyframes -> keyframes/")

    sheets = make_sheets(frames, out / "sheets", args.tile, args.cols, args.rows)
    print(f"[extract] {len(sheets)} contact sheets -> sheets/")

    V.jdump({"video": str(src), "frames": len(frames), "keyframes": len(keys),
             "sheets": sheets, "cuts": len(cuts)}, out / "extract_report.json")
    print("[extract] done")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
