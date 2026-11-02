"""Stage 6b - add the on-screen text in EDITING, never in the generator.

Why this exists: image models render text badly (or not at all). The style
clone therefore locks the TEXT GEOMETRY measured from the reference
(style_spec.text_bands) and burns the words in here, on top of the finished
clips, with a real font.

Two outputs:
  1. the re-rendered video with the text burned in
  2. a TEXT OVERLAY SHEET (timestamp -> words -> tier -> animation) so the
     same text can be typed by hand in CapCut instead

Usage:
  python add_text.py --plan shot_plan_final.json --video final.mp4 \
                     --out final_text.mp4 [--sheet text_overlay_sheet.md] \
                     [--fade 0.4] [--dry-run]
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import vlib  # noqa: E402

SERIF_BOLD = [
    r"C:\Windows\Fonts\timesbd.ttf",
    r"C:\Windows\Fonts\georgiab.ttf",
    r"C:\Windows\Fonts\cour.ttf",
    r"C:\Windows\Fonts\seguisb.ttf",
]
SANS_BOLD = [
    r"C:\Windows\Fonts\impact.ttf",
    r"C:\Windows\Fonts\segoeuib.ttf",
    r"C:\Windows\Fonts\arialbd.ttf",
    r"C:\Windows\Fonts\calibrib.ttf",
]
CAP_RATIO = 0.70  # cap height as a fraction of the em size


def pick_font(paths):
    from PIL import ImageFont

    for p in paths:
        if Path(p).exists():
            try:
                return ImageFont.truetype(p, 40), p
            except Exception:
                pass
    return vlib.load_font(40), "default"


def bands_of(style_spec):
    """Distinct measured text bands.

    The detector reports the same band several times (once per sampled frame
    that shows it), with slightly different edges and different frame counts.
    Raw use would stack two copies of the same line on top of each other, so:
      1. merge bands that overlap vertically (keep the one seen most often),
      2. drop watermark-sized bands (height_px < 20),
      3. sort top -> bottom so line 1 lands above line 2.
    """
    raw = (style_spec or {}).get("text_bands") or []
    if not raw:
        return []
    items = []
    for b in raw:
        y0 = float(b.get("y0", 0.0))
        y1 = float(b.get("y1", 0.0))
        if y1 <= y0:
            continue
        items.append({
            "y0": y0, "y1": y1,
            "centre_pct": (y0 + y1) / 2.0,
            "height_px": int(b.get("height_px", 0) or 0),
            "colour": b.get("colour", "#FFFFFF"),
            "frames": int(b.get("frames", 0) or 0),
        })
    # 1. merge overlapping bands, keep the one with the most frame hits
    items.sort(key=lambda b: -b["frames"])
    merged = []
    for b in items:
        hit = None
        for m in merged:
            ov = min(m["y1"], b["y1"]) - max(m["y0"], b["y0"])
            smaller = min(m["y1"] - m["y0"], b["y1"] - b["y0"])
            if smaller > 0 and ov / smaller >= 0.5:
                hit = m
                break
        if hit is None:
            merged.append(dict(b))
        else:
            # keep the wider band so the cap-height estimate stays honest
            if (b["y1"] - b["y0"]) > (hit["y1"] - hit["y0"]):
                hit.update(y0=b["y0"], y1=b["y1"],
                           centre_pct=(b["y0"] + b["y1"]) / 2.0,
                           height_px=max(hit["height_px"], b["height_px"]))
    # 2. drop watermark-sized bands
    keep = [b for b in merged if b["height_px"] >= 20]
    if not keep:
        keep = merged
    # 3. top -> bottom
    keep.sort(key=lambda b: b["y0"])
    return keep


def split_words(text):
    parts = [p.strip() for p in re.split(r"[|/]", text or "") if p.strip()]
    return parts or ([text.strip()] if (text or "").strip() else [])


def cards_of(scene, default_start=0.0, default_end=0.0):
    """Text cards of a scene.

    Preferred form (per-beat lockups, the way a real lyric/motion piece works):
        scene["text_cards"] = [{"t_start": 1.2, "t_end": 3.6, "lines": ["lead", "hero"]}]
    Fallback (one block for the whole scene):
        scene["text_on_screen"] = "line one | line two"
    """
    cards = []
    for c in scene.get("text_cards") or []:
        lines = c.get("lines")
        if lines is None:
            lines = split_words(c.get("text", ""))
        if isinstance(lines, str):
            lines = split_words(lines)
        lines = [str(x).strip() for x in (lines or []) if str(x).strip()]
        if not lines:
            continue
        st = float(c.get("t_start", default_start))
        en = float(c.get("t_end", default_end))
        if en <= st:
            continue
        cards.append({"start": st, "end": en, "lines": lines})
    if cards:
        return cards
    lines = split_words(scene.get("text_on_screen", ""))
    if lines and default_end > default_start:
        return [{"start": default_start, "end": default_end, "lines": lines}]
    return []


def render_png(lines, band_list, style_spec, out_path, width, height, stroke_px=0, stroke_colour="#000000"):
    """Full-frame RGBA PNG with the words at the measured band positions.

    stroke_px > 0 draws a heavy outline around the glyphs. Reference title cards
    (heavy condensed caps + thick dark outline) are unreadable without it when
    the lockup sits on a light or saturated field.
    """
    from PIL import Image, ImageDraw, ImageFont

    img = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    # Pick the face that matches the locked typography (sans vs serif).
    typo = ""
    try:
        typo = str((style_spec.get("typography") or "")).lower()
    except Exception:
        typo = ""
    faces = SANS_BOLD if ("sans" in typo or "condensed" in typo) else SERIF_BOLD
    font, font_path = pick_font(faces)

    notes = []
    for i, line in enumerate(lines):
        band = band_list[min(i, len(band_list) - 1)]
        cap_px = max(10, int(band.get("height_px", 0) or height * 0.05))
        em = int(round(cap_px / CAP_RATIO))
        try:
            font = ImageFont.truetype(font_path, em) if font_path != "default" else font
        except Exception:
            font = vlib.load_font(em)
        colour = band.get("colour", "#FFFFFF").lstrip("#")
        rgb = tuple(int(colour[i:i + 2], 16) for i in (0, 2, 4))
        scol = str(stroke_colour or "#000000").lstrip("#")
        srgb = tuple(int(scol[i:i + 2], 16) for i in (0, 2, 4))
        centre = (band.get("y0", 0) + band.get("y1", 0)) / 2.0
        bbox = draw.textbbox((0, 0), line, font=font)
        tw = bbox[2] - bbox[0]
        x = (width - tw) / 2.0 - bbox[0]
        y = centre * height - (bbox[3] - bbox[1]) / 2.0 - bbox[1]
        if stroke_px and stroke_px > 0:
            draw.text((x, y), line, font=font, fill=rgb + (255,),
                      stroke_width=int(stroke_px), stroke_fill=srgb + (255,))
        else:
            draw.text((x, y), line, font=font, fill=rgb + (255,))
        notes.append({
            "words": line,
            "font": Path(font_path).name if font_path != "default" else "default",
            "font_size_px": em,
            "cap_height_px": cap_px,
            "colour": band.get("colour", "#FFFFFF"),
            "stroke_px": int(stroke_px or 0),
            "stroke_colour": str(stroke_colour),
            "band_y_pct": [round(band.get("y0", 0) * 100, 1), round(band.get("y1", 0) * 100, 1)],
            "x_px": round(x, 1),
        })

    img.save(out_path)
    return notes


def build_filter(groups, fade):
    """One filtergraph: each text group is a faded RGBA overlay chained onto the main video.

    overlay takes TWO inputs (main first, overlay second) and outputs one stream, so
    every group is its own two-input filter chained onto the previous result.
    Group i is ffmpeg input i+1 (input 0 is the video itself).
    """
    parts = ["[0:v]format=rgba[base0]"]
    cur = "base0"
    for i, g in enumerate(groups):
        dur = g["end"] - g["start"]
        out_fade = max(0.0, dur - fade)
        parts.append(
            f"[{i + 1}:v]format=rgba,"
            f"fade=t=in:st=0:d={fade:.3f}:alpha=1,"
            f"fade=t=out:st={out_fade:.3f}:d={fade:.3f}:alpha=1,"
            f"setpts=PTS-STARTPTS+{g['start']:.3f}/TB[o{i}]"
        )
        nxt = f"b{i + 1}"
        parts.append(f"[{cur}][o{i}]overlay=0:0:format=auto[{nxt}]")
        cur = nxt
    parts.append(f"[{cur}]format=yuv420p[vout]")
    return ";".join(parts)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--plan", required=True)
    ap.add_argument("--video", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--sheet", default="")
    ap.add_argument("--fade", type=float, default=0.4)
    ap.add_argument("--stroke", type=int, default=0,
                    help="outline width in px around the glyphs (0 = no outline)")
    ap.add_argument("--stroke-colour", default="#000000")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    plan = vlib.jload(args.plan)
    scenes = plan.get("scenes") or []
    style_spec = plan.get("style_spec") or {}
    bands = bands_of(style_spec)
    if not bands:
        bands = [{"y0": 0.44, "y1": 0.50, "height_px": 34, "colour": "#FFFFFF"}]

    info = vlib.probe(args.video)
    W, H = info["width"], info["height"]

    groups, sheet_rows = [], []
    for sc in scenes:
        st_scene = float(sc.get("t_start", 0.0))
        en_scene = float(sc.get("t_end", 0.0))
        cards = cards_of(sc, st_scene, en_scene)
        if not cards:
            continue
        for ci, card in enumerate(cards, 1):
            png = Path(args.out).with_suffix("").parent / (
                f"_text_{sc.get('n', 0):02d}_{ci:02d}.png")
            notes = render_png(card["lines"], bands, style_spec, png, W, H,
                               stroke_px=args.stroke, stroke_colour=args.stroke_colour)
            groups.append({"start": card["start"], "end": card["end"], "png": png,
                           "scene": sc.get("n")})
            for ti, nt in enumerate(notes):
                tier = "hero" if len(card["lines"]) == 1 else (
                    "lead" if ti == 0 else "tail")
                sheet_rows.append({
                    "timestamp": f"{card['start']:.2f}-{card['end']:.2f}",
                    "scene": f"{sc.get('n')}.{ci}",
                    "words": nt["words"],
                    "tier": tier,
                    "font": nt["font"],
                    "size_px": nt["font_size_px"],
                    "colour": nt["colour"],
                    "y_pct": f"{nt['band_y_pct'][0]}-{nt['band_y_pct'][1]}",
                    "animation": f"fade in {args.fade:.2f}s, hold, fade out {args.fade:.2f}s",
                })
            print(f"[text] scene {sc.get('n')}.{ci}: {card['lines']} @ "
                  f"{card['start']:.2f}-{card['end']:.2f}s -> {png.name}")

    if not groups:
        print("[text] no scene carries text_on_screen - nothing to do")
        if args.sheet:
            Path(args.sheet).write_text("# Text overlay sheet\n\n(no text on screen)\n", encoding="utf-8")
        return 0

    # --- video render -----------------------------------------------------
    # The PNGs are looped (infinite) so overlay holds the last frame; the render
    # must be cut to the source duration or ffmpeg encodes forever.
    dur = float(info.get("duration") or 0.0)
    cmd = [vlib.ffmpeg(), "-y", "-hide_banner", "-v", "error", "-i", args.video]
    for g in groups:
        cmd += ["-loop", "1", "-framerate", "30", "-i", str(g["png"])]
    cmd += ["-filter_complex", build_filter(groups, args.fade), "-map", "[vout]", "-map", "0:a?"]
    cmd += ["-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p",
            "-c:a", "copy", "-movflags", "+faststart"]
    if dur > 0:
        # -t (NOT -shortest): the audio stream can be a few ms shorter than the
        # video and -shortest would then cut frames off the end.
        cmd += ["-t", f"{dur:.3f}"]
    cmd += [args.out]
    if args.dry_run:
        print("[filter]", cmd[-3])
        return 0
    vlib.must_run(cmd)
    print(f"[text] wrote {args.out}")

    # --- overlay sheet ----------------------------------------------------
    if args.sheet:
        rows = ["| timestamp | scene | words | tier | font | size px | colour | y % | animation |",
                "|---|---|---|---|---|---|---|---|---|"]
        for r in sheet_rows:
            rows.append("| " + " | ".join(str(r[k]) for k in
                         ["timestamp", "scene", "words", "tier", "font", "size_px", "colour", "y_pct", "animation"]) + " |")
        Path(args.sheet).write_text(
            "# Text overlay sheet\n\n"
            "The words are already burned into the render. Use this table to place the\n"
            "same text by hand in CapCut / Premiere if you want to edit it.\n\n"
            + "\n".join(rows) + "\n", encoding="utf-8")
        print(f"[text] wrote {args.sheet}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
