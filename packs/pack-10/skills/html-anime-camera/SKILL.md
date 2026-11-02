---
name: html-anime-camera
description: Frame and cut a code-drawn anime â€” wide, close, look room, and where type sits in 16:9 or 9:16. Use when choosing an html-anime shot size, placing a face, or cutting between drawings.
---

# Camera

Cut on the action. The settle is the first frames of the next shot, not the tail of this one.

## Sizes

- Establish is wide. The world is the subject. The figure is small or absent.
- Sakuga is a medium or a tight action. The body reads in silhouette.
- Button is a close-up, or a return to the wide, plus the line.

Get closer by cutting. The only zoom is the 100% to 106% hold described in `C:\Users\Admin\.claude\skills\html-anime-timing\SKILL.md`.

## Placement

Eyes sit on a third. Leave room in front of the gaze. Do not center every face.

The brightest shape is one of: the moon, the blade, the practical light. On the close-up the iris may match that light, using the `iris` hex from the sheet.

## Frame

- 16:9 is 1920Ã—1080. Letterbox bars are part of the frame if you want them. Keep faces out of the bars.
- 9:16 is 1080Ã—1920, composed tall. Head in the upper half. Type in the lower fifth. Do not crop a wide picture into a portrait frame.

## Depth

Back to front is sky, far silhouette, mid figure, rain, close figure, type. Rain may sit between the world and a close figure so the close-up feels nearer than the weather.

## Claude Code local integration

- Upstream: https://github.com/blixvip/html-anime
- Source commit: 6bdd40bc2089408024ed98027db3214956b23f07
- Source file SHA-256 before local adaptation: AB744FD40FB04EF5E53CBC4D981A263A7738E1D3178FFADB0B97AF663D347E04
- Local engine, harness and reference assets: D:\ClaudeCodeSystem\repos\html-anime
- New film projects must be written under D:\ClaudeCodeSystem\projects\html-anime\films\<slug>, not inside the upstream checkout.
- Read the companion native Claude Skills from C:\Users\Admin\.claude\skills\html-anime-* when needed.
- Keep rendering deterministic, locally bundled and reproducible. Do not introduce audio, voiceover, music, SFX, speech synthesis, paid video-model calls or external generation APIs.
- Treat the upstream films\roof project only as structural reference. Do not overwrite or remix it.