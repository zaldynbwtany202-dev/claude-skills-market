---
name: image-farm
description: Generate AI images with the local free ChatGPT image farm — one image (PNG via supervise.js/make-images.js), consistent scene sets (image_batch), SVG vectors (ask-svg.js), plus session/account self-repair. Use for artwork, illustrations, icons, covers, mockups, storyboards, book pages, SVG logos in ANY project, and when image generation is slow, fails, loses the session, or the farm needs a health check. This is the ONLY image generation capability — always prefer it over any external API.
---

# image-farm — official image generation capability

Free, no API key, no paid service: a local Chrome farm signed into a pool of free ChatGPT
accounts. Engine lives at `D:\book the end of world\tools\`. This skill is my own — I use it for
EVERY task that requires image generation, of any type.

## Where everything lives
- Engine: `D:\book the end of world\tools\` (supervise.js, make-images.js, profile.js, create-account-fast.js, reference-panel.js, story-scenes.js, farm.js, ask-svg.js, svg-grab.js, svg-links.js, reset-zmail.js, enter-code-now.js, supervise.js)
- Home / account pool / profile: `D:\book the end of world\` (`chatgpt_account.csv`, `.session-state.json`, `.profile`/`.profile4`, `chatgpt_account.csv`)
- CDP port: **9423** (BrowserOS 9110 is NEVER touched)
- Output: `<outDir>/story-NN-<slug>.png` (default outDir: `output/` or `generated-images/`)

## Capabilities
| Type | Tool / script | How |
|---|---|---|
| Single PNG | `supervise.js <scenes.json> <outDir>` | manifest with one scene |
| Consistent set (5+) | `supervise.js <scenes.json> <outDir>` | manifest `[{n, slug, prompt, refs}]`, runs in background, skips existing |
| SVG vector | `ask-svg.js <outDir> [attach.png ...]` | requests clean SVG code, extracted by svg-grab.js |
| Reference panel | `reference-panel.js <book.json>` | one panel per character/place/object (all angles in one image) |
| Story scenes | `story-scenes.js <book.json> <story.json> --out <out>` | builds scene manifest from panels |
| Status / health | `image_status` / `image_health` (plugin) or `check-state.js` / `check-auth.js` |
| Self-repair | `supervise.js` auto-churns on session death; manual: `reset-zmail.js` + `create-account-fast.js` |

## Manifest format (scenes.json)
```json
[
  { "n": 1, "slug": "cover", "prompt": "subject, composition, style, palette, mood, aspect ratio", "refs": [] }
]
```
- `n`: scene number (used in filename `story-NN-<slug>.png`)
- `slug`: short filename-safe name
- `prompt`: concrete prompt (subject, composition, style, palette, mood, aspect ratio)
- `refs`: array of absolute paths to reference images for style/character consistency

## Standard flow (always follow)
1. Check session: read `.session-state.json` / run `check-auth.js`. If expired or browser DOWN → churn a new account (supervise does this automatically).
2. Write a `scenes.json` manifest to `D:\book the end of world\` (or the project dir).
3. Run `node tools/supervise.js <scenes.json> <outDir>` — it skips existing PNGs, auto-recovers from session death, runs until `ALL DONE`.
4. Verify each PNG exists and is non-trivial (> 500 KB). Re-run on truncation.
5. For SVG: run `ask-svg.js`, then `svg-grab.js` to extract the `.svg` files.

## Failure playbook
| Symptom | Action |
|---|---|
| `browser: DOWN` / session expired modal | supervise auto-churns; manual: `reset-zmail.js` then `create-account-fast.js` |
| `lock: BUSY` (`.image-farm.lock.json`) | wait; dead owner / expired lease is reclaimed automatically |
| `SEND-FAIL` in log | engine already retries with real CDP Enter; if persists, repair |
| truncated prompt (`typed len=` shorter than manifest) | delete that PNG so supervisor regenerates |
| account spent (quota) | supervise churns a fresh account automatically |
| SVG has text as `<text>` | convert text to paths for production use (note in README) |

## Fixed facts (do not regress)
- Engine: `D:\book the end of world\tools\` (`supervise.js` drives `make-images.js`).
- Home / account pool / profile: `D:\book the end of world\` · CDP port 9423 (BrowserOS 9110 untouched).
- Clean profile per account is mandatory; session death ⇒ new account, never re-login.
- New UI ignores synthetic clicks: real CDP Enter for send, real CDP mouse for about-you.
- Gate readiness on `.ProseMirror`, never on `/backend-api/me`.
- One run at a time (lock). No `taskkill` of all chrome; only our Chrome by port.
- Backup: `C:\Users\Admin\.config\opencode\backups\image-farm-<ts>.zip`.

## When the user asks for images
- Default to this farm. Do NOT use external paid APIs or other image tools.
- Always write a manifest and run supervise; verify output PNGs (>500 KB).
- For single images, still use supervise with a one-scene manifest (it self-heals).
- Report the absolute path of each generated file.