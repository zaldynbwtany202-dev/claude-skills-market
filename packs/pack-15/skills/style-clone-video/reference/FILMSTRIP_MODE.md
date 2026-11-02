# FILMSTRIP MODE — many frames from ONE generation

The image model gives back **one** picture per call. To get real character
motion we ask it for a single canvas that already contains **N consecutive
frames of the same shot** — a *camera strip*, a flipbook, a sprite sheet — and
then cut that canvas into real frames ourselves.

One farm call → one image → N frames → one animated shot. That is the whole
point: it is cheaper than N generations and it guarantees continuity (the same
camera, the same set, the same character) because the model drew all the
poses at once.

---

## 1. Ask for the strip

`plan_shots.py finalize` appends the instruction automatically when
`--filmstrip N` is given:

```
--filmstrip 4 --filmstrip-layout 2x2 --filmstrip-scenes 2,3,4,5
```

* `--filmstrip N` — frames per strip (0 = off).
* `--filmstrip-layout COLUMNSxROWS` — the grid. **2x2 (4 frames) is the sweet spot**
  because the farm always returns a 16:9 canvas and 2x2 cells are close to a
  16:9 cell. **4x2 (8 frames)** is the practical maximum; a single row of 4 would
  give very narrow cells.
* `--filmstrip-scenes` — which scenes get a strip (empty = all).

**How many frames fit.** The canvas is 16:9, the frame is 2:1, so the cell is
never the frame:

| frames | layout | cell | crop to 2:1 |
|---|---|---|---|
| 4 | 2x2 | 16:9 | none - the cells are already 2:1 inside the canvas |
| 8 | 4 columns x 2 rows | 1:1 | loses half the height, keeps the full width of a wide shot |
| 8 | 2 columns x 4 rows | 4:1 | loses half the width |

More frames = smaller cells = a softer upscale. 8 frames is the limit on a 16:9
canvas; 4 frames stays sharp.

The instruction that goes to the model:

> OUTPUT FORMAT — ONE single image that is a CAMERA STRIP of 4 consecutive
> animation frames of the SAME shot, arranged in a grid of exactly 2 columns
> and 2 rows (row by row, left to right). Every cell shows the same camera
> angle, the same framing, the same background and the same lighting; only the
> subject changes, moving through 4 successive poses of one continuous action
> (step 1 → step 2 → … → step 4, like a flipbook). Cells are equal size,
> separated by thin plain black gutters. Absolutely NO borders, NO frames, NO
> labels, NO numbers, NO arrows, NO captions, NO text anywhere in the image.
> Each cell must be a complete, usable frame of the shot on its own.

Keep the SCENE CORE (subject + action) first, then the strip block, then the
locked STYLE block — same order as a normal scene.

---

## 2. Slice it

```
python scripts/slice_filmstrip.py \
    --image images/story-02-scene-02.png \
    --out  frames/scene-02 \
    --frames 4 --grid 2x2 --target 1920x960
```

The slicer finds the cells in this order:

1. **content bbox** — a uniform black border around the canvas is ignored.
2. **interior gutters** — thin dark lines between the cells split the bbox
   into real panels; the gutter is excluded from both neighbours.
3. **equal division** of the content bbox (always works, even when the model
   draws no gutters).

Each cell is centre-cropped to the target aspect and resized to the target
size, so every output frame is a full, usable frame of the shot. The report
(`slice_report.json`) prints the chosen layout, the boundaries and the mean
colour of every cell — read it, a wrong slice is obvious in the numbers.

Output: `frames/scene-02/frame-01.png … frame-04.png`.

---

## 3. Animate it (pose-to-pose, character motion rung 2)

```
python scripts/animate_shots.py --plan shot_plan_final.json \
    --images images --frames frames --out clips --fps 30 --size 1920x960
```

When the scene's motion type is `pose2pose` the tool:

* reads the N sliced frames,
* gives each frame its own slow push-in (so the camera never stops),
* holds each pose for an equal share of the scene,
* cross-dissolves the poses into each other.

Result: the subject visibly changes pose (aim → fire → smoke → recover) while
the camera keeps moving. If the frames are missing the tool says so and falls
back to `push` — it never silently ships a static shot.

Tunables on the scene:

```json
"motion": {"type": "pose2pose", "crossfade": 0.35, "push": 0.05}
```

---

## 4. What this is and what it is not

| | |
|---|---|
| **Is** | real character motion: poses change, the shot breathes, the camera moves |
| **Is** | one farm call per shot (not per frame) — the cheap, fast route |
| **Is** | continuous with the still-image pipeline: a strip is just a still that contains more information |
| **Is not** | frame-perfect animation — it is pose-to-pose, like limited animation |
| **Is not** | lip sync, cloth, hair or secondary motion |
| **Is not** | a video model: nothing is generated in motion, every pose is a drawn still |

Higher rungs live in `CHARACTER_ANIMATION.md` (pose-to-pose is rung 2; real
2D rig animation is rung 3 and 3D is rung 4).

---

## 5. Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| the slicer reports one giant cell | the model drew a single picture, not a grid | regenerate with a stronger strip instruction; check the PNG by eye first |
| the cells are in the wrong order | the model drew the grid in a different order | swap the cell order in `slice_filmstrip.py` or re-generate |
| the cells have a visible seam | a gutter was not detected | the equal-division fallback already handles it; the seam is at the cell edge only |
| the clip looks like a slideshow | `crossfade` too small for the shot length | raise `crossfade` to 0.5–0.6 s |
| QC flags FROZEN | the shot holds still too long | the punch must be followed by the tail push (already built in) or the shot needs a different motion type |
