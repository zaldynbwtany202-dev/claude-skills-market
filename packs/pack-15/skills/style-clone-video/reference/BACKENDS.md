# Backends - what you can swap in

The pipeline is backend-agnostic at two seams: **image generation** and **image
understanding**. Everything else (frames, beats, montage, verify) is local and free.

## Image generation

### Installed and working: the ChatGPT farm

`D:\book the end of world` - driven by the `imagegengpt` skill.

```
cd "D:\book the end of world"
D:\Claude\runtime\node\node.exe tools\supervise.js <scenes.json> <outdir> [maxRounds]
```

- `scenes.json` = `[{n, slug, prompt, refs:[...]}]`; `refs` are **absolute paths** to images
  auto-attached to the composer. That is how the style is cloned: the master panel is
  generated *from* the reference's own keyframes, and every scene is generated *from* the
  master panel.
- Output name = `story-<String(n).padStart(2,'0')>-<slug>.png` in `<outdir>`.
- The supervisor self-heals: on a dead session it churns a new account (~38 s), retries on
  TYPE-FAIL / SEND-FAIL, skips already-rendered pages, prints `ALL DONE` at the end.
- Output: ~1672x941, ~18-44 s per page.
- Node is **not** on PATH: always `D:\Claude\runtime\node\node.exe`.
- Visible Chrome only. Never headless. Never a broad `taskkill`. The farm uses its own
  profile (`D:\book the end of world\.profile`) - do not touch the user's Chrome.
- Mailbox: zemail.me only.
- **One job at a time.** Two supervisors fight over the same Chrome tab, the same profile
  and the same ChatGPT session, and both die. Use `scripts/farm_run.py`, which refuses to
  start a second job and runs the supervisor detached with its output redirected to a file
  (piping a long job through a shell truncates the command line and kills the job).
- A **monitoring subagent** must run in parallel with the farm job.

Other tools in the farm, for reference:

| tool | what it does |
|---|---|
| `tools/make-images.js` | the worker: attaches `refs`, types the prompt, saves the PNG |
| `tools/master-ref.js <prompt.md> <outDir>` | sends one long prompt, saves `master-ref-panel.png` |
| `tools/reference-panel.js <book.json>` | per-character/place/prop sheets (book pipeline, not style clone) |
| `tools/send-master-panel.js <book-dir>` | sends an existing `master-panel.png` + its prompt |
| `tools/story-scenes.js` | builds `scenes.json` from `book.json` + `story.json` |

This is the default and the only backend proven on this machine.


### Not available here (do not build on them)

- **MeiGen MCP** - command files exist in `C:\Users\Admin\.config\opencode\commands\`
  but there is no `meigen` server in `opencode.json`. The commands are stale.
- **fal.ai** - no `FAL_KEY`, no CLI, no MCP server.
- **Any local diffusion model** - no GPU, and no model weights on disk.

To add one later, the seam is `plan_shots.py finalize --scenes`: anything that can turn
`[{n, slug, prompt, refs}]` into `{slug}.png` files can replace the farm.

## Image understanding

### Installed and working: offline measurement + the agent's own eyes

`analyze_frames.py` gives hard numbers (palette, exposure, grain, vignette, typography
geometry, composition, cut rhythm). The semantic half - illustration language, camera
language, motifs - comes from **looking** at the contact sheets and writing
`style_notes.json`.

This split is deliberate: numbers are reproducible, descriptions are judgement, and the
judgement is the part a model should not be asked to fake.

### Optional plug-in: a VLM

Any OpenAI-compatible vision endpoint can be pointed at the contact sheets to draft the
`style_notes.json` semi-automatically. On this machine the local LiteLLM gateway
(`http://127.0.0.1:4000/v1`) is the intended target, but it is **not running by default**
- check it before relying on it:

```powershell
try { (Invoke-WebRequest http://127.0.0.1:4000/v1/models -TimeoutSec 3).StatusCode }
catch { "gateway down - use the agent's own vision instead" }
```

Do not block on the gateway. The measurement path is the primary path.

## Audio

- The reference's music can be reused as a bed for the montage (it *is* the style).
- No TTS. A voice-over must be recorded or supplied.
- Target mix: music 12 dB under the voice, whole mix normalised to -14 LUFS.

## The image-farm plugin (a general capability, not this skill's tool)

`image_generate` / `image_batch` / `image_status` are **opencode plugin tools** - any
project can ask for generated images through them.

| what | where |
|---|---|
| engine source | `C:\Users\Admin\.config\opencode\vendor\image-farm\` (profile.js · make-images.js · chat.js · reset-zmail.js · enter-code-now.js · supervise.js) |
| plugin loader | `C:\Users\Admin\.config\opencode\plugins\image-farm.js` |
| farm home (own accounts pool + own browser profile) | `C:\Users\Admin\.config\opencode\vendor\image-farm\home\` |
| CDP port | **9424** (BrowserOS is 9110; the user's own Chrome is never touched) |
| self-test of the same code path | `C:\Users\Admin\.config\opencode\plugin-selftest.mjs` |

Env handed to every child process: `IMAGE_FARM_HOME` · `IMAGE_FARM_PORT` (9424) ·
`IMAGE_FARM_EXTERNAL` (0 = own wiped profile, 1 = an already signed-in BrowserOS session
with no churn) · `IMAGE_FARM_CHROME`.

- **A clean profile per account is mandatory.** That is what makes zemail deliver the
  verification mail directly. In EXTERNAL / BrowserOS mode `wipeProfile` is a no-op, the
  direct mail breaks (`no-verification-page`) - never point the farm at the user's own
  profile or BrowserOS' profile.
- ChatGPT session death => create a fresh account immediately (churn). Never re-login.
- Never broad-taskkill Chrome. Never wipe the user's profile. No cron.
- Plugin tools load at session start; a session started before the install may not list
  them yet.

`scripts/farm_run.py` in this skill drives the **book farm** at `D:\book the end of world`
(the same engine, a different home). Use the plugin for one-off images and the script
for a scene batch that needs the two-hop reference chain.
