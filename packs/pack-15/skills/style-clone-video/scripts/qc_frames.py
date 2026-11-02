"""Stage 8 - the QUALITY CHECK loop.

"The single biggest upgrade over a one-shot render is to render it, look at a
frame every half second, critique it like a senior motion designer, fix
everything and repeat."

This script does the mechanical half of that loop:
  1. samples a frame every N seconds
  2. burns the timestamp on it so it can be located in the timeline
  3. builds contact sheets the agent can actually LOOK at
  4. measures each frame and flags the things a frame cannot hide:
     black frames, frozen stretches, blown highlights, motion gaps

The agent then reads the contact sheets, writes the critique, fixes the plan,
re-renders and runs this again. Aim for at least 4 rounds.

Usage:
  python qc_frames.py --video out.mp4 --outdir qc [--every 0.5]
                       [--width 384] [--cols 4] [--report qc_report.json]
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import vlib  # noqa: E402


def sample_frames(video: str, outdir: Path, every: float, width: int) -> list[Path]:
    outdir.mkdir(parents=True, exist_ok=True)
    for old in outdir.glob("q_*.png"):
        old.unlink()
    rate = 1.0 / max(every, 0.04)
    cmd = [
        vlib.ffmpeg(), "-y", "-hide_banner", "-v", "error", "-i", video,
        "-vf", f"fps={rate:.6f},scale={width}:-2:flags=area",
        "-fps_mode", "passthrough", str(outdir / "q_%04d.png"),
    ]
    vlib.must_run(cmd)
    return sorted(outdir.glob("q_*.png"))


def metrics(path: Path) -> dict:
    import cv2
    import numpy as np

    img = cv2.imread(str(path), cv2.IMREAD_COLOR)
    if img is None:
        return {}
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    h, w = gray.shape
    lap = cv2.Laplacian(gray, cv2.CV_64F).var()
    return {
        "mean_luma": float(gray.mean() / 255.0),
        "p01": float(np.percentile(gray, 1) / 255.0),
        "p99": float(np.percentile(gray, 99) / 255.0),
        "std": float(gray.std() / 255.0),
        "black_ratio": float((gray < 10).mean()),
        "blown_ratio": float((gray > 245).mean()),
        "sharpness": float(lap),
        "size": [w, h],
    }


def build_sheets(frames: list[Path], outdir: Path, cols: int, every: float,
                 width: int, per_sheet: int = 24) -> list[str]:
    from PIL import Image, ImageDraw

    font = vlib.load_font(14)
    sheets = []
    for s in range(0, len(frames), per_sheet):
        chunk = frames[s:s + per_sheet]
        if not chunk:
            continue
        with Image.open(chunk[0]) as im0:
            tw, th = im0.size
        rows = (len(chunk) + cols - 1) // cols
        pad, label = 4, 18
        W = cols * (tw + pad) + pad
        H = rows * (th + pad + label) + pad
        sheet = Image.new("RGB", (W, H), (12, 12, 12))
        draw = ImageDraw.Draw(sheet)
        for i, fp in enumerate(chunk):
            idx = s + i
            with Image.open(fp).convert("RGB") as im:
                x = pad + (i % cols) * (tw + pad)
                y = pad + (i // cols) * (th + pad + label)
                sheet.paste(im, (x, y))
                t = idx * every
                draw.text((x + 2, y + th + 2), f"{t:6.2f}s  #{idx + 1}",
                          font=font, fill=(200, 200, 200))
        out = outdir / f"qc_sheet_{s // per_sheet + 1:02d}.png"
        sheet.save(out)
        sheets.append(str(out))
    return sheets


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--video", required=True)
    ap.add_argument("--outdir", required=True)
    ap.add_argument("--every", type=float, default=0.5)
    ap.add_argument("--width", type=int, default=384)
    ap.add_argument("--cols", type=int, default=4)
    ap.add_argument("--report", default="")
    args = ap.parse_args()

    outdir = Path(args.outdir)
    frames = sample_frames(args.video, outdir, args.every, args.width)
    if not frames:
        print("[qc] no frames sampled")
        return 1

    rows = []
    prev = None
    frozen_run = 0
    for i, fp in enumerate(frames):
        m = metrics(fp)
        if not m:
            continue
        m["index"] = i + 1
        m["t"] = round(i * args.every, 3)
        m["file"] = str(fp)
        if prev is not None:
            import cv2
            import numpy as np

            a = cv2.imread(str(prev), cv2.IMREAD_GRAYSCALE).astype(np.float32)
            b = cv2.imread(str(fp), cv2.IMREAD_GRAYSCALE).astype(np.float32)
            m["delta"] = float(np.abs(a - b).mean())
            frozen_run = frozen_run + 1 if m["delta"] < 0.35 else 0
            m["frozen_streak"] = frozen_run
        prev = fp
        flags = []
        if m["mean_luma"] < 0.02 or m["black_ratio"] > 0.92:
            flags.append("BLACK")
        if m.get("frozen_streak", 0) >= 3:
            flags.append("FROZEN")
        if m["blown_ratio"] > 0.30:
            flags.append("BLOWN")
        if m["std"] < 0.01:
            flags.append("FLAT")
        m["flags"] = flags
        rows.append(m)

    sheets = build_sheets(frames, outdir, args.cols, args.every, args.width)
    flagged = [r for r in rows if r["flags"]]
    report = {
        "video": args.video,
        "sampled_every_s": args.every,
        "frames_sampled": len(rows),
        "sheets": sheets,
        "flagged": flagged,
        "frames": rows,
    }
    rp = Path(args.report) if args.report else outdir / "qc_report.json"
    vlib.jdump(report, rp)

    print(f"[qc] {len(rows)} frames every {args.every}s -> {len(sheets)} sheet(s)")
    for s in sheets:
        print(f"[qc] sheet: {s}")
    if flagged:
        print(f"[qc] FLAGGED {len(flagged)} frame(s):")
        for r in flagged[:40]:
            print(f"       t={r['t']:7.2f}s  {','.join(r['flags'])}  "
                  f"luma={r['mean_luma']:.3f} delta={r.get('delta', 0):.3f}")
    else:
        print("[qc] no mechanical flags (black/frozen/blown/flat)")
    print(f"[qc] report: {rp}")
    print("[qc] NOW LOOK at every sheet with the read tool, critique it like a "
          "senior motion designer, fix the plan, re-render, run again. >= 4 rounds.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
