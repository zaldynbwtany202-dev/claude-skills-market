---
name: handpainted-character-animation
description: Create polished hand-painted 2D cartoon character animations with consistent character design, acted emotions, readable storyboards, frame-accurate motion, brush-painted backgrounds, transitions, contact-sheet review, and silent MP4 rendering. Use for 2D cartoon, hand-drawn, p5.js, p5.brush, character animation, animated GIF/video, storyboard, or character motion tasks.
---

# Hand-Painted Character Animation

Use this skill for crafted 2D cartoon or hand-painted character animation. The bundled engine and visual guide are in engine/ and references/ANIMATION_GUIDE.md.

## Non-negotiable constraints

- Visual-only. Render silent video and image sequences. Do not add, generate, process, mux, transcribe, synthesize, or otherwise use audio, speech, music, soundtrack, or voice features.
- Preserve a user-provided character/person's visible identity and proportions where relevant. Do not redesign their face or alter identity.
- Use 2D painted shapes and frame-by-frame acting; do not substitute a slideshow, simple CSS transforms, or fake 3D rotation.
- Never claim rendering succeeded until the output file exists and has been inspected.
- Keep generated outputs in the user's project/output directory, not inside the Skill directory.

## Workflow

1. Read references/ANIMATION_GUIDE.md before designing shots. Use model sheets in engine/docs/ for character views and expressions.
2. Understand the story, duration, aspect ratio, visual style, character identity, setting, and supplied reference assets. Reuse known context; do not ask again for details already given.
3. Create a concise storyboard before coding. Give each shot a clear action, anticipation, readable action/reaction timing, a held payoff, and a transition. The result must feel like one connected short film.
4. Plan a consistent character model, poses, expressions, props, and backgrounds. Preserve character proportions and design between frames.
5. Copy engine/ into the target project (for example, project/animation-engine/) before editing. Keep the original Skill engine untouched.
6. Inspect the copied src/config.js, src/scenes/demo.js, studio.html, and render.mjs. Replace the demo scene with the requested story; do not reuse its narrative or model unless asked.
7. Implement deterministic frames as pure functions of time. Use acting, easing, camera, brush, timing, transition, and view helpers.
8. Render contact sheets, frame strips, face crops, and transition frames. Inspect silhouettes, contacts, timing, continuity, line stability, and quality. Repair and render again.
9. Render silently with node render.mjs --clip --out=out/video.mp4, or use --frames then --encode. ffmpeg is required for MP4 encoding; Chrome and Node are required for rendering.
10. Inspect the output file, duration, dimensions, visual continuity, and logs. Report actual evidence and limitations.

## Hardware-aware rendering

Start with one rendering worker on this hardware class. Test a short section before a full render. p5.brush watercolor fills can be slow without a high-end GPU; reduce expensive watercolor layers, simplify background detail, reuse static assets, and reserve close-ups for important moments. Do not install large GPU frameworks or AI video models automatically.

## Engine map

- engine/src/clawd.js: character, emotions, views, poses, accessories.
- engine/src/core.js: painting, motion, camera, timing, visual effects.
- engine/src/timeline.js: shots, loops, transitions.
- engine/render.mjs: contact sheets, strips, crops, stills, silent MP4 rendering.
- engine/studio.html: browser preview and scrubbing.
- engine/docs/emotions.jpg and engine/docs/views.jpg: model sheets.
- references/ANIMATION_GUIDE.md: animation and rendering reference.
