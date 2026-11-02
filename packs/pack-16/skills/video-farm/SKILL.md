---
name: video-farm
description: Generate video clips with BytePlus Ark Seedance through the signed-in BrowserOS console — one clip (video_generate) or a live status check (video_status). Use for b-roll, product shots, scene tests, animation loops, establishing shots, or any project that needs a generated MP4. No API key: the plugin drives the trial generator UI the user is already signed into, then downloads the finished file locally.
---

# video-farm — official video generation capability

Two tools exist in **every** workspace. No API key, no arkcli. The plugin drives the BytePlus
Ark Seedance console page in BrowserOS (the user's signed-in session) and saves the result as MP4.

| Tool | What it does | Key args |
|---|---|---|
| `video_generate` | Prompt → console submit → poll → download MP4 → ffprobe | `prompt`, `name`, `out_dir`, `duration_sec` (4–12, default 5), `model`, `timeout_sec` |
| `video_status` | Live generator tab, progress, visible video, last 5 jobs | none |

## Standard flow

1. Write the prompt as subject + action + camera move + lighting + mood. One clip, one idea.
2. Call `video_generate` with `name` (slug) and `duration_sec` when 5 s is not right.
3. It opens/uses the `gen_video` tab, primes the composer with a template `Recreate`, replaces the
   text with your prompt, sets the duration chip, submits, and polls every 4 s.
4. On completion it downloads the clip, runs ffprobe, writes a job JSON, and returns
   `title` / `output` (path, size, codec, resolution, fps, task URL) / `metadata`.
5. Typical run: 60–120 s for a 5 s clip. Longer durations cost more tokens and take longer.

## Output layout

```
<project>/generated-videos/<slug>.mp4          # default out_dir
C:\Users\Admin\.config\opencode\vendor\video-farm\jobs\<iso>.json   # job record
C:\Users\Admin\.config\opencode\vendor\video-farm\jobs\.lock        # single-run lock
```

## Failure playbook

| Symptom | Cause / action |
|---|---|
| `another video generation is running (pid …, Ns)` | A run holds `jobs\.lock`. Wait for it, or delete the lock if the pid is gone. |
| `BrowserOS CDP unreachable` | Run `powershell -NoProfile -ExecutionPolicy Bypass -File C:\Users\Admin\.config\opencode\bin\start-browseros.ps1`. |
| `tab did not hydrate` logged, then success | Normal: the long-lived tab showed only the console shell; a fresh tab hydrated in ~2 s. |
| `generator editor never appeared` | The console is signed out or the page changed. Open the URL in BrowserOS and check. |
| `submit stayed disabled after inserting the prompt` | Template priming failed (site UI change). Re-run; if it repeats, inspect the Recreate button with `video_status`. |
| `timed out after …` with a task URL | Rendering is slow. Open the task URL — the clip may already be there; re-running is not needed. |
| clip is 960×536 / 10 s / 765,991 B | That is `vision_loading_optimized_960.mp4`, the loading animation. The filter blocks it; if it appears, the selection guard regressed. |
| clip is not 1280×720 | The console's ratio/resolution chips were changed by hand. Set `16:9` + `720P` in the tab, then re-run. |

## Fixed facts (do not regress)

- BrowserOS CDP `127.0.0.1:9110`; start via `C:\Users\Admin\.config\opencode\bin\start-browseros.ps1`.
- Model `seedance-1-5-pro-251215`; console `https://console.byteplus.com/ark/region:ap-southeast-1/experience/gen_video?model=seedance-1-5-pro-251215`.
- Prompt entry must go through the editor state: `focus()`, `execCommand('selectAll')`, `execCommand('insertText', …)`. Plain CDP typing never enables submit.
- Submit needs a template `Recreate` click first; the plugin hit-tests with `document.elementFromPoint`, then replaces the text.
- The real clip is served from `ark-common-storage-*-prod-*.tos-*.volces.com` after the page shows `Regenerate` / `Edit again`.
- One generation at a time (`jobs\.lock`, 20 min lease, dead-owner reclaim). Never run two.
- Never touch the user's own Chrome/profile, never broad-taskkill, no cron.
- ffprobe: `C:\Users\Admin\Videos\VIDEOMAKERGEN\vendor\ffmpeg-9.0.2-essentials_build\bin\ffprobe.exe`.

Backup: `C:\Users\Admin\.config\opencode\backups\video-farm-<ts>.zip` (plugin + loader + skill).
