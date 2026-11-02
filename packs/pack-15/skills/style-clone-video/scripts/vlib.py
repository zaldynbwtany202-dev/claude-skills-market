"""Shared helpers for the style-clone-video skill.

Everything here is Windows-safe: no ffmpeg on PATH, no global python packages.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

# ---------------------------------------------------------------- environment

def setup_env() -> None:
    os.environ.setdefault("PYTHONUTF8", "1")
    os.environ.setdefault("HF_HUB_DISABLE_SYMLINKS", "1")
    os.environ.setdefault("NLTK_ALLOW_PROXIED_URLOPEN", "1")
    os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")


def _find(tool: str) -> str:
    """Resolve ffmpeg/ffprobe: env override -> project vendor dir -> PATH."""
    exe = os.environ.get(tool.upper() + "_BIN")
    if exe and Path(exe).exists():
        return exe
    roots = [
        Path(r"C:\Users\Admin\Videos\VIDEOMAKERGEN\vendor"),
        Path(__file__).resolve().parents[3] / "vendor",
    ]
    for root in roots:
        if root.exists():
            # portable builds ship both ffmpeg.exe and ffprobe.exe in one ffmpeg-* dir
            hits = sorted(root.glob(f"ffmpeg-*/bin/{tool}.exe"))
            if hits:
                return str(hits[-1])
    found = shutil.which(tool)
    if found:
        return found
    raise SystemExit(
        f"[{tool}] not found. Set {tool.upper()}_BIN to the full path of {tool}.exe."
    )


def ffmpeg() -> str:
    return _find("ffmpeg")


def ffprobe() -> str:
    return _find("ffprobe")


# ------------------------------------------------------------------- process

def run(cmd: list[str], timeout: int = 3600) -> subprocess.CompletedProcess:
    """Run a native command, never raising on non-zero (we inspect ourselves)."""
    return subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=timeout,
    )


def must_run(cmd: list[str], timeout: int = 3600) -> subprocess.CompletedProcess:
    p = run(cmd, timeout=timeout)
    if p.returncode != 0:
        tail = "\n".join((p.stderr or "").strip().splitlines()[-25:])
        raise SystemExit(f"command failed ({p.returncode}):\n{' '.join(cmd[:6])} ...\n{tail}")
    return p


# ---------------------------------------------------------------------- json

def jdump(obj, path) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(obj, fh, ensure_ascii=False, indent=2)
        fh.write("\n")


def jload(path):
    # utf-8-sig tolerates the BOM that Windows PowerShell 5.1 writes
    with open(path, "r", encoding="utf-8-sig") as fh:
        return json.load(fh)


# ---------------------------------------------------------------------- ffmpeg

def probe(path) -> dict:
    """ffprobe -> {width,height,fps,duration,nb_frames,audio,nb_streams}"""
    cmd = [
        ffprobe(), "-v", "error", "-print_format", "json",
        "-show_format", "-show_streams", str(path),
    ]
    data = json.loads(must_run(cmd).stdout)
    v = next((s for s in data["streams"] if s["codec_type"] == "video"), None)
    a = next((s for s in data["streams"] if s["codec_type"] == "audio"), None)

    def _fps(s):
        if not s:
            return 0.0
        for key in ("avg_frame_rate", "r_frame_rate"):
            num, _, den = s.get(key, "0/1").partition("/")
            try:
                if int(den):
                    return float(num) / float(den)
            except ValueError:
                pass
        return 0.0

    out = {
        "width": int(v["width"]) if v else 0,
        "height": int(v["height"]) if v else 0,
        "fps": round(_fps(v), 5),
        "duration": float(data["format"].get("duration", 0.0)),
        "nb_frames": int(v.get("nb_frames", 0)) if v else 0,
        "codec": v.get("codec_name") if v else None,
        "pix_fmt": v.get("pix_fmt") if v else None,
        "has_audio": a is not None,
        "audio_codec": a.get("codec_name") if a else None,
        "sample_rate": int(a["sample_rate"]) if a and a.get("sample_rate") else 0,
        "channels": int(a.get("channels", 0)) if a else 0,
        "raw": data,
    }
    return out


def frame_pts(path) -> list[float]:
    """Exact presentation timestamps of every video frame (VFR safe)."""
    cmd = [
        ffprobe(), "-v", "error", "-select_streams", "v:0",
        "-show_entries", "frame=pts_time", "-of", "csv=p=0", str(path),
    ]
    pts = []
    for line in must_run(cmd).stdout.splitlines():
        line = line.strip().strip(",")
        if line and line != "N/A":
            try:
                pts.append(float(line))
            except ValueError:
                pass
    return pts


def scene_cuts(path, threshold: float = 0.25) -> list[dict]:
    """Detect hard cuts with ffmpeg's scene score. -> [{t, score}]

    The metadata is printed to the log at INFO level; the `file=` variant
    breaks on Windows paths (drive letter is parsed as a filter option).
    """
    cmd = [
        ffmpeg(), "-hide_banner", "-v", "info", "-i", str(path),
        "-filter:v", f"select='gt(scene,{threshold})',metadata=print",
        "-an", "-f", "null", "-",
    ]
    p = run(cmd)
    text = (p.stdout or "") + "\n" + (p.stderr or "")
    cuts, cur = [], {}
    for line in text.splitlines():
        if "pts_time:" in line:
            try:
                cur["t"] = float(line.split("pts_time:")[1].split()[0])
            except (IndexError, ValueError):
                cur = {}
        elif "lavfi.scene_score" in line:
            try:
                cur["score"] = float(line.split("scene_score=")[-1].strip())
            except (IndexError, ValueError):
                cur["score"] = 0.0
            if "t" in cur:
                cuts.append(cur)
            cur = {}
    return cuts


# ----------------------------------------------------------------------- font

FONT_CANDIDATES = [
    r"C:\Windows\Fonts\segoeui.ttf",
    r"C:\Windows\Fonts\arial.ttf",
    r"C:\Windows\Fonts\calibri.ttf",
]


def load_font(size: int):
    from PIL import ImageFont

    for path in FONT_CANDIDATES:
        if Path(path).exists():
            try:
                return ImageFont.truetype(path, size)
            except Exception:
                pass
    return ImageFont.load_default()


def hexof(rgb) -> str:
    return "#{:02X}{:02X}{:02X}".format(int(rgb[0]), int(rgb[1]), int(rgb[2]))


def eprint(*a):
    print(*a, file=sys.stderr, flush=True)
