"""Stage 4b - export PORTABLE prompts for every scene.

The local farm is the free default, but a style clone is only useful if it can
also be rebuilt in Flow / Veo / Omni / any other generator. This writes, per
scene, the three blocks the master prompt format asks for:

  IMAGE PROMPT          the fully built final frame, in the locked style
  BACKGROUND PLATE      the same frame with ONLY the background
  ANIMATION PROMPT      the build-in timeline that ends on that exact frame

and a Flow-compatible clip block (STYLE / SEQUENCE / TEXT RULES / AVOID).

Rules baked in here (they come from the motion-graphics references):
  - the STYLE paragraph is IDENTICAL in every scene (no generator memory)
  - the palette hexes and the typography spec are REPEATED, never "same as before"
  - the animation prompt starts on a clean background and ends holding the
    final composed frame
  - the AUDIO RULE is always present verbatim: the music and the voice are
    added in editing, never generated
  - text is 1-5 words (1-3 for Arabic / non-Latin); if the generator cannot
    spell it, generate the CLEAN PLATE and add the words in editing

Usage:
  python export_prompts.py --plan shot_plan_final.json --outdir prompts \
                            [--clean-plate] [--clip-length 10]
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import vlib  # noqa: E402

AUDIO_RULE = ("No background music. No voiceover. No dialogue, speech, singing or lip movement. "
              "Silent clip.")
OPENING_RULE = ("The clip STARTS on the clean background only, with no elements, icons or text visible.")


def style_paragraph(spec: dict) -> str:
    pal = ", ".join(p["hex"] for p in spec.get("palette", []))
    exp = spec.get("exposure", {})
    comp = spec.get("composition", {})
    ty = spec.get("typography", "the reference typography")
    bands = spec.get("text_bands") or []
    band_txt = "; ".join(
        f"text band at y {b['y0']*100:.0f}%-{b['y1']*100:.0f}% in {b.get('colour','#FFFFFF')}"
        for b in bands[:3]
    ) or "centred title card"
    w, h = spec.get("resolution", [1080, 1920])
    return (
        f"STYLE (locked - reproduce exactly, do not improvise): "
        f"{spec.get('style_line','')} "
        f"Frame {w}x{h}. Colour: strictly limited palette using ONLY these hexes: {pal}. "
        f"Exposure: mean luma {exp.get('mean_luma',0):.3f}, p01 {exp.get('p01',0):.3f}, "
        f"p99 {exp.get('p99',0):.3f}, contrast {exp.get('contrast_std',0):.3f}, "
        f"saturation {exp.get('saturation',0):.3f}. "
        f"Finish: film grain sigma {spec.get('grain',0):.5f}, vignette falloff "
        f"{spec.get('vignette_db',0):.2f} dB, bloom on highlights, soft focus with halos. "
        f"Background: {spec.get('backgrounds','')} Lighting: {spec.get('lighting','')} "
        f"Illustration language: {spec.get('illustration_language','')} "
        f"Camera: {spec.get('camera_language','')} "
        f"Composition: subject energy centroid at {comp.get('energy_centroid',[0.5,0.5])}, "
        f"large negative space, subject in a third. "
        f"Typography: {ty} ({band_txt}). "
        f"Recurring motifs: {'; '.join(spec.get('motifs', []))}. "
        f"Forbidden: {'; '.join(spec.get('forbidden', []))}."
    )


def image_prompt(scene: dict, style: str, text: str) -> str:
    body = (
        f"{scene.get('visual_idea','')}. "
        f"Build the FULLY FINISHED final frame of this shot, fully lit and fully composed, "
        f"as a single finished photograph - not a sketch, not a storyboard. "
        f"Every element described here is present in the final frame. "
        f"Leave clean negative space where the words will sit."
    )
    if text:
        body += (f' On-screen text: none - the words are added in editing. '
                 f'The area around the title band must stay completely clean.')
    return body + "\n\n" + style


def plate_prompt(scene: dict, style: str) -> str:
    return (
        f"Same frame, same camera, same lighting and the same colour and texture as the image "
        f"prompt for this scene, but with ONLY the background: "
        f"{scene.get('visual_idea','')} stripped of every element, object, icon, person and "
        f"all text. Background only, empty, ready for elements to be composited on top.\n\n"
        + style
    )


def animation_prompt(scene: dict, style: str, text: str, clip_len: int) -> str:
    dur = int(round(scene.get("seconds", clip_len)))
    hold = max(1.0, min(2.0, dur * 0.2))
    enter0, enter1 = 0.0, 0.5
    settle_end = max(enter1 + 0.4, dur - hold)
    lines = [
        f"Purpose: bring the {scene.get('visual_idea','')} shot to life, then hold it.",
        f"Duration: {dur} seconds, {int(scene.get('beats', 0))} beats, "
        f"motion type: {scene.get('motion',{}).get('type','push')}, "
        f"camera: {scene.get('camera_language','locked-off') if 'camera_language' in scene else 'locked-off with a very slow drift'}.",
        "",
        f"{enter0:.1f}-{enter1:.1f}s: {OPENING_RULE} Only the background, with slow ambient motion "
        f"(a barely perceptible drift, dust or grain movement). Nothing else is visible.",
        f"{enter1:.1f}-{enter1 + 0.4:.1f}s: the main subject enters with a soft scale-pop / slide-up / "
        f"mask reveal and settles into its final position.",
        f"{enter1 + 0.4:.1f}-{settle_end:.1f}s: secondary elements and the light settle in, one after "
        f"another in a staggered order of about 0.2-0.4s, most important first.",
        f"{settle_end:.1f}-{dur:.1f}s: everything settles and HOLDS on the final composed frame, "
        f"matching the image prompt exactly, with gentle micro-motion only.",
        f"Exit: ends on a hold, ready for a hard cut. Do not fade to black.",
        "",
        f"TEXT RULES: {'no text, letters, numbers, captions, subtitles or watermarks anywhere' if not text else 'only these exact words appear on screen: ' + chr(34) + text + chr(34) + ' - each group appears only in its own time window'}.",
        f"AUDIO: {AUDIO_RULE}",
    ]
    return "\n".join(lines) + "\n\n" + style


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--plan", required=True)
    ap.add_argument("--outdir", required=True)
    ap.add_argument("--clip-length", type=int, default=10)
    ap.add_argument("--clean-plate", action="store_true",
                    help="emit the text-free variant (words are added in editing)")
    ap.add_argument("--model", default="Gemini Omni Flash")
    args = ap.parse_args()

    plan = vlib.jload(args.plan)
    spec = plan.get("style_spec") or {}
    scenes = plan.get("scenes") or []
    style = style_paragraph(spec)
    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    blocks = []
    total = len(scenes)
    for i, sc in enumerate(scenes, 1):
        text = (sc.get("text_on_screen") or "").strip()
        if args.clean_plate:
            text = ""
        n = sc.get("n", i)
        slug = sc.get("slug", f"scene-{n:02d}")
        dur = int(round(sc.get("seconds", args.clip_length)))
        md = []
        md.append(f"# CLIP {i} of {total} - {args.model} - {dur}s - "
                  f"{spec.get('resolution',[0,0])[0]}x{spec.get('resolution',[0,0])[1]} - "
                  f"Script: \"{text or '(no text - added in editing)'}\"")
        md.append("")
        md.append("## IMAGE PROMPT")
        md.append("```")
        md.append(image_prompt(sc, style, text))
        md.append("```")
        md.append("")
        md.append("## BACKGROUND PLATE PROMPT")
        md.append("```")
        md.append(plate_prompt(sc, style))
        md.append("```")
        md.append("")
        md.append("## ANIMATION PROMPT")
        md.append("```")
        md.append(animation_prompt(sc, style, text, dur))
        md.append("```")
        md.append("")
        path = outdir / f"{slug}.md"
        path.write_text("\n".join(md), encoding="utf-8")
        blocks.append((i, slug, dur, text, "\n".join(md)))
        print(f"[prompts] {path}")

    idx = [
        "# Portable prompts - style clone",
        "",
        f"Style DNA locked from the reference. {total} clip(s), "
        f"{args.model}, {args.clip_length}s discipline.",
        "",
        "Every clip carries the IDENTICAL STYLE paragraph (generators have no memory "
        "between clips). The music and the voice are added in editing, never generated.",
        "",
        "---",
        "",
    ]
    for i, slug, dur, text, body in blocks:
        idx.append(body)
        idx.append("---")
        idx.append("")
    idx.append("## Flow tips")
    idx.append("")
    idx.append(f"1. Model + duration + aspect: {args.model}, {args.clip_length}s per clip, "
               f"{spec.get('resolution',[0,0])[0]}x{spec.get('resolution',[0,0])[1]}.")
    idx.append("2. Riskiest text: the clips carrying the longest words, numbers or brand names - "
               "generate 3-4 of those and pick the cleanest. If it still misspells, use the "
               "CLEAN PLATE variant and add the words in editing (see text_overlay_sheet.md).")
    idx.append(f"3. Join order: clip 1 -> {total}. Each clip ends on a hold, so hard cuts keep the "
               "rhythm.")
    (outdir / "ALL_PROMPTS.md").write_text("\n".join(idx), encoding="utf-8")
    print(f"[prompts] {outdir / 'ALL_PROMPTS.md'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
