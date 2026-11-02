---
name: media-pipeline-design
description: Design robust image, comic, animation, motion-graphics, and video production pipelines with consistent characters and testable rendered outputs. Use for creative media production tasks.
---

# Media Pipeline Design

Plan the pipeline from deliverable backward:
1. Define final output: still image, comic page, short video, animated sequence, motion graphic, or interactive visual.
2. Define visual direction, style references, aspect ratio, resolution, scene count, timing, and quality criteria.
3. Create reusable character/reference sheets and lock identity, proportions, wardrobe, palette, and expressions.
4. Generate or source base imagery only when needed. Keep prompts, references, seeds, and versions organized per project.
5. Separate assets into reusable layers; prefer SVG/PNG layers with clear names and alpha where suitable.
6. Build storyboard, shot list, camera actions, scene transitions, timing, and motion curves.
7. Select the lightest suitable animation/rendering path: HTML/CSS/JS deterministic timeline, SVG, browser rendering, FFmpeg, or existing lightweight tooling.
8. Use heavyweight diffusion/video models only if the hardware or an explicitly available external service supports them. Never assume a 4 GB GPU can run large video models.
9. Validate the final rendered media: dimensions, frame rate, duration, codec, continuity, artifacts, and whether the requested motion is genuinely animated rather than static images or slides.
10. Keep image/video assets separated by project; do not reuse unrelated character assets accidentally.

No audio, speech, STT, TTS, or voice-cloning pipeline.
