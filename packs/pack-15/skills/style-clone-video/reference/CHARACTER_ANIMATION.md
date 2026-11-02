# Character animation - the evolution track

The skill today moves a still. This file is the ladder from "still that breathes" to
"character that acts", and which rung each rung costs.

## Rung 0 - camera moves only (shipped)

`push`, `pull`, `pan`, `parallax`, `still`. The frame is fixed, the camera is not.
Zero extra cost, zero risk of artefacts. Already in `animate_shots.py`.

## Rung 1 - `live`: breathing and sway (shipped)

What `motion.type = "live"` does today:

1. **Matte the subject** with OpenCV GrabCut: seed the central region as probable
   foreground, the border as background, 4 iterations, morphological open+close, Gaussian
   blur, then upsample to full resolution.
2. **Quality gate**: if the matte covers < 4% or > 90% of the frame it is rejected and the
   shot falls back to `push`. The fallback is recorded in `animation_report.json`.
3. **Two layers**: the background is scaled, cropped with a slow sinusoidal drift and
   blurred; the foreground is the matted subject.
4. **Breathing**: the foreground is rescaled per frame by
   `1 + 0.014*sin(2*PI*t/3.4)` - a 3.4 s cycle, 1.4% peak.
5. **Sway**: the foreground is offset by `14*sin(2*PI*t/5)` px horizontally and
   `6*sin(2*PI*t/3.4)` px vertically.

Why it works: a still that is *exactly* still reads as a photograph. A still with two
slow, out-of-phase sinusoids reads as a person standing there. It is the cheapest
possible "alive".

Limit: it is a loop, not a performance. The character never changes pose.

## Rung 2 - pose-to-pose motion (SHIPPED — the filmstrip route)

`motion.type = "pose2pose"` turns a FILMSTRIP into a performance: the scene was
generated as ONE canvas holding N consecutive poses of the same shot, the
canvas is sliced into N frames, every frame is held in turn with its own slow
push-in, and the poses are cross-dissolved into each other. The subject
actually changes pose (aim → fire → smoke → recover) while the camera keeps
moving.

- Needs: a way to get key poses → **the filmstrip** (one generation, N poses).
  See `FILMSTRIP_MODE.md`.
- The crossfade duration is a beat fraction, not a fixed 0.3 s.
- No per-pose matte is needed: the poses are already registered because the
  model drew them in one image.
- Limit: it is pose-to-pose, i.e. limited animation. No in-between frames, no
  cloth, no hair.

## Rung 2b - key poses drawn one by one (the next build)

The subject is matted in several key poses, and the tool crossfades between them on the
beat, with the matte driving a small amount of registration drift so the blend reads as
movement rather than a dissolve.

- Needs: a way to get key poses. Either an image-to-image model per pose (the farm can
  be driven with a reference attachment), or a rig.
- The matte must be re-estimated per pose, or the mask must be propagated from the first
  pose with a forward-backward consistency check.
- The crossfade duration is a beat fraction, not a fixed 0.3 s.

## Rung 2b - key poses drawn one by one (the next build)

The filmstrip gives poses but no control over WHICH poses. Driving the farm once
per pose (each pose prompted separately, with the previous pose attached as a
reference image) gives full control of the action: step 1 aim, step 2 fire,
step 3 recoil.

- The reference attachment keeps the style and the character locked.
- Registration drift between poses is the hard part: the matte must be
  re-estimated per pose, or propagated from the first pose with a
  forward-backward consistency check, otherwise the blend swims.
- Cost: N generations per shot instead of 1.
- It is the bridge to rung 3: once poses are controlled, the same data drives
  a real rig.

## Rung 3 - real 2D animation (the target)
Bring in a vector rig: the character is redrawn as layered shapes (skia, like
`vendor/ai-motion-graphics/scripts/flat25d_kit.py`) or as an SVG with bone-free
parameterised limbs (the `vendor/animate` grammar: `src/scenes.js` with timed actions
`TT`, `ev(t,d)`, `popS(t)`).

- The style lock still applies: same palette, same finish, same grain and vignette.
- The output is frames, and the montage stage is unchanged.
- Cost: the whole animation stage is replaced by a renderer, not a filtergraph.

## Rung 4 - 3D / volumetric

`vendor/ai-motion-graphics` mode G: Three.js headless Chromium, animation in the vertex
shader, instanced geometry, clay shading, log-zoom camera. The style lock maps onto
palette, camera and finish; the "illustration" dimension becomes a shader/material spec.

## What does NOT work and must not be attempted here

- **No video-generation model on this machine.** No GPU, no fal key, no Veo/Flow access.
  Anything that needs a diffusion model must run somewhere else, or not at all.
- **No TTS.** There is no local voice synthesis. A voice-over has to be recorded or
  supplied; the skill can only place and duck it.
- **Do not fake a face.** If the reference has a real face and the new video claims to
  show a person talking, that is a different product (talking-head avatars) and it needs
  a lip-sync model. This skill does not do that.

## The honest line

Rung 1 gives a still that is alive. Rung 3 gives a character that acts. Everything
between is a cost decision, not a technical mystery. Say which rung a result is on.
