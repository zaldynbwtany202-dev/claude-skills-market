"""Stage 5 — MONTAGE.  motion clips -> the finished video.

Cuts land on the scene grid (already beat-snapped in the plan).  Transitions are
PER SCENE: a scene may open on a hard cut or on a motivated reveal.  Hard cuts
break the transition chain (the professional rule: never the same transition
twice in a row, mix hard cuts with reveals), so the montage is assembled as
RUNS of cross-faded shots that are then concatenated.

  python montage.py --plan shot_plan_final.json --clips <dir> --out final.mp4
                    [--music bed.mp3] [--vo vo.wav] [--xfade 0.45]
                    [--transition-mode plan|auto|hard] [--music-db -12] [--lufs -14]

Transition vocabulary (ffmpeg xfade): hard cut + these reveals
  fade  fadeblack  fadewhite  dissolve  radial  smoothleft  smoothright
  slideleft  slideright  slideup  slidedown  circleopen  circleclose
  wipeleft  wiperight  wipeup  wipedown  zoomin  zoomout  hblur  pixelize
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import vlib as V

V.setup_env()

# Professional reveal vocabulary.  Hard cuts are always allowed and never
# count as "the same transition twice" (a cut is not a transition).
REVEALS = ["fade", "fadeblack", "fadewhite", "dissolve", "radial", "smoothleft",
           "smoothright", "slideleft", "slideright", "slideup", "slidedown",
           "circleopen", "circleclose", "wipeleft", "wiperight", "wipeup",
           "wipedown", "zoomin", "zoomout", "hblur", "pixelize"]

ALIASES = {
    "dipblack": "fadeblack", "dip": "fadeblack", "dip-to-black": "fadeblack",
    "flash": "fadewhite", "white": "fadewhite", "burn": "fadewhite",
    "whip": "slideleft",
}

# Rotation used when the plan does not name a transition: mostly hard cuts with
# a motivated reveal every few shots, and never the same reveal twice in a row.
AUTO_ROTATION = ["cut", "cut", "fade", "cut", "fadeblack", "cut", "cut",
                 "fade", "cut", "fadewhite", "cut", "dissolve", "cut",
                 "zoomin", "cut", "smoothleft"]

VALID = {"cut", "none", "hard"} | set(REVEALS) | set(ALIASES)


def duration_for(style: str, base: float) -> float:
    """Reveal lengths.  A dissolve between two different locations is a
    mistake, so the soft reveals stay SHORT; only a motivated light
    transition (dip to black / flash) is allowed to breathe."""
    if style in ("fadeblack",):
        return max(base, 0.45)
    if style in ("fadewhite", "zoomin", "zoomout", "hblur", "circleopen",
                 "circleclose", "radial", "pixelize"):
        return max(base, 0.28)
    if style in ("dissolve",):
        return max(base, 0.22)
    if style in ("slideleft", "slideright", "slideup", "slidedown", "smoothleft",
                 "smoothright", "wipeleft", "wiperight", "wipeup", "wipedown"):
        return max(base, 0.26)
    return base


def plan_transitions(scenes: list[dict], base: float, mode: str) -> list[dict]:
    """-> one dict per scene: {kind: 'cut'|'xfade', style, duration}

    `kind` describes the transition INTO that scene.  The first scene is always
    a cut (it opens the film).
    """
    out = []
    last_visual = ""
    for i, sc in enumerate(scenes):
        if i == 0:
            out.append({"kind": "cut", "style": "", "duration": 0.0})
            continue
        t = str(sc.get("transition", "") or "").strip().lower()
        t = ALIASES.get(t, t)
        if mode == "hard":
            t = "cut"
        elif mode == "auto" or t not in VALID:
            t = AUTO_ROTATION[(i - 1) % len(AUTO_ROTATION)]
        if t in ("cut", "none", "hard"):
            out.append({"kind": "cut", "style": "", "duration": 0.0})
            continue
        # never the same visible transition twice in a row
        if t == last_visual:
            alt = next((r for r in REVEALS if r != last_visual), "fade")
            t = alt
        d = float(sc.get("transition_duration", 0) or 0) or duration_for(t, base)
        out.append({"kind": "xfade", "style": t, "duration": d})
        last_visual = t
    return out


def build_video_chain(clips: list[Path], transitions: list[dict],
                      w: int, h: int, fps: int) -> tuple[str, list[str], float]:
    """Returns (filtergraph, input_args, total_duration)."""
    n = len(clips)
    if n == 0:
        raise SystemExit("no clips")
    args: list[str] = []
    for c in clips:
        args += ["-i", str(c)]
    dur = [V.probe(c)["duration"] for c in clips]

    # runs: consecutive shots joined by a cross-fade; a hard cut starts a new run
    runs: list[list[int]] = []
    cur = [0]
    for i in range(1, n):
        if transitions[i]["kind"] == "cut":
            runs.append(cur)
            cur = [i]
        else:
            cur.append(i)
    runs.append(cur)

    parts: list[str] = []
    run_labels: list[str] = []
    for ri, run in enumerate(runs):
        if len(run) == 1:
            parts.append(f"[{run[0]}:v]scale={w}:{h},setsar=1,fps={fps},"
                         f"format=yuv420p[r{ri}]")
        else:
            prev = f"[{run[0]}:v]"
            offset = dur[run[0]] - transitions[run[1]]["duration"]
            for k in range(1, len(run)):
                t = transitions[run[k]]
                out = f"[r{ri}_{k}]"
                parts.append(
                    f"{prev}[{run[k]}:v]xfade=transition={t['style']}:"
                    f"duration={t['duration']:.3f}:offset={offset:.3f}{out}"
                )
                prev = out
                offset += dur[run[k]] - t["duration"]
            parts.append(f"{prev}scale={w}:{h},setsar=1,fps={fps},format=yuv420p[r{ri}]")
        run_labels.append(f"[r{ri}]")
    parts.append("".join(run_labels) + f"concat=n={len(runs)}:v=1:a=0[vout]")

    total = sum(dur) - sum(t["duration"] for t in transitions)
    return ";".join(parts), args, total


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--plan", required=True)
    ap.add_argument("--clips", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--music", default=None)
    ap.add_argument("--vo", default=None)
    ap.add_argument("--xfade", type=float, default=0.45,
                    help="default reveal duration in seconds (0 = hard cuts only)")
    ap.add_argument("--transition-mode", default="plan",
                    choices=["plan", "auto", "hard"],
                    help="plan = use the scene's transition field; auto = rotate; hard = cuts only")
    ap.add_argument("--music-db", type=float, default=-12.0)
    ap.add_argument("--lufs", type=float, default=-14.0)
    ap.add_argument("--fps", type=int, default=30)
    ap.add_argument("--crf", type=int, default=18)
    args = ap.parse_args()

    plan = V.jload(args.plan)
    wanted = []
    for s in plan["scenes"]:
        c = Path(args.clips) / f"clip_{s['n']:02d}.mp4"
        if c.exists():
            wanted.append((s, c))
        else:
            print(f"[montage] missing clip for scene {s['n']} — skipped")
    if not wanted:
        print("[montage] no clips found", file=sys.stderr)
        return 2

    scenes = [s for s, _ in wanted]
    clips = [c for _, c in wanted]
    transitions = plan_transitions(scenes, args.xfade, args.transition_mode)

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    res = plan.get("style_spec", {}).get("resolution") or [1920, 1080]
    w, h = int(res[0]), int(res[1])
    fg, in_args, total = build_video_chain(clips, transitions, w, h, args.fps)

    audio_args: list[str] = []
    afilter = ""
    if args.music:
        audio_args += ["-stream_loop", "-1", "-i", str(args.music)]
        music_idx = len(clips)
        afilter += f"[{music_idx}:a]volume={args.music_db}dB[mus];"
    if args.vo:
        audio_args += ["-i", str(args.vo)]
        vo_idx = len(clips) + (1 if args.music else 0)
        afilter += f"[{vo_idx}:a]volume=0dB[voc];"

    if args.music and args.vo:
        afilter += "[mus][voc]amix=inputs=2:duration=longest:dropout_transition=0[mix];"
        afilter += f"[mix]loudnorm=I={args.lufs}:TP=-1.5:LRA=11[aout]"
    elif args.music:
        afilter += f"[mus]loudnorm=I={args.lufs}:TP=-1.5:LRA=11[aout]"
    elif args.vo:
        afilter += f"[voc]loudnorm=I={args.lufs}:TP=-1.5:LRA=11[aout]"

    if afilter:
        fg += ";" + afilter

    cmd = ([V.ffmpeg(), "-hide_banner", "-v", "error", "-y"] + in_args + audio_args
           + ["-filter_complex", fg, "-map", "[vout]"]
           + (["-map", "[aout]"] if afilter else ["-an"])
           + ["-t", f"{total:.3f}",
              "-r", str(args.fps), "-c:v", "libx264", "-preset", "medium",
              "-crf", str(args.crf), "-pix_fmt", "yuv420p",
              "-c:a", "aac", "-b:a", "192k", "-ar", "44100", "-ac", "2",
              "-movflags", "+faststart", str(out)])

    p = V.run(cmd)
    if p.returncode != 0 or not out.exists():
        print("[montage] audio pass failed:\n" + (p.stderr or "")[-1200:], file=sys.stderr)
        fg2, in2, total2 = build_video_chain(clips, transitions, w, h, args.fps)
        cmd2 = ([V.ffmpeg(), "-hide_banner", "-v", "error", "-y"] + in2
                + ["-filter_complex", fg2, "-map", "[vout]", "-an",
                   "-t", f"{total2:.3f}", "-r", str(args.fps), "-c:v", "libx264",
                   "-preset", "medium", "-crf", str(args.crf), "-pix_fmt", "yuv420p",
                   "-movflags", "+faststart", str(out)])
        p = V.run(cmd2)
        if p.returncode != 0 or not out.exists():
            print("[montage] FAILED\n" + (p.stderr or "")[-1500:], file=sys.stderr)
            return 1
        print("[montage] audio pass failed -> silent render kept")

    info = V.probe(out)
    V.jdump({"clips": [str(c) for c in clips],
             "transitions": [{"n": s["n"], **t} for s, t in zip(scenes, transitions)],
             "mode": args.transition_mode, "xfade": args.xfade,
             "music": args.music, "vo": args.vo, "output": str(out),
             "probe": {k: info[k] for k in ("width", "height", "fps", "duration", "nb_frames", "has_audio")}},
            out.with_name(out.stem + "_report.json"))
    used = [t["style"] for t in transitions if t["kind"] == "xfade"]
    print(f"[montage] {out}  {info['width']}x{info['height']}  "
          f"{info['duration']:.3f}s  {info['nb_frames']} frames  audio={info['has_audio']}")
    print(f"[montage] transitions: {used if used else 'hard cuts only'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
