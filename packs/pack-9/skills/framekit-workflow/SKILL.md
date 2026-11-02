---
name: framekit-workflow
description: Use the locally installed FrameKit application to process existing videos, GIFs and images into sprite sheets, transparent PNG sequences, GIF, APNG, Animated WebP and Spine-style assets; remove solid backgrounds, clean edges, and edit sprite frames locally.
user-invocable: true
---

# FrameKit Local Media Workflow

Use the installed FrameKit application for frame extraction and animation asset preparation. FrameKit is a browser-local utility, not a generative video model. It does not create original character animation from a text prompt; use the native html-anime Skills for code-drawn 2D scenes.

## Installed source and runtime

- Source checkout: D:\ClaudeCodeSystem\repos\framekit-web
- Production build: D:\ClaudeCodeSystem\repos\framekit-web\dist
- Local projects/output: D:\ClaudeCodeSystem\projects\framekit-output
- NPM cache: D:\ClaudeCodeSystem\cache\npm
- Browser cache: D:\ClaudeCodeSystem\cache\ms-playwright
- Native entry command: `playwright-cli` (configured to use local browser and D-drive cache)

## Start the app

Run the Vite development server from the source checkout and bind only to loopback:

```powershell
Set-Location 'D:\ClaudeCodeSystem\repos\framekit-web'
npm run dev -- --host 127.0.0.1
```

Open http://127.0.0.1:5173/ with the installed Playwright CLI. Keep the development server bound to 127.0.0.1; do not expose it to the LAN or public internet.

Available routes:
- #/sprite-sheet — video to sprite sheet and frame extraction
- #/bg-remove — solid-background removal and edge cleanup
- #/video-gif — video to GIF conversion
- #/sprite-editor — sprite sheet editing and frame ordering
- #/format-converter — PNG sequence, APNG, GIF and Animated WebP conversions
- #/gif-to-sprite — GIF frame extraction and sprite sheet generation

## Operating workflow

1. Inspect the source media metadata and ask only for a missing essential output requirement (for example: frame size or sprite layout).
2. Use the matching route and keep the source asset on the user's local disk.
3. Use chroma key controls conservatively. Preview connected-background removal before exporting to avoid deleting similarly colored details inside the subject.
4. Inspect frame order, crop, playback speed, FPS and output dimensions before export.
5. Export only the requested formats. Prefer transparent PNG sequences or sprite sheets for further editing, APNG/Animated WebP for high-quality web animation, and GIF for simple compatibility previews.
6. Save outputs in D:\ClaudeCodeSystem\projects\framekit-output or the user's explicitly selected local destination.
7. Re-open the exported file or inspect its metadata to verify dimensions, frame count, alpha channel and playback where applicable. Do not claim successful conversion until the output file exists and has been checked.

## Privacy, limits and constraints

- FrameKit is designed for local browser-side processing. Do not upload user media to third-party sites or cloud services.
- No account, hosted backend, model API, voice, music, voiceover or SFX are needed for this workflow.
- The project does not generate original video from text. It processes user-provided existing media.
- Large/high-resolution files may consume substantial browser memory. Process in smaller clips or reduce frame rate/resolution when the browser becomes unstable; do not install GPU-only dependencies.
- Preserve the upstream source checkout. Keep user work and exports outside it.
- If an output format fails, report that specific failure and offer a tested alternative rather than silently changing formats.

## Verification status

- Upstream project: https://github.com/joepUI/framekit-web
- Version: 2.5.0
- Source commit: b134ad6e873cf84c6d6dd99933e80e3e7d60c127
- License: MIT (full notice stored in LICENSE)
- Local production build: PASSED with Vite 6.4.5
- NPM security audit after compatible toolchain and transitive updates: 0 vulnerabilities
- Browser acceptance of the six tools and actual media export is still to be verified per route; do not mark every conversion type accepted based on the build alone.
