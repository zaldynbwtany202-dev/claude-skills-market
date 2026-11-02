"""Stage 4 — ANIMATION.  stills (or a filmstrip) -> motion clips.

Motion types
  push      Ken Burns push-in (the reference's camera language: ~7-8% / 3 s)
  pull      slow zoom out
  pan       lateral drift, constant zoom
  parallax  blurred background drifting behind a sharper foreground
  live      CHARACTER ANIMATION rung 1: the subject is matted (GrabCut), then
            it breathes (sinusoidal scale) and sways while the background
            drifts the other way
  punch_in  EMPHASIS: a fast zoom to 1.18 over ~0.35 s, then hold  (rung 0+)
  zoom_out  fast zoom back out from 1.18 to 1.00, then hold
  pose2pose CHARACTER ANIMATION rung 2: the scene was generated as a FILMSTRIP
            (N consecutive frames in one canvas).  Every frame is held in turn
            with its own slow push and the poses are cross-dissolved into each
            other -> the subject actually changes pose (a cheap flipbook).

If the subject matte is unreliable the tool falls back to `push` and says so.
If a filmstrip cannot be found the tool falls back to `push` and says so.

usage:
  python animate_shots.py --plan shot_plan_final.json --images <dir>
                           [--frames <dir>]   # sliced filmstrip frames
                           --out <dir> [--size 1920x960] [--fps 30]
"""
from __future__ import annotations

import argparse
import math
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import vlib as V

V.setup_env()
import numpy as np  # noqa: E402
from PIL import Image  # noqa: E402

try:
    import cv2
except Exception:                                        # pragma: no cover
    cv2 = None


# ------------------------------------------------------------------- matting

def subject_mask(src: Path, out_png: Path) -> dict:
    """GrabCut the main subject. -> {ok, coverage, reason}"""
    if cv2 is None:
        return {"ok": False, "coverage": 0.0, "reason": "opencv not installed"}
    img = cv2.imread(str(src))
    if img is None:
        return {"ok": False, "coverage": 0.0, "reason": "cannot read image"}
    h, w = img.shape[:2]
    small = cv2.resize(img, (w // 2, h // 2), interpolation=cv2.INTER_AREA)
    sh, sw = small.shape[:2]
    bgd = np.zeros((1, 65), np.float64)
    fgd = np.zeros((1, 65), np.float64)
    m = np.zeros((sh, sw), np.uint8)
    m[int(sh * 0.12):int(sh * 0.88), int(sw * 0.12):int(sw * 0.88)] = cv2.GC_PR_FGD
    rect = (int(sw * 0.12), int(sh * 0.10), int(sw * 0.76), int(sh * 0.80))
    try:
        cv2.grabCut(small, m, rect, bgd, fgd, 4, cv2.GC_INIT_WITH_RECT)
    except Exception as e:
        return {"ok": False, "coverage": 0.0, "reason": f"grabcut failed: {e}"}
    fg = np.where((m == cv2.GC_FGD) | (m == cv2.GC_PR_FGD), 255, 0).astype(np.uint8)
    fg = cv2.morphologyEx(fg, cv2.MORPH_OPEN, np.ones((5, 5), np.uint8))
    fg = cv2.morphologyEx(fg, cv2.MORPH_CLOSE, np.ones((9, 9), np.uint8))
    fg = cv2.resize(fg, (w, h), interpolation=cv2.INTER_LINEAR)
    fg = cv2.GaussianBlur(fg, (0, 0), 3)
    cov = float((fg > 127).mean())
    if not (0.04 < cov < 0.90):
        return {"ok": False, "coverage": round(cov, 4), "reason": "matte coverage out of range"}
    out_png.parent.mkdir(parents=True, exist_ok=True)
    Image.fromarray(fg).save(out_png)
    return {"ok": True, "coverage": round(cov, 4), "reason": ""}


# ------------------------------------------------------------------ filtergraphs

def graph_push(w, h, fps, dur, amount=0.075, pull=False, pan=0.0):
    total = max(1, int(round(dur * fps)))
    if pull:
        z = f"max(1.0,{1.0 + amount:.4f}-{amount:.4f}*(on/{max(1,total - 1)}))"
    else:
        z = f"min(1.45,{1.0:.4f}+{amount:.4f}*(on/{max(1,total - 1)}))"
    if pan:
        xp = f"(iw-iw/zoom)*({pan:.3f}*on/{max(1,total - 1)})"
        yp = "(ih-ih/zoom)*0.5"
    else:
        xp = "iw/2-(iw/zoom/2)"
        yp = "ih/2-(ih/zoom/2)"
    return (f"scale=iw*4:ih*4:flags=lanczos,"
            f"zoompan=z='{z}':x='{xp}':y='{yp}':d={total}:s={w}x{h}:fps={fps},"
            f"scale={w}:{h}:flags=lanczos,format=yuv420p[vout]")


def graph_punch(w, h, fps, dur, amount=0.18, punch_s=0.35, out=True, tail=0.05):
    """Fast punch-in (or punch-out) then a slow continued push — the classic
    emphasis move.

    The tail push matters: a punch that simply HOLDS leaves the shot frozen for
    the rest of its length, and a frozen shot reads as broken footage.  The
    camera never stops.
    """
    total = max(1, int(round(dur * fps)))
    p = max(2, int(round(punch_s * fps)))
    rest = max(1, total - p)
    if out:
        z = (f"if(lte(on,{p}),{1.0 + amount:.4f}-{amount:.4f}*on/{p},"
             f"{1.0:.4f}+{tail:.4f}*(on-{p})/{rest})")
    else:
        z = (f"if(lte(on,{p}),{1.0:.4f}+{amount:.4f}*on/{p},"
             f"{1.0 + amount:.4f}+{tail:.4f}*(on-{p})/{rest})")
    xp = "iw/2-(iw/zoom/2)"
    yp = "ih/2-(ih/zoom/2)"
    return (f"scale=iw*4:ih*4:flags=lanczos,"
            f"zoompan=z='{z}':x='{xp}':y='{yp}':d={total}:s={w}x{h}:fps={fps},"
            f"scale={w}:{h}:flags=lanczos,format=yuv420p[vout]")


def graph_live(w, h, fps, dur, breathe=0.014, sway=14.0):
    """Background drifts one way, matted subject breathes and sways the other."""
    return (
        f"[0:v]split=2[bg][fg];"
        f"[1:v]scale={w}:{h}:flags=lanczos,format=gray[msk];"
        f"[fg]scale={w}:{h}:flags=lanczos,format=rgba[fgc];"
        f"[fgc][msk]alphamerge[fgA];"
        f"[fgA]scale=w='iw*(1+{breathe}*sin(2*PI*t/3.4))':"
        f"h='ih*(1+{breathe}*sin(2*PI*t/3.4))':eval=frame[fgB];"
        f"[bg]scale={w}:{h}:flags=lanczos,"
        f"crop={w}:{h}:'min(max((iw-{w})/2-18*sin(2*PI*t/7),0),iw-{w})':"
        f"'min(max((ih-{h})/2+8*sin(2*PI*t/9),0),ih-{h})',"
        f"boxblur=6:1,eq=brightness=-0.06:saturation=0.9[bgp];"
        f"[bgp][fgB]overlay=x='(W-w)/2+{sway}*sin(2*PI*t/5)':"
        f"y='(H-h)/2+6*sin(2*PI*t/3.4)':format=auto,format=yuv420p[vout]"
    )


def graph_parallax(w, h, fps, dur):
    return (
        f"[0:v]split=2[bg][fg];"
        f"[bg]scale={w}:{h}:flags=lanczos,"
        f"crop={w}:{h}:'min(max((iw-{w})/2+22*sin(2*PI*t/8),0),iw-{w})':"
        f"'min(max((ih-{h})/2-10*sin(2*PI*t/11),0),ih-{h})',"
        f"boxblur=14:2,eq=brightness=-0.12:saturation=0.85[bgp];"
        f"[fg]scale={w}:{h}:flags=lanczos[fgp];"
        f"[bgp][fgp]overlay=x='(W-w)/2-10*sin(2*PI*t/8)':"
        f"y='(H-h)/2+5*sin(2*PI*t/11)':format=auto,format=yuv420p[vout]"
    )


def graph_pose2pose(w, h, fps, dur, n_frames, blend=4, push=0.05, hold_frames=None):
    """FILMSTRIP -> real motion.

    Every filmstrip cell is a different pose of the same shot.  Each pose is
    held for its share of the shot while the camera keeps pushing in, and the
    poses are joined with a SHORT blend (default 4 frames = 0.13 s).

    Why the blend is short: a long cross-dissolve between two different poses
    shows BOTH poses at once - a ghost.  4 frames softens the cut and reads as
    a cut, not as a dissolve.  (This is the house rule: a 4-frame crossfade
    built from real frames.)

    `hold_frames` (optional) sets the exact length of every pose in frames -
    use it to land the pose changes on the beat grid.

    Returns (filtergraph, holds, blend_frames, total_seconds).
    """
    n = max(1, int(n_frames))
    total = max(2, int(round(dur * fps)))
    bl = max(0, min(int(blend), max(0, total // (2 * n))))
    if hold_frames:
        holds = [int(x) for x in hold_frames][:n]
        while len(holds) < n:
            holds.append(holds[-1] if holds else total // n)
        # the clip must come out exactly as long as the planned shot
        diff = (total + (n - 1) * bl) - sum(holds)
        holds[-1] = max(1, holds[-1] + diff)
    else:
        hold_sum = total + (n - 1) * bl
        base = hold_sum // n
        holds = [base] * n
        for i in range(hold_sum - base * n):
            holds[i] += 1
    out_total = sum(holds) - (n - 1) * bl

    parts = []
    for i, hf in enumerate(holds):
        f_i = sum(holds[:i]) - i * bl          # output frame where pose i starts
        z = f"min(1.45,{1.0:.4f}+{push:.4f}*(({f_i}+on)/{max(1, out_total)}))"
        parts.append(
            f"[{i}:v]scale=iw*4:ih*4:flags=lanczos,"
            f"zoompan=z='{z}':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':"
            f"d={hf}:s={w}x{h}:fps={fps},"
            f"trim=duration={hf / fps:.4f},setpts=PTS-STARTPTS[p{i}]"
        )
    if bl <= 0:
        parts.append("".join(f"[p{i}]" for i in range(n)) + f"concat=n={n}:v=1:a=0[vout]")
        return ";".join(parts), holds, 0, out_total / fps
    prev = "[p0]"
    for i in range(1, n):
        f_i = sum(holds[:i]) - i * bl
        out = f"[x{i}]"
        parts.append(
            f"{prev}[p{i}]xfade=transition=fade:duration={bl / fps:.4f}:"
            f"offset={f_i / fps:.4f}{out}"
        )
        prev = out
    parts.append(f"{prev}format=yuv420p[vout]")
    return ";".join(parts), holds, bl, out_total / fps


def beat_holds(t_start, t_end, n, fps, period=None, offset=0.0):
    """Pose lengths in frames that land the pose changes on the beat grid.

    With no period -> an even split.  With a period -> the interior beats of
    the shot are sampled evenly, so every pose change is ON a beat.

    The returned holds add up to `shot frames + (n-1)*blend`, so after the
    blend the clip is EXACTLY the planned length - the cuts never drift off
    the beat.
    """
    total = max(2, int(round((t_end - t_start) * fps)))
    if not period or period <= 0:
        return None
    b0 = int(np.ceil((t_start - offset) / period))
    b1 = int(np.floor((t_end - offset) / period))
    beats = [offset + k * period for k in range(b0, b1 + 1)]
    if len(beats) < 2:
        return None
    idx = [round(i * (len(beats) - 1) / (n - 1)) for i in range(1, n)] if n > 1 else []
    idx = sorted(set(int(x) for x in idx))
    marks = [beats[0]] + [beats[i] for i in idx] + [beats[-1]]
    holds = []
    for i in range(len(marks) - 1):
        f0 = int(round((marks[i] - t_start) * fps))
        f1 = int(round((marks[i + 1] - t_start) * fps))
        holds.append(max(1, f1 - f0))
    while len(holds) < n:
        holds.append(holds[-1])
    holds = holds[:n]
    return holds


# -------------------------------------------------------------------- driver

def render_clip(img: Path, out: Path, motion: dict, w: int, h: int, fps: int, dur: float,
                frames_dir: Path | None = None, scene: dict | None = None) -> dict:
    motion = motion or {}
    mtype = motion.get("type", "push")
    amount = float(motion.get("amount", 0.075))
    total = max(1, int(round(dur * fps)))
    note = ""
    mask_used = ""

    # ---- rung 2: pose-to-pose from a sliced filmstrip
    if mtype in ("pose2pose", "filmstrip"):
        paths = find_filmstrip_frames(frames_dir, scene or {}) if frames_dir else []
        if paths:
            holds = None
            period = float(motion.get("beat_period", 0) or 0)
            if period > 0:
                holds = beat_holds(float((scene or {}).get("t_start", 0.0)),
                                   float((scene or {}).get("t_end", dur)),
                                   len(paths), fps, period=period,
                                   offset=float(motion.get("beat_offset", 0.0)))
            fc, holds, bl, out_dur = graph_pose2pose(
                w, h, fps, dur, len(paths),
                blend=int(motion.get("blend", 4)),
                push=float(motion.get("push", 0.05)),
                hold_frames=holds)
            args = []
            for p in paths:
                args += ["-loop", "1", "-i", str(p)]
            out.parent.mkdir(parents=True, exist_ok=True)
            cmd = ([V.ffmpeg(), "-hide_banner", "-v", "error", "-y"] + args
                   + ["-filter_complex", fc, "-map", "[vout]", "-t", f"{out_dur:.3f}",
                      "-r", str(fps), "-c:v", "libx264", "-preset", "medium", "-crf", "18",
                      "-pix_fmt", "yuv420p", str(out)])
            p = V.run(cmd)
            if p.returncode == 0 and out.exists():
                info = V.probe(out)
                return {"ok": True, "motion": "pose2pose", "note":
                        f"{len(paths)} poses, holds {holds}, blend {bl} f"
                        + (" (beat-aligned)" if period > 0 else ""),
                        "mask": "", "frames": info["nb_frames"],
                        "duration": info["duration"], "path": str(out),
                        "filmstrip": [str(x) for x in paths]}
            note = "pose2pose graph failed -> push fallback"
            if out.exists():
                out.unlink()
        else:
            note = "no filmstrip frames found -> push fallback"
        mtype = "push"

    # ---- rung 1: mattes + breathing
    if mtype == "live":
        mask = out.parent / "_masks" / f"{out.stem}_mask.png"
        res = subject_mask(img, mask)
        if res["ok"]:
            mask_used = str(mask)
            fc = graph_live(w, h, fps, dur)
            args = ["-loop", "1", "-i", str(img), "-loop", "1", "-i", str(mask)]
        else:
            note = f"matte unreliable ({res['reason']}) -> fell back to push"
            mtype = "push"
            fc = None
    else:
        fc = None
        args = ["-loop", "1", "-i", str(img)]

    if fc is None:
        if mtype == "parallax":
            fc = graph_parallax(w, h, fps, dur)
        elif mtype == "pull":
            fc = graph_push(w, h, fps, dur, amount, pull=True)
        elif mtype == "pan":
            fc = graph_push(w, h, fps, dur, amount, pan=0.9)
        elif mtype == "pan_left":
            fc = graph_push(w, h, fps, dur, amount, pan=-0.9)
        elif mtype == "still":
            fc = graph_push(w, h, fps, dur, 0.02)
        elif mtype in ("punch_in", "punch"):
            fc = graph_punch(w, h, fps, dur, amount=float(motion.get("amount", 0.18)),
                             punch_s=float(motion.get("punch_s", 0.35)), out=False,
                             tail=float(motion.get("tail", 0.05)))
        elif mtype in ("zoom_out", "punch_out"):
            fc = graph_punch(w, h, fps, dur, amount=float(motion.get("amount", 0.18)),
                             punch_s=float(motion.get("punch_s", 0.35)), out=True,
                             tail=float(motion.get("tail", 0.05)))
        else:
            fc = graph_push(w, h, fps, dur, amount)

    out.parent.mkdir(parents=True, exist_ok=True)
    cmd = ([V.ffmpeg(), "-hide_banner", "-v", "error", "-y"] + args
           + ["-filter_complex", fc, "-map", "[vout]", "-t", f"{dur:.3f}",
              "-r", str(fps), "-c:v", "libx264", "-preset", "medium", "-crf", "18",
              "-pix_fmt", "yuv420p", str(out)])
    p = V.run(cmd)
    if p.returncode != 0 or not out.exists():
        # one retry with the safest graph before giving up
        fc = graph_push(w, h, fps, dur, amount)
        cmd = ([V.ffmpeg(), "-hide_banner", "-v", "error", "-y", "-loop", "1", "-i", str(img),
                "-vf", fc, "-t", f"{dur:.3f}", "-r", str(fps), "-c:v", "libx264",
                "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p", str(out)])
        p = V.run(cmd)
        if p.returncode != 0 or not out.exists():
            return {"ok": False, "error": (p.stderr or "")[-600:], "motion": mtype}
        note = (note + " | " if note else "") + "primary graph failed -> push fallback"
        mtype = "push"

    info = V.probe(out)
    return {"ok": True, "motion": mtype, "note": note, "mask": mask_used,
            "frames": info["nb_frames"], "duration": info["duration"], "path": str(out)}


def find_filmstrip_frames(frames_dir: Path, scene: dict) -> list[Path]:
    """Look for frame-01.png .. frame-NN.png under the usual folder names."""
    n = int(scene.get("n", 0))
    slug = str(scene.get("slug", ""))
    cands = [frames_dir / f"scene-{n:02d}", frames_dir / f"scene-{n}",
              frames_dir / slug, frames_dir / f"story-{n:02d}-{slug}"]
    for d in cands:
        if not d.is_dir():
            continue
        fs = sorted(d.glob("frame-*.png")) or sorted(d.glob("f_*.png"))
        if fs:
            return fs
    return []


def find_image(images: Path, scene: dict) -> Path | None:
    cands = [images / f"story-{scene['n']:02d}-{scene['slug']}.png",
             images / f"{scene['slug']}.png",
             images / f"scene-{scene['n']:02d}.png",
             images / f"{scene['n']:02d}.png"]
    for c in cands:
        if c.exists():
            return c
    hits = sorted(images.glob(f"*{scene['n']:02d}*"))
    return hits[0] if hits else None


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--plan", required=True)
    ap.add_argument("--images", required=True)
    ap.add_argument("--frames", default="", help="sliced filmstrip frames root")
    ap.add_argument("--out", required=True)
    ap.add_argument("--size", default=None, help="WxH; default = the reference resolution")
    ap.add_argument("--fps", type=int, default=30)
    args = ap.parse_args()

    plan = V.jload(args.plan)
    images = Path(args.images)
    outdir = Path(args.out)
    frames_dir = Path(args.frames) if args.frames else None
    res = plan.get("style_spec", {}).get("resolution") or [1920, 1080]
    if args.size:
        w, h = (int(v) for v in args.size.lower().split("x"))
    else:
        w, h = int(res[0]), int(res[1])

    report = []
    for scene in plan["scenes"]:
        img = find_image(images, scene)
        if img is None:
            report.append({"n": scene["n"], "ok": False, "error": "no image found"})
            print(f"[anim] scene {scene['n']}: NO IMAGE")
            continue
        out = outdir / f"clip_{scene['n']:02d}.mp4"
        r = render_clip(img, out, scene.get("motion", {}), w, h, args.fps, scene["seconds"],
                        frames_dir=frames_dir, scene=scene)
        r["n"] = scene["n"]
        r["image"] = str(img)
        report.append(r)
        print(f"[anim] scene {scene['n']}: {r.get('motion')} "
              f"{'OK' if r.get('ok') else 'FAIL'} {r.get('note','')}")
    V.jdump({"plan": args.plan, "size": [w, h], "fps": args.fps, "clips": report},
            outdir / "animation_report.json")
    ok = sum(1 for r in report if r.get("ok"))
    print(f"[anim] {ok}/{len(report)} clips rendered -> {outdir}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
