"""Stage [4] GENERATE - run the ChatGPT image farm safely.

Wraps `tools/supervise.js` from the farm at `D:\\book the end of world` and adds
the two rules that are easy to break by hand:

  * ONE JOB AT A TIME - two supervisors fight over the same Chrome tab, the same
    profile and the same ChatGPT session, and both die. This script refuses to
    start while another `supervise.js` is alive.
  * supervise.js must be DETACHED with its output redirected to a file. Piping a
    long job through a shell truncates the command line and the job dies at the
    end of the line.

usage:
    python farm_run.py --scenes <scenes.json> --out <outdir> [--rounds 30] [--wait]
    python farm_run.py --status

Exit codes: 0 ok / 10 another job is running / 11 farm missing / 12 node missing
"""
from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
import time
from pathlib import Path

FARM = Path(r"D:\book the end of world")
NODE = Path(r"D:\Claude\runtime\node\node.exe")
SUPERVISE = FARM / "tools" / "supervise.js"
DONE_RE = re.compile(r"ALL DONE", re.I)
START_RE = re.compile(r"\[SUP\]", re.I)


def _ps(script: str) -> str:
    r = subprocess.run(
        ["powershell", "-NoProfile", "-Command", script],
        capture_output=True, text=True, errors="replace",
    )
    return r.stdout or ""


def running_supervisors() -> list[str]:
    """Command lines of every live `supervise.js` / `make-images.js` / `enter-code-now.js`."""
    out = _ps(
        "Get-CimInstance Win32_Process -Filter \"Name='node.exe'\" | "
        "ForEach-Object { $_.CommandLine }"
    )
    hits = []
    for line in out.splitlines():
        s = line.strip()
        if not s:
            continue
        if any(k in s for k in ("supervise.js", "make-images.js", "enter-code-now.js",
                                 "reset-zmail.js", "gen-loop.js")):
            hits.append(s)
    return hits


def status() -> int:
    live = running_supervisors()
    print(f"farm root : {FARM}  exists={FARM.is_dir()}")
    print(f"node      : {NODE}  exists={NODE.exists()}")
    if live:
        print(f"farm busy : {len(live)} live job(s)")
        for s in live:
            print(f"           {s}")
        return 10
    print("farm free : no live supervisor")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--scenes")
    ap.add_argument("--out")
    ap.add_argument("--rounds", type=int, default=30)
    ap.add_argument("--wait", action="store_true")
    ap.add_argument("--timeout", type=float, default=3600.0)
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--status", action="store_true")
    args = ap.parse_args()

    if args.status:
        return status()

    if not args.scenes or not args.out:
        ap.error("--scenes and --out are required")
    if not SUPERVISE.is_file():
        print(f"[farm] MISSING {SUPERVISE}")
        return 11
    if not NODE.exists():
        print(f"[farm] MISSING {NODE}")
        return 12

    live = running_supervisors()
    if live and not args.force:
        print("[farm] REFUSING: the farm is already busy. One job at a time.")
        for s in live:
            print(f"[farm]   {s}")
        print("[farm] Wait for it to finish, or use --force if you know it is dead.")
        return 10

    scenes = Path(args.scenes)
    if not scenes.is_absolute():
        scenes = (FARM / scenes).resolve()
    if not scenes.is_file():
        print(f"[farm] scenes file not found: {scenes}")
        return 13
    outdir = Path(args.out)
    if not outdir.is_absolute():
        outdir = (FARM / outdir).resolve()
    outdir.mkdir(parents=True, exist_ok=True)

    log = outdir / "_farm.log"
    err = outdir / "_farm.err.log"
    cmd = [str(NODE), "tools/supervise.js", str(scenes), str(outdir), str(args.rounds)]

    print(f"[farm] scenes : {scenes}")
    print(f"[farm] outdir : {outdir}")
    print(f"[farm] log    : {log}")

    env = dict(os.environ)
    env.setdefault("PYTHONUTF8", "1")
    # DETACHED_PROCESS: the job must outlive this shell.
    flags = getattr(subprocess, "DETACHED_PROCESS", 0x00000008) | getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0x00000200)
    with open(log, "w", encoding="utf-8", errors="replace") as lf, \
         open(err, "w", encoding="utf-8", errors="replace") as ef:
        proc = subprocess.Popen(cmd, cwd=str(FARM), stdout=lf, stderr=ef,
                                stdin=subprocess.DEVNULL, env=env,
                                creationflags=flags, close_fds=True)
    print(f"[farm] pid    : {proc.pid}")

    if not args.wait:
        print("[farm] running detached. Poll the log or run: farm_run.py --status")
        return 0

    deadline = time.time() + args.timeout
    seen = 0
    while time.time() < deadline:
        time.sleep(5)
        if proc.poll() is not None:
            break
        try:
            txt = log.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        lines = [l for l in txt.splitlines() if START_RE.search(l)]
        if len(lines) > seen:
            for l in lines[seen:]:
                print(f"[farm] {l.strip()}")
            seen = len(lines)
        if DONE_RE.search(txt):
            print("[farm] supervisor reported ALL DONE")
            break

    code = proc.poll()
    if code is None:
        print("[farm] still running (timeout) — it is detached, leave it alone")
        return 0
    try:
        tail = log.read_text(encoding="utf-8", errors="replace").splitlines()[-8:]
    except OSError:
        tail = []
    for l in tail:
        print(f"[farm] | {l}")
    if err.is_file():
        et = err.read_text(encoding="utf-8", errors="replace").strip()
        if et:
            print("[farm] stderr:")
            for l in et.splitlines()[-6:]:
                print(f"[farm] ! {l}")
    print(f"[farm] exit {code}")
    return 0 if code == 0 else code


if __name__ == "__main__":
    raise SystemExit(main())
