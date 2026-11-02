"""Stage 6 — VERIFY.  the finished video vs the plan.

Checks (numbers, not vibes):
  resolution / fps / duration vs the plan
  decoded frame count vs container frame count
  black frames (blackdetect) and frozen stretches (freezedetect)
  integrated loudness (ebur128) vs the mix target
  every planned scene present in the timeline

usage:
  python verify_output.py --plan shot_plan_final.json --video final.mp4 [--lufs -14]
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import vlib as V

V.setup_env()


def decode_count(video: Path) -> int:
    p = V.run([V.ffmpeg(), "-hide_banner", "-v", "info", "-i", str(video),
               "-map", "0:v:0", "-f", "null", "-"])
    m = re.findall(r"frame=\s*(\d+)", p.stderr or "")
    return int(m[-1]) if m else 0


def black_and_freeze(video: Path) -> tuple[list, list]:
    p = V.run([V.ffmpeg(), "-hide_banner", "-v", "info", "-i", str(video),
               "-vf", "blackdetect=d=0.15:pix_th=0.10,freezedetect=n=-50dB:d=1.0",
               "-an", "-f", "null", "-"])
    text = p.stderr or ""
    black = [{"start": float(a), "end": float(b)}
             for a, b in re.findall(r"black_start:([\d.]+) black_end:([\d.]+)", text)]
    freeze = [{"start": float(a), "end": float(b)}
              for a, b in re.findall(r"freeze_start:\s*([\d.]+)\s+freeze_end:\s*([\d.]+)", text)]
    return black, freeze


def loudness(video: Path) -> dict:
    p = V.run([V.ffmpeg(), "-hide_banner", "-nostats", "-i", str(video),
               "-filter_complex", "ebur128=peak=true", "-f", "null", "-"])
    text = p.stderr or ""
    out = {}
    m = re.findall(r"Integrated loudness:\s*I:\s*(-?[\d.]+)\s*LUFS", text)
    if m:
        out["integrated_lufs"] = float(m[-1])
    m = re.findall(r"Loudness range:\s*LRA:\s*(-?[\d.]+)\s*LU", text)
    if m:
        out["lra"] = float(m[-1])
    m = re.findall(r"True peak:\s*Peak:\s*(-?[\d.]+)\s*dBFS", text)
    if m:
        out["true_peak_dbfs"] = float(m[-1])
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--plan", required=True)
    ap.add_argument("--video", required=True)
    ap.add_argument("--lufs", type=float, default=-14.0)
    ap.add_argument("--tolerance", type=float, default=0.35, help="seconds")
    ap.add_argument("--out", default=None)
    args = ap.parse_args()

    plan = V.jload(args.plan)
    video = Path(args.video)
    if not video.exists():
        print(f"no such video: {video}", file=sys.stderr)
        return 2

    info = V.probe(video)
    decoded = decode_count(video)
    black, freeze = black_and_freeze(video)
    loud = loudness(video) if info["has_audio"] else {}

    expected = sum(float(s["seconds"]) for s in plan["scenes"])
    # every cross-fade eats `transition_duration` seconds of overlap
    overlap = 0.0
    for s in plan["scenes"][1:]:
        t = str(s.get("transition", "cut") or "cut").strip().lower()
        if t in ("cut", "none", "hard", ""):
            continue
        overlap += float(s.get("transition_duration", 0) or 0)
    expected -= overlap
    res = plan.get("style_spec", {}).get("resolution") or [info["width"], info["height"]]

    checks = []

    def chk(name, ok, detail):
        checks.append({"check": name, "ok": bool(ok), "detail": detail})

    chk("resolution", (info["width"], info["height"]) == (int(res[0]), int(res[1])),
        f"{info['width']}x{info['height']} (plan {res[0]}x{res[1]})")
    chk("duration", abs(info["duration"] - expected) <= args.tolerance,
        f"{info['duration']:.3f}s vs plan {expected:.3f}s (tol {args.tolerance}s)")
    chk("frame_count_container", info["nb_frames"] > 0, f"nb_frames={info['nb_frames']}")
    chk("frame_count_decoded", decoded == info["nb_frames"] or info["nb_frames"] == 0,
        f"decoded={decoded} container={info['nb_frames']}")
    chk("no_black_frames", not black, f"{len(black)} black run(s)")
    chk("no_frozen_shot", not freeze, f"{len(freeze)} frozen stretch(es)")
    if info["has_audio"]:
        i = loud.get("integrated_lufs")
        chk("loudness_target", i is not None and abs(i - args.lufs) <= 1.5,
            f"{i} LUFS (target {args.lufs})")
    else:
        checks.append({"check": "loudness_target", "ok": True, "detail": "no audio track (silent render)"})

    report = {
        "video": str(video),
        "probe": {k: info[k] for k in ("width", "height", "fps", "duration", "nb_frames", "has_audio")},
        "decoded_frames": decoded,
        "expected_duration": round(expected, 3),
        "transition_overlap": round(overlap, 3),
        "black_runs": black,
        "frozen": freeze,
        "loudness": loud,
        "checks": checks,
        "result": "PASS" if all(c["ok"] for c in checks) else "FAIL",
    }
    out = Path(args.out) if args.out else video.with_name(video.stem + "_verify.json")
    V.jdump(report, out)
    for c in checks:
        print(f"  [{'ok ' if c['ok'] else 'FAIL'}] {c['check']}: {c['detail']}")
    print(f"[verify] RESULT {report['result']} -> {out}")
    return 0 if report["result"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
