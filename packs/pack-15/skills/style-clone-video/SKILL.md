---
name: style-clone-video
description: Clone the editing style of a reference video and produce a NEW video from it - extract the reference to frames, measure it with an image-analysis engine, lock a STYLE DNA, generate new scenes with an image-generation tool, animate them, montage them on the beat, and verify the result. Use when the user wants to copy a video's look and feel, make a new video in a reference's style, build a video from stills, or asks for a video skill that can also animate characters. Also use for "استنسخ اسلوب مونتاج", "clone this video's style", "make a new video like this one".
---

# style-clone-video

Turn **one reference video** into **a new video that inherits its style**, with no GPU and
no hand-editing:

```
reference.mp4
  -> [1] FRAMES        ffmpeg: sampled frames + keyframes + contact sheets
  -> [2] ANALYSIS      measure: palette, exposure, grain, vignette, typography, cut rhythm
  -> [3] LOCK          a STYLE DNA + a beat-locked scene plan
  -> [4] GENERATE      new stills per scene, guided by a master style panel
  -> [4b] PROMPTS      portable Flow / Veo / Omni prompts (rebuild the clone elsewhere)
  -> [4c] FILMSTRIP    N consecutive poses in ONE canvas -> slice -> real motion
  -> [5] ANIMATE       camera moves + character liveness + pose-to-pose from a strip
  -> [6] MONTAGE       cut on the beat, professional transitions, music bed, -14 LUFS mix
  -> [6b] TEXT         burn the on-screen words in editing, at the measured bands
  -> [7] VERIFY        frames, duration, black frames, frozen frames, loudness
  -> [8] QC LOOK       look at a frame every 0.5 s, critique, fix, repeat >= 4 rounds
```

The reference is analysed **once** and its style is *locked into a reusable spec*.
Every generated scene repeats that spec verbatim, so the new video looks like the
reference without anyone re-describing it by hand.

## Environment (this machine)

| need | value |
|---|---|
| python | `C:\Users\Admin\.cache\video-editor\style-venv\Scripts\python.exe` (numpy, pillow, opencv-python-headless) |
| ffmpeg / ffprobe | auto-resolved by `scripts/vlib.py` -> `FFMPEG_BIN` env, then `vendor\ffmpeg-*/bin`, then PATH. **Not on PATH.** |
| image generation | the ChatGPT farm at `D:\book the end of world` (node: `D:\Claude\runtime\node\node.exe`) |
| GPU | none. Everything here is CPU. |

Recreate the venv if it is gone:
`uv venv C:\Users\Admin\.cache\video-editor\style-venv --python 3.11` then
`uv pip install --python <venv>\Scripts\python.exe numpy pillow opencv-python-headless`.

## The seven stages

### [0] Intake - the 3 questions

Ask **once**, then never again for this project:
1. **THE IDEA** - what is the new video about? (one line; offer 10 varied options if the
   user has not decided)
2. **TOTAL DURATION** - 20 / 30 / 45 / 60 / 90 s (and the aspect: 9:16, 16:9, 1:1, or
   the reference's own aspect - default: the reference's)
3. **VIDEO LANGUAGE** - the language of the voice-over, and for Arabic the dialect
   (Egyptian / Gulf / MSA)

Everything else is decided by the tool, not the user. Do not write anything else until
the user has answered.

Two documents carry the craft rules for these answers:
`reference/MOTION_BRIEF_TEMPLATE.md` (the PRODUCT / STORY / FORMAT / LOOK / MOTION /
SOUND / QUALITY CHECK / RULES brief) and `reference/FLOW_KINETIC_SPEC.md` (clip
discipline, the text-lockup tiers, the animation menus, the exact Flow prompt shape).

### [1] FRAMES - `scripts/extract_frames.py`

```powershell
& $py scripts\extract_frames.py <reference.mp4> <workdir> --fps 2 --scene 0.25
```

Produces `probe.json`, `cuts.json`, `frames/`, `keyframes/`, `sheets/` (contact sheets with
burned-in timecode). The frame index is timestamp-accurate even for VFR footage.

**Sample the BODY of the reference, not its opening.** A channel intro (title
sequence, mascot, cold open) is often a completely different look from the
episode itself: different palette, different grade, different medium. Locking
the style on the intro produces a clone of the intro, not of the channel. If the
reference is a long episode, sample 4 segments spread over the body and skip the
first minutes. Measure the palette on the BODY - the numbers must agree with the
frames you looked at (saturation, vignette falloff, grain).

### [2] ANALYSIS - `scripts/analyze_frames.py`  (the image-analysis tool)

```powershell
& $py scripts\analyze_frames.py <workdir>\frames <workdir>\style_dna.json --cuts <workdir>\cuts.json
```

Measures per frame and over the sequence: palette (k-means, hex + share), exposure
(mean luma, p01/p99, contrast, saturation), bloom, edge density, sharpness, film grain,
vignette falloff in dB, composition (gradient-energy centroid, rule-of-thirds bias),
**text bands** (horizontal bands of dense fine structure = burned-in titles; each band
reports its y-range, colour and height) and the cut rhythm.

**Then LOOK at the contact sheets and the keyframes yourself.** The script measures; you
interpret. Write the semantic half into `<workdir>\style_notes.json`:

```json
{
  "style_line": "one sentence: the whole look",
  "illustration_style": "photographic / vector / 3D clay / line art ...",
  "camera_language": "how the camera behaves",
  "motion_language": "how things move inside a shot",
  "backgrounds": "what the background looks like",
  "lighting": "key light, contrast, shadows",
  "finish": "grain, bloom, halation, vignette",
  "typography": "family, weight, size, colour, placement",
  "motifs": ["recurring element", "..."],
  "forbidden": ["never do this"],
  "notes": "how you got there"
}
```

A worked example lives in `reference/STYLE_NOTES.example.json`.

### [3] LOCK - `scripts/plan_shots.py scaffold`

```powershell
& $py scripts\plan_shots.py scaffold --style <workdir>\style_dna.json `
    --notes <workdir>\style_notes.json --idea "<the new idea>" `
    --duration 30 --tempo 100 --beat-offset 0.464 --out <workdir>\shot_plan.json
```

- Scene slots are 4 / 6 / 8 / 10 s (the clip lengths the image models actually produce),
  packed to hit the target duration with the fewest cuts.
- With `--tempo` the slot boundaries snap to the **beat grid** of the music, so the
  montage cuts on the beat. The song decides the arc.
- Writes `shot_plan.json`, `STYLE_SPEC.txt` (the locked, copy-pasteable style block)
  and `SCENE_MAP.md` (the table: # | time | length | on-screen text | visual idea | why).

**Then fill the plan**: for every scene set `visual_idea`, `why`, `text_on_screen` and
`prompt_core` (the subject content only - the style block is injected automatically).
`prompt_core` must be the *subject* of the frame: who/what/where/framing. Never the style.

### [4] GENERATE - new stills in the locked style

The style-clone bridge is a **two-hop reference chain**:

```
reference keyframes  ->  MASTER PANEL  ->  every scene
 (4 real frames)        (1 model sheet)    (refs = the panel)
```

The model is shown the *actual frames of the reference* when it builds the master panel,
and it is shown the *master panel* when it builds each scene. That is what makes it a
clone rather than a description.

```powershell
# 1. wire the chain (absolute paths; the farm uploads by path)
& $py scripts\plan_shots.py finalize --plan <workdir>\shot_plan.json `
    --out <workdir>\shot_plan_final.json --scenes <workdir>\scenes.json `
    --master <workdir>\master_panel.json `
    --ref-keyframes <workdir>\keyframes --ref-count 4 `
    --master-panel <workdir>\images\story-01-master-panel.png

# 2. master panel FIRST (one scene)
& $py scripts\farm_run.py --scenes <workdir>\master_panel.json --out <workdir>\images --wait

# 3. then the scenes (each references the panel that now exists)
& $py scripts\farm_run.py --scenes <workdir>\scenes.json --out <workdir>\images --wait
```

`plan_shots.py finalize` produces `scenes.json` (farm format: `n`, `slug`, `prompt`,
`refs`) and `master_panel.json`, and injects the locked style into **every** prompt.
The farm names its output `story-<n>-<slug>.png`, so the master panel lands at
`story-01-master-panel.png` - pass exactly that path to `--master-panel`.

**Farm rules that are enforced by `farm_run.py`, not by good intentions:**

| rule | why |
|---|---|
| **one job at a time** | two supervisors fight over the same Chrome tab, profile and ChatGPT session; both die. `farm_run.py` refuses to start while another job is live (`--status` tells you). |
| **detached + redirected** | piping a long job through a shell truncates the command line and the job dies at the end of the line. |
| visible Chrome only, never headless | the farm drives a real browser. |
| never broad `taskkill` | it would kill the user's own Chrome. |
| the supervisor churns accounts itself | temp accounts live 5-30 min; do not script around it. |
| re-runs skip finished pages | `--wait` is safe to repeat. |
| outputs < 500 KB are corrupt | delete and retry (max 3). |

**A monitoring subagent must run in parallel with the farm job** (it counts outputs,
checks supervisor liveness, restarts a dead supervisor, deletes corrupt PNGs).

### [4b] PROMPTS - `scripts/export_prompts.py` (portable, for Flow / Veo / Omni)

The farm is one renderer. The clone must be rebuildable anywhere, so the same plan is
exported as copy-paste prompts:

```powershell
& $py scripts\export_prompts.py --plan <workdir>\shot_plan_final.json --outdir <workdir>\prompts `
    --clip-length 10 --model "Gemini Omni Flash"
```

Writes one `.md` per scene plus `ALL_PROMPTS.md`. Every file repeats the **identical**
STYLE paragraph (palette hexes, exposure, grain, vignette, illustration language, camera,
composition, typography, motifs, the forbidden list) - never "same as before". Each
scene carries an IMAGE PROMPT (the fully built final frame, with clear space where the
words go), a BACKGROUND PLATE PROMPT (background only) and an ANIMATION PROMPT
(the clip STARTS on the clean background only; elements stagger in over 0.2-0.4 s; the
last 1-2 s settle and HOLD on the final frame; it ends on a hold ready for a hard cut),
ending with the verbatim audio line *"No background music. No voiceover. No dialogue,
speech, singing or lip movement. Silent clip."*

`--clean-plate` strips every text instruction and swaps the words for
"leave clear empty space at [position] for text added later" - use it when the renderer
misspells. The full spec lives in `reference/FLOW_KINETIC_SPEC.md`.


### [4c] FILMSTRIP - many frames from ONE generation

The generator returns one picture per call. To get real character motion, ask it for a
single canvas that already contains **N consecutive poses of the same shot** (a *camera
strip*), then slice that canvas into real frames yourself. One farm call -> one image ->
N frames -> one animated shot. Cheaper than N generations, and the poses are guaranteed
continuous because the model drew them together.

```powershell
# 1. the plan asks for strips (2x2 = 4 frames is the sweet spot)
& $py scripts\plan_shots.py finalize --plan <workdir>\shot_plan.json `
    --out <workdir>\shot_plan_final.json --scenes <workdir>\scenes.json `
    --master <workdir>\master_panel.json --ref-keyframes <workdir>\keyframes `
    --master-panel <workdir>\images\story-01-master-panel.png `
    --filmstrip 4 --filmstrip-layout 2x2 --filmstrip-scenes 2,3,4,5

# 2. the farm returns ONE strip per scene (same refs, same style block)
& $py scripts\farm_run.py --scenes <workdir>\scenes.json --out <workdir>\images --wait

# 3. slice each strip into frames
& $py scripts\slice_filmstrip.py --image <workdir>\images\story-02-scene-02.png `
    --out <workdir>\frames\scene-02 --frames 4 --grid 2x2 --target 1920x960
```

The slicer finds the cells by the content bbox, then the interior gutters (a gutter is
excluded from both neighbours), then equal division. It prints the chosen boundaries and
the mean colour of every cell - read the numbers, a wrong slice is obvious.

Full spec: `reference/FILMSTRIP_MODE.md`.

### [5] ANIMATE - `scripts/animate_shots.py`

```powershell
& $py scripts\animate_shots.py --plan <workdir>\shot_plan_final.json `
    --images <workdir>\images --frames <workdir>\frames --out <workdir>\clips --fps 30
```

Motion types, set per scene in `motion.type`:

| type | what it does |
|---|---|
| `push` | Ken Burns push-in, ~7-8% of frame per 3 s (the reference's own camera language) |
| `pull` | slow zoom out |
| `pan` / `pan_left` | lateral drift at constant zoom |
| `parallax` | blurred background drifting behind a sharper foreground |
| `punch_in` | fast zoom to 1.14-1.18 in ~0.35 s, **then a slow continued push** - the camera never stops, so the shot never freezes |
| `zoom_out` | the same in reverse |
| `live` | **character animation rung 1**: the subject is matted with GrabCut, then breathes (sinusoidal scale) and sways (sinusoidal offset) while the background drifts the other way |
| `pose2pose` | **character animation rung 2**: the sliced filmstrip frames are held in turn, each with its own push, and cross-dissolved into each other - the subject really changes pose |
| `still` | locked frame, micro-drift only |

If the matte is unreliable the tool falls back to `push`; if the filmstrip frames are
missing it falls back to `push` **and says so** in `animation_report.json`. It never
silently ships a still frame.

`live` is the floor of the character-animation track, `pose2pose` is the rung above it.
The ceiling is in `reference/CHARACTER_ANIMATION.md`.

### [6] MONTAGE - `scripts/montage.py`

```powershell
& $py scripts\montage.py --plan <workdir>\shot_plan_final.json --clips <workdir>\clips `
    --out <workdir>\final.mp4 --music <bed.mp3> --vo <vo.wav> --music-db -12 --lufs -14 `
    --transition-mode plan
```

Cuts land on the scene grid (already beat-snapped). Each scene carries its **own**
`transition`:

```json
"transition": "fade", "transition_duration": 0.45
```

The vocabulary is a hard cut plus the ffmpeg reveals: `fade` `fadeblack` `fadewhite`
`dissolve` `radial` `smoothleft` `smoothright` `slideleft` `slideright` `slideup`
`slidedown` `circleopen` `circleclose` `wipeleft` `wiperight` `wipeup` `wipedown`
`zoomin` `zoomout` `hblur` `pixelize`.

The assembler is run-aware: shots joined by a cross-fade form a **run**, a hard cut
starts a new run, and the runs are concatenated. That is what lets a professional edit
mix hard cuts with motivated reveals instead of cross-fading everything.

Rules the tool enforces: **never the same reveal twice in a row**, and cuts are the
default (most edits are cuts). `--transition-mode auto` rotates a
cut-heavy pattern when the plan says nothing; `--transition-mode hard` forces cuts only.
`--xfade` sets the default reveal length (0.45 s); a reveal that needs longer asks for it
and gets it.

Music is ducked 12 dB under the voice-over and the whole mix is normalised to **-14
LUFS** (house target).

**The cross-fade eats time**: every reveal overlaps two shots, so the finished video is
shorter than the sum of the shots. `verify_output.py` accounts for that and compares
against the plan, transition overlap included.

### [6b] TEXT - `scripts/add_text.py` (burn the words in editing)

Image models render small text badly, so the words are added **here**, at the positions
the analyser measured (the text bands of the reference), with the reference's typeface.

```powershell
& $py scripts\add_text.py --plan <workdir>\shot_plan_final.json --video <workdir>\final.mp4 `
    --out <workdir>\final_text.mp4 --sheet <workdir>\text_overlay_sheet.md
```

Per-beat lockups go in the plan as `text_cards` (one card = one hero moment):

```json
"text_cards": [
  {"t_start": 0.46, "t_end": 5.56, "lines": ["xoshm dawey", "wakw chawm"]},
  {"t_start": 5.56, "t_end": 10.66, "lines": ["wakw gyanm", "wakw nawm"]}
]
```

`text_on_screen` (pipe- or slash-separated) is the fallback for one block per scene.
The script writes a **text overlay sheet** (timestamp | scene | words | tier | font |
size px | colour | y % | animation) so the same text can be re-typed by hand in
CapCut / Premiere if the burn-in needs to change.

Rules: max 6 words on screen per beat, one hero word at 3-5x the lead size, the script's
words verbatim, two lockups never overlap, graphics land ~0.05 s before the word.

### [7] VERIFY - `scripts/verify_output.py`

```powershell
& $py scripts\verify_output.py --plan <workdir>\shot_plan_final.json --video <workdir>\final.mp4
```

Checks resolution, duration vs plan, container frame count vs decoded frame count, black
runs, frozen stretches, and loudness vs the target. Prints `[ok]`/`[FAIL]` per check and
writes `final_verify.json`. **Report the numbers, not "it looks good".**

### [8] QC LOOK - `scripts/qc_frames.py` (the quality-check loop)

The single biggest upgrade to a render: **look at a frame every half second, critique
it like a senior motion designer, fix everything, and repeat.**

```powershell
& $py scripts\qc_frames.py --video <workdir>\final_text.mp4 --outdir <workdir>\qc `
    --every 0.5 --width 384 --cols 4 --report <workdir>\qc_report.json
```

Samples the timeline, measures every frame (mean luma, p01/p99, contrast, black ratio,
blown ratio, Laplacian sharpness, delta to the previous frame) and auto-flags **BLACK**,
**FROZEN** (a streak of 3+ identical frames), **BLOWN** (>30% of pixels above 245) and
**FLAT**. It writes contact sheets with burned-in timestamps.

Then **open every sheet with the read tool and look at it.** The script can only find
mechanical faults; the composition, the pacing and the type are your call. Fix the plan,
re-render, run again. **Minimum 4 rounds** before you call it done.

## Hard rules

1. **Never write "same as before" in a scene prompt.** The style block is injected
   mechanically, with the palette HEX, the exposure figures and the typography spec, every
   time. That is the whole point of the lock.
2. **Measure, then look.** The script finds the numbers; you confirm them with your own
   eyes on the contact sheet. A style DNA that was never looked at is a guess.
3. **Clone the style, not the content.** No copyrighted characters, logos, brand names or
   exact copy from the reference. The `forbidden` list is injected into every prompt.
4. **The song decides the arc.** Cuts land on the beat grid; the payoff goes on the
   loudest hit.
5. **Text is added in editing, not in the image.** Image models render small text
   badly. Keep the image text-free and burn titles in afterwards.
6. **A fallback is reported, never hidden.** Matte failure, audio failure, frame-count
   mismatch - all of it goes in the report and in the message to the user.
7. **Verify by ear once.** The numbers pass; the mix still has to be listened to.
8. **The cut is the transition.** Most professional edits are hard cuts. A dissolve
   between two different locations is a mistake, not polish. Only use a reveal when
   it is motivated (a dip to black at an act break, a flash on a light source) and
   keep it short: 4 frames for a soften, 0.45 s for a dip to black.

## What this does not do (state it plainly)

- It cannot restore a voice-over that was never recorded, and it does not synthesise
  speech. `ffmpeg` on this machine has no TTS.
- The generated stills are single frames. `live` gives breathing and sway; `pose2pose`
  (the filmstrip route) gives real pose changes - but neither is articulated acting.
  For that see `reference/CHARACTER_ANIMATION.md`.
- It renders a flat MP4. There are no trimmable edit points for an NLE to open.
- A reference that is itself AI-generated will produce a clone of an AI look; that is
  what "clone the style" means, and it is not a copyright defence.

## Reference files

- `reference/STYLE_DNA.md` - the 13 dimensions of the lock and what each one means.
- `reference/STYLE_NOTES.example.json` - a filled-in example.
- `reference/CHARACTER_ANIMATION.md` - the evolution track from stills to acting.
- `reference/FILMSTRIP_MODE.md` - N frames from ONE generation: the prompt, the slicer,
  the pose-to-pose animation and the failure table.
- `reference/MOTION_BRIEF_TEMPLATE.md` - the brief (PRODUCT / STORY / FORMAT / LOOK /
  MOTION / SOUND / QUALITY CHECK / RULES) + the fill-in template + the Arabic rules.
- `reference/FLOW_KINETIC_SPEC.md` - clip discipline, text lockups, the animation menus,
  the strict Flow prompt format, the clean-plate fallback, the 8 hard rules.
- `reference/BACKENDS.md` - swapping the image generator or adding a VLM.

## The scripts

| script | stage | what it does |
|---|---|---|
| `scripts/extract_frames.py` | 1 | video -> frames, keyframes, contact sheets, cut list, probe |
| `scripts/analyze_frames.py` | 2 | the image-analysis engine -> `style_dna.json` |
| `scripts/plan_shots.py` | 3 | `scaffold` = style lock + beat grid; `finalize` = prompts + farm scenes |
| `scripts/farm_run.py` | 4 | runs the image farm safely (one job at a time, detached) |
| `scripts/export_prompts.py` | 4b | portable Flow / Veo / Omni prompts per scene + `ALL_PROMPTS.md` |
| `scripts/slice_filmstrip.py` | 4c | one strip canvas -> N real frames (bbox + gutters + equal division) |
| `scripts/animate_shots.py` | 5 | stills/strips -> moving clips (push / pull / pan / punch_in / parallax / live / pose2pose / still) |
| `scripts/montage.py` | 6 | clips -> final mp4, per-scene transitions (cut + reveals), music ducked, -14 LUFS |
| `scripts/add_text.py` | 6b | burns the words in at the measured bands + writes the overlay sheet |
| `scripts/verify_output.py` | 7 | frames, duration, black, freeze, loudness -> PASS/FAIL |
| `scripts/qc_frames.py` | 8 | sample every 0.5 s, flag black/frozen/blown/flat, contact sheets |
| `scripts/vlib.py` | - | shared: ffmpeg/ffprobe resolution, json in/out, font loading |

