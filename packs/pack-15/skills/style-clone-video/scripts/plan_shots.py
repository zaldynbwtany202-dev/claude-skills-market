"""Stage 3 — STYLE LOCK + SHOT PLAN.

  scaffold : measured DNA (+ optional agent-written notes) -> shot_plan.json
             with scene slots, a locked STYLE SPEC block, and a SCENE MAP table.
  finalize : shot_plan.json (prompt cores filled) -> prompts with the locked
             style injected into EVERY scene + a farm-ready scenes.json.

The rule from the master prompt this encodes: never write "same as before".
Every scene prompt carries the palette HEX, the typography spec and the
illustration style, verbatim, every time.

usage:
  python plan_shots.py scaffold --style style_dna.json [--notes style_notes.json]
                                --idea "..." [--duration 30] [--tempo 100] [--beat-offset 0.464]
                                --out shot_plan.json
  python plan_shots.py finalize --plan shot_plan.json --out shot_plan_final.json
                                [--scenes scenes.json] [--master master_panel.json]
                                [--ref-keyframes KEYDIR] [--master-panel ABS.png]
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

SLOT_LENGTHS = [10, 8, 6, 4]          # Google Flow / Veo clip lengths
PROMPT_CORE_KEY = "prompt_core"


# ----------------------------------------------------------------- style spec

def build_style_spec(dna: dict, notes: dict) -> dict:
    m = dna.get("measured", {})
    ex = m.get("exposure", {})
    pal = m.get("palette", [])
    bands = m.get("text_bands", [])
    spec = {
        "style_line": notes.get("style_line", ""),
        "resolution": m.get("resolution"),
        "aspect": m.get("aspect"),
        "palette": [{"hex": h, "share": s} for h, s in pal],
        "exposure": ex,
        "grain": m.get("grain"),
        "vignette_db": m.get("vignette_db"),
        "sharpness": m.get("sharpness"),
        "bloom_fraction": ex.get("bloom_fraction"),
        "saturation": ex.get("saturation"),
        "composition": m.get("composition", {}),
        "text_bands": bands,
        "illustration_style": notes.get("illustration_style", ""),
        "camera_language": notes.get("camera_language", ""),
        "motion_language": notes.get("motion_language", ""),
        "backgrounds": notes.get("backgrounds", ""),
        "lighting": notes.get("lighting", ""),
        "finish": notes.get("finish", ""),
        "typography": notes.get("typography", ""),
        "motifs": notes.get("motifs", []),
        "forbidden": notes.get("forbidden", [
            "no watermark, no logo, no brand name, no subtitle text inside the image",
            "do not copy copyrighted characters, logos or exact copy from the reference",
        ]),
        "notes": notes.get("notes", ""),
    }
    return spec


def style_block(spec: dict) -> str:
    """The locked, repeatable style paragraph injected into every scene prompt."""
    pal = ", ".join(p["hex"] for p in spec.get("palette", []))
    band = spec.get("text_bands") or []
    ty = []
    for b in band:
        ty.append(f"text band at y {b['y0']:.0%}-{b['y1']:.0%} in {b['colour']}")
    ex = spec.get("exposure", {})
    res = spec.get("resolution") or [0, 0]
    sat = ex.get("saturation")
    mono = (sat is None) or float(sat) < 0.05
    vig = spec.get("vignette_db")
    grain = spec.get("grain")
    colour_line = (
        f"- Colour: strictly monochrome / near-zero saturation "
        f"(measured {sat}). Use ONLY these hexes: {pal}."
        if mono else
        f"- Colour: MUTED, limited-palette colour (measured saturation {sat}) — "
        f"it is NOT monochrome, do not desaturate it to grey. Use ONLY these hexes: {pal}, "
        f"plus small amounts of olive/moss green, warm ochre and one or two bright accents "
        f"(signal red, flame orange, sky blue) exactly as the reference uses them."
    )
    finish_bits = []
    if grain is not None:
        finish_bits.append(
            f"surface texture sigma {grain}" + (" — keep it subtle, no heavy film grain" if float(grain) < 0.012 else " — visible light grain"))
    if vig is not None:
        finish_bits.append(
            f"vignette falloff {vig} dB" + (" — essentially NO vignette, do not darken the corners" if float(vig) < 2.0 else " — keep the falloff"))
    finish_bits.append("clean flat vector fills, no lens flare, no depth-of-field blur")
    lines = [
        f"STYLE LOCK — reproduce this exactly, do not improvise:",
        f"- Frame: {res[0]}x{res[1]} ({spec.get('aspect')} aspect).",
        colour_line,
        f"- Exposure: mean luma {ex.get('mean_luma')}, p01 {ex.get('p01')}, p99 {ex.get('p99')}, "
        f"contrast {ex.get('contrast_std')}, saturation {sat}.",
        f"- Finish: {'; '.join(finish_bits)}.",
        f"- Background: {spec.get('backgrounds') or 'as in the reference'}.",
        f"- Lighting: {spec.get('lighting') or 'as in the reference'}.",
        f"- Illustration language: {spec.get('illustration_style') or 'as in the reference'}.",
        f"- Camera: {spec.get('camera_language') or 'as in the reference'}.",
        f"- Composition: subject energy centroid at {spec.get('composition', {}).get('energy_centroid')}, "
        f"large negative space, subject in a third.",
    ]
    if spec.get("typography"):
        lines.append(f"- Typography (added in editing, not in the image): {spec['typography']}")
    if ty:
        lines.append(f"- Title-card geometry: {', '.join(ty)}.")
    if spec.get("motifs"):
        lines.append("- Recurring motifs: " + "; ".join(spec["motifs"]))
    for f in spec.get("forbidden", []):
        lines.append(f"- {f}")
    return "\n".join(lines)


# ------------------------------------------------------------------ planning

def fit_slots(duration: int) -> list[int]:
    """Express the target duration as 4/6/8/10 s scene slots (fewest cuts first)."""
    best = None

    def rec(rem, acc):
        nonlocal best
        if rem == 0:
            key = (len(acc), acc)          # fewer shots wins
            if best is None or key < best[0]:
                best = (key, acc[:])
            return
        for L in SLOT_LENGTHS:
            if L <= rem:
                acc.append(L)
                rec(rem - L, acc)
                acc.pop()

    rec(duration, [])
    if best:
        return best[1]
    rem = duration
    acc = []
    for L in SLOT_LENGTHS:
        while rem - L >= 4:
            acc.append(L)
            rem -= L
    if rem:
        acc.append(min(SLOT_LENGTHS, key=lambda L: abs(L - rem)))
    return acc


def snap_to_beat(t: float, tempo: float, offset: float) -> float:
    if not tempo or tempo <= 0:
        return t
    period = 60.0 / tempo
    k = round((t - offset) / period)
    return round(offset + k * period, 4)


def build_scene_map(slots: list[int], tempo: float, offset: float, duration: float | None = None):
    """Scene boundaries. With a tempo they land on the beat grid; without one
    they are plain slot lengths. Never negative, never off-grid."""
    scenes = []
    if tempo and tempo > 0:
        period = 60.0 / tempo
        k0 = math.ceil((0.0 - offset) / period - 1e-9)          # first beat >= 0
        t_first = offset + k0 * period
        if t_first < 0:
            k0 += 1
            t_first = offset + k0 * period
        beats_per = [max(1, int(round(L / period))) for L in slots]
        total_b = sum(beats_per)
        if duration:
            avail = int(math.floor((duration - t_first) / period)) + 1
            while total_b > avail and len(beats_per) > 1:
                beats_per[-1] -= 1
                total_b -= 1
                if beats_per[-1] < 1:
                    beats_per.pop()
                    total_b = sum(beats_per)
            if total_b < avail:
                beats_per[-1] += (avail - total_b)
                total_b = sum(beats_per)
        t = t_first
        for i, (L, nb) in enumerate(zip(slots, beats_per), start=1):
            t1 = round(t + nb * period, 4)
            scenes.append({
                "n": i, "slug": f"scene-{i:02d}",
                "seconds": round(t1 - t, 4), "t_start": round(t, 4), "t_end": t1,
                "clip_length_s": L, "beats": nb,
                "text_on_screen": "", "visual_idea": "", "why": "",
                "motion": {"type": "push", "amount": 0.08, "direction": "in"},
                "transition": "cut", PROMPT_CORE_KEY: "",
            })
            t = t1
        return scenes

    t = 0.0
    for i, L in enumerate(slots, start=1):
        t1 = round(t + L, 4)
        scenes.append({
            "n": i, "slug": f"scene-{i:02d}",
            "seconds": round(t1 - t, 4), "t_start": round(t, 4), "t_end": t1,
            "clip_length_s": L, "beats": None,
            "text_on_screen": "", "visual_idea": "", "why": "",
            "motion": {"type": "push", "amount": 0.08, "direction": "in"},
            "transition": "cut", PROMPT_CORE_KEY: "",
        })
        t = t1
    return scenes


# ------------------------------------------------------------------- drivers

def filmstrip_instruction(n: int, layout: str) -> str:
    """The prompt block that turns ONE image into N consecutive frames.

    The generator can only hand back one canvas, so we ask it for a camera
    strip / flipbook: the same shot in N successive poses, arranged in a grid.
    slice_filmstrip.py then cuts that canvas into N real frames and
    animate_shots.py turns them into pose-to-pose motion.
    """
    c, r = (int(x) for x in layout.lower().replace("x", " ").split())
    order = ("row by row, left to right" if r > 1 and c > 1
             else ("left to right" if c > 1 else "top to bottom"))
    return (
        f"OUTPUT FORMAT — ONE single image that is a CAMERA STRIP of {n} consecutive "
        f"animation frames of the SAME shot, arranged in a grid of exactly {c} columns "
        f"and {r} rows ({order}).\n"
        f"Rules for the strip: every cell shows the same camera angle, the same "
        f"framing, the same background and the same lighting; only the subject "
        f"changes, moving through {n} successive poses of one continuous action "
        f"(step 1 -> step 2 -> ... -> step {n}, like a flipbook). Cells are equal "
        f"size, separated by thin plain black gutters. Absolutely NO borders, NO "
        f"frames, NO labels, NO numbers, NO arrows, NO captions, NO text anywhere "
        f"in the image. Each cell must be a complete, usable frame of the shot on "
        f"its own. Ignore the usual 16:9 canvas and fill it with the {c}x{r} grid."
    )


def pick_ref_frames(keydir: str, count: int = 4) -> list[str]:
    """Choose `count` reference keyframes spread across the reference, by name order.

    These are the frames the image model will actually SEE, so they are the real
    style-clone bridge. Absolute paths - the farm uploads them by path."""
    d = Path(keydir)
    if not d.is_dir():
        return []
    files = sorted([p for p in d.iterdir()
                    if p.suffix.lower() in (".jpg", ".jpeg", ".png")], key=lambda p: p.name)
    if not files:
        return []
    if len(files) <= count:
        return [str(p.resolve()) for p in files]
    idx = [round(i * (len(files) - 1) / (count - 1)) for i in range(count)]
    return [str(files[i].resolve()) for i in sorted(set(idx))]


def cmd_scaffold(args) -> int:
    dna = V.jload(args.style)
    notes = V.jload(args.notes) if args.notes and Path(args.notes).exists() else {}
    spec = build_style_spec(dna, notes)
    slots = fit_slots(int(args.duration))
    scenes = build_scene_map(slots, args.tempo, args.beat_offset, float(args.duration))

    plan = {
        "schema": "style-clone-video/shot-plan@1",
        "idea": args.idea,
        "duration_target": args.duration,
        "tempo_bpm": args.tempo,
        "beat_offset": args.beat_offset,
        "style_spec": spec,
        "style_block": style_block(spec),
        "scenes": scenes,
    }
    V.jdump(plan, args.out)

    block_path = Path(args.out).with_name("STYLE_SPEC.txt")
    block_path.write_text(plan["style_block"] + "\n", encoding="utf-8")

    rows = ["| # | time | len | on-screen text | visual idea | why |",
            "|---|------|-----|----------------|-------------|-----|"]
    for s in scenes:
        rows.append(f"| {s['n']} | {s['t_start']:.2f}–{s['t_end']:.2f} | {s['clip_length_s']}s | "
                    f" | {s['visual_idea']} | {s['why']} |")
    Path(args.out).with_name("SCENE_MAP.md").write_text(
        f"# Scene map — {args.idea}\n\n" + "\n".join(rows) + "\n", encoding="utf-8")

    print(f"[plan] {len(scenes)} scenes, {sum(s['seconds'] for s in scenes):.2f}s -> {args.out}")
    print(f"[plan] style block -> {block_path}")
    print("[plan] NEXT: fill visual_idea / text_on_screen / prompt_core for every scene, then run 'finalize'")
    return 0


def cmd_finalize(args) -> int:
    plan = V.jload(args.plan)
    spec = plan["style_spec"]
    block = plan["style_block"]
    fs_n = int(getattr(args, "filmstrip", 0) or 0)
    fs_layout = getattr(args, "filmstrip_layout", "2x2") or "2x2"
    fs_scenes = set()
    raw = (getattr(args, "filmstrip_scenes", "") or "").strip()
    if raw:
        fs_scenes = {int(x) for x in raw.replace(" ", "").split(",") if x.strip()}
    out_scenes = []
    for s in plan["scenes"]:
        core = (s.get(PROMPT_CORE_KEY) or "").strip()
        if not core:
            print(f"[plan] WARNING scene {s['n']} has an empty {PROMPT_CORE_KEY} — it will be skipped")
            continue
        s = dict(s)
        use_strip = fs_n >= 2 and (not fs_scenes or s["n"] in fs_scenes)
        if use_strip:
            prompt = f"{core}\n\n{filmstrip_instruction(fs_n, fs_layout)}\n\n{block}"
            s["filmstrip"] = {"n": fs_n, "layout": fs_layout}
            s["motion"] = {"type": "pose2pose", "crossfade": 0.35, "push": 0.05}
        else:
            prompt = f"{core}\n\n{block}"
            s["filmstrip"] = None
        s["prompt"] = prompt
        out_scenes.append(s)

    plan["scenes"] = out_scenes
    plan["style_spec"] = spec
    V.jdump(plan, args.out)
    print(f"[plan] finalized {len(out_scenes)} scenes -> {args.out}")

    if args.scenes:
        mp = Path(args.master_panel).resolve() if args.master_panel else None
        farm = []
        for s in out_scenes:
            refs = s.get("refs", []) or []
            if mp:
                refs = [str(mp)] + [r for r in refs if r != str(mp)]
            farm.append({"n": s["n"], "slug": s["slug"], "prompt": s["prompt"], "refs": refs})
        V.jdump(farm, args.scenes)
        print(f"[plan] farm scenes -> {args.scenes}")
        if mp:
            print(f"[plan]   every scene references the master panel: {mp}")

    if args.master:
        spec_line = (spec.get("style_line") or "reproduce the reference style")
        pal = ", ".join(p["hex"] for p in spec.get("palette", []))
        master_prompt = (
            f"MASTER REFERENCE PANEL — a single model sheet that locks the style for every later scene.\n"
            f"Style: {spec_line}\n"
            f"Palette (use ONLY these): {pal}\n"
            f"Background: {spec.get('backgrounds') or 'as in the reference'}\n"
            f"Lighting: {spec.get('lighting') or 'as in the reference'}\n"
            f"Illustration: {spec.get('illustration_style') or 'as in the reference'}\n"
            f"Camera: {spec.get('camera_language') or 'as in the reference'}\n"
            f"Finish: grain {spec.get('grain')}, vignette {spec.get('vignette_db')} dB, soft focus with halos.\n"
            f"Show the recurring motifs side by side: "
            f"{'; '.join(spec.get('motifs') or ['the main subject'])}.\n"
            f"Layout: a clean horizontal model sheet, 16:9, wide negative space between the motifs, "
            f"a neutral background that matches the reference, and NO text, NO watermark, NO logo.\n"
            f"This panel is the style reference that every other scene will be generated against."
        )
        refs = pick_ref_frames(args.ref_keyframes, args.ref_count) if args.ref_keyframes else []
        V.jdump([{"n": 1, "slug": "master-panel", "prompt": master_prompt, "refs": refs}], args.master)
        print(f"[plan] master panel -> {args.master}")
        if refs:
            print(f"[plan]   master panel shows the model {len(refs)} reference frames:")
            for r in refs:
                print(f"[plan]     ref {r}")
        else:
            print("[plan]   WARNING: master panel has NO reference frames attached — "
                  "the style must be re-described in words or the clone will drift")

    Path(args.out).with_name("SCENE_MAP.md").write_text(
        "# Scene map\n\n| # | time | len | on-screen text | visual idea | why | motion | transition |\n"
        "|---|------|-----|----------------|-------------|-----|--------|------------|\n"
        + "\n".join(
            f"| {s['n']} | {s['t_start']:.2f}–{s['t_end']:.2f} | {s['clip_length_s']}s | "
            f"{s.get('text_on_screen','')} | {s.get('visual_idea','')} | {s.get('why','')} | "
            f"{(s.get('motion') or {}).get('type','')} | {s.get('transition','')} |"
            for s in out_scenes) + "\n", encoding="utf-8")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("scaffold")
    s.add_argument("--style", required=True)
    s.add_argument("--notes", default=None)
    s.add_argument("--idea", required=True)
    s.add_argument("--duration", type=int, default=30)
    s.add_argument("--tempo", type=float, default=0.0)
    s.add_argument("--beat-offset", type=float, default=0.0)
    s.add_argument("--out", default="shot_plan.json")
    s.set_defaults(fn=cmd_scaffold)

    f = sub.add_parser("finalize")
    f.add_argument("--plan", required=True)
    f.add_argument("--out", default="shot_plan_final.json")
    f.add_argument("--scenes", default=None)
    f.add_argument("--master", default=None)
    f.add_argument("--ref-keyframes", default=None,
                   help="folder of reference keyframes the model will be shown")
    f.add_argument("--ref-count", type=int, default=4)
    f.add_argument("--master-panel", default=None,
                   help="ABS path where the farm will save the master panel; every scene references it")
    f.add_argument("--filmstrip", type=int, default=0,
                   help="N consecutive frames per scene, generated in ONE canvas (0 = off)")
    f.add_argument("--filmstrip-layout", default="2x2",
                   help="grid of the strip, e.g. 2x2 (4 frames) or 2x3 (6 frames)")
    f.add_argument("--filmstrip-scenes", default="",
                   help="comma list of scene numbers that get a filmstrip; empty = all")
    f.set_defaults(fn=cmd_finalize)

    args = ap.parse_args()
    return args.fn(args)


if __name__ == "__main__":
    raise SystemExit(main())
