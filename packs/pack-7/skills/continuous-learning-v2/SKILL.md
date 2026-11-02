---
name: continuous-learning-v2
description: Instinct-based learning system that observes sessions via hooks, creates atomic instincts with confidence scoring, and evolves them into skills/commands/agents. v2.1 adds project-scoped instincts to prevent cross-project contamination. Use when capturing lessons from a session, managing instincts, or promoting them into skills, commands, or agents.
metadata:
  version: 2.1.0
  origin: ECC
---

# Continuous Learning v2.1 - Instinct
-Based Architecture

An advanced learning system that turns your Claude Code sessions into reusable knowledge through atomic "instincts" - small learned behaviors with confidence scoring.

**v2.1** adds **project-scoped instincts** — React patterns stay in your React project, Python conventions stay in your Python project, and universal patterns (like "always validate input") are shared globally.

## When to Activate

- Setting up automatic learning from Claude Code sessions
- Configuring instinct-based behavior extraction via hooks
- Tuning confidence thresholds for learned behaviors
- Reviewing, exporting, or importing instinct libraries
- Evolving instincts into full skills, commands, or agents
- Managing project-scoped vs global instincts
- Promoting instincts from project to global scope

## What's New in v2.1

| Feature | v2.0 | v2.1 |
|---------|------|------|
| Storage | Global (`~/.claude/homunculus/`) | Project-scoped (`${XDG_DATA_HOME:-~/.local/share}/ecc-homunculus/projects/<hash>/`) |
| Scope | All instincts apply everywhere | Project-scoped + global |
| Detection | None | git remote URL / repo path |
| Promotion | N/A | Project → global when seen in 2+ projects |
| Commands | 4 (status/evolve/export/import) | 6 (+promote/projects) |
| Cross-project | Contamination risk | Isolated by default |

## What's New in v2 (vs v1)

| Feature | v1 | v2 |
|---------|----|----|
| Observation | Stop hook (session end) | PreToolUse/PostToolUse (100% reliable) |
| Analysis | Main context | Background agent (Haiku) |
| Granularity | Full skills | Atomic "instincts" |
| Confidence | None | 0.3-0.9 weighted |
| Evolution | Direct to skill | Instincts -> cluster -> skill/command/agent |
| Sharing | None | Export/import instincts |

## The Instinct Model

An instinct is a small learned behavior:

```yaml
---
id: prefer-functional-style
trigger: "when writing new functions"
confidence: 0.7
domain: "code-style"
source: "session-observation"
scope: project
project_id: "a1b2c3d4e5f6"
project_name: "my-react-app"
---

# Prefer Functional Style

## Action
Use functional patterns over classes when appropriate.

## Evidence
- Observed 5 instances of functional pattern preference
- User corrected class-based approach to functional on 2025-01-15
```

**Properties:**
- **Atomic** -- one trigger, one action
- **Confidence-weighted** -- 0.3 = tentative, 0.9 = near certain
- **Domain-tagged** -- code-style, testing, git, debugging, workflow, etc.
- **Evidence-backed** -- tracks what observations created it
- **Scope-aware** -- `project` (default) or `global`

## How It Works

```
Session Activity (in a git repo)
      |
      | Hooks capture prompts + tool use (100% reliable)
      | + detect project context (git remote / repo path)
      v
+---------------------------------------------+
|  projects/<project-hash>/observations.jsonl  |
|   (prompts, tool calls, outcomes, project)   |
+---------------------------------------------+
      |
      | Observer agent reads (background, Haiku)
      v
+---------------------------------------------+
|          PATTERN DETECTION                   |
|   * User corrections -> instinct             |
|   * Error resolutions -> instinct            |
|   * Repeated workflows -> instinct           |
|   * Scope decision: project or global?       |
+---------------------------------------------+
      |
      | Creates/updates
      v
+---------------------------------------------+
|  projects/<project-hash>/instincts/personal/ |
|   * prefer-functional.yaml (0.7) [project]   |
|   * use-react-hooks.yaml (0.9) [project]     |
+---------------------------------------------+
|  instincts/personal/  (GLOBAL)               |
|   * always-validate-input.yaml (0.85) [global]|
|   * grep-before-edit.yaml (0.6) [global]     |
+---------------------------------------------+
      |
      | /evolve clusters + /promote
      v
+---------------------------------------------+
|  projects/<hash>/evolved/ (project-scoped)   |
|  evolved/ (global)                           |
|   * commands/new-feature.md                  |
|   * skills/testing-workflow.md               |
|   * agents/refactor-specialist.md            |
+---------------------------------------------+
```

## Project Detection

The system automatically detects your current project:

1. **`CLAUDE_PROJECT_DIR` env var** (highest priority) -- honored as an explicit override even when the directory is not a git repo (hashed by its absolute path)
2. **`git remote get-url origin`** -- hashed to create a portable project ID (same repo on different machines gets the same ID)
3. **`git rev-parse --show-toplevel`** -- fallback using repo path (machine-specific)
4. **Global fallback** -- if no project is detected, instincts go to global scope

Each project gets a 12-character hash ID (e.g., `a1b2c3d4e5f6`). A registry file at `${XDG_DATA_HOME:-~/.local/share}/ecc-homunculus/projects.json` maps IDs to human-readable names.

### Data Directory

Continuous-learning-v2 stores observer data outside `~/.claude` so Claude Code's sensitive-path guard does not block background instinct writes:

1. `CLV2_HOMUNCULUS_DIR` when set to an absolute path
2. `$XDG_DATA_HOME/ecc-homunculus`
3. `$HOME/.local/share/ecc-homunculus`

Existing users with data at `~/.claude/homunculus` can migrate once:

```bash
bash skills/continuous-learning-v2/scripts/migrate-homunculus.sh
```

## Quick Start

### 1. Enable Observation Hooks

**If installed as a plugin** (recommended):

No extra `settings.json` hook block is required. Claude Code v2.1+ auto-loads the plugin `hooks/hooks.json`, and `observe.sh` is already registered there.

If you previously copied `observe.sh` into `~/.claude/settings.json`, remove that duplicate `PreToolUse` / `PostToolUse` block. Duplicating the plugin hook causes double execution and `${CLAUDE_PLUGIN_ROOT}` resolution errors because that variable is only available inside plugin-managed `hooks/hooks.json` entries.

**If installed manually** to `~/.claude/skills`, add this to your `~/.claude/settings.json`:

```json
{
  "hooks": {
    "PreToolUse": [{
      "matcher": "*",
      "hooks": [{
        "type": "command",
        "command": "~/.claude/skills/continuous-learning-v2/hooks/observe.sh"
      }]
    }],
    "PostToolUse": [{
      "matcher": "*",
      "hooks": [{
        "type": "command",
        "command": "~/.claude/skills/continuous-learning-v2/hooks/observe.sh"
      }]
    }]
  }
}
```

### 2. Initialize Directory Structure

The system creates directories automatically on first use, but you can also create them manually:

```bash
# Global directories
mkdir -p "${XDG_DATA_HOME:-$HOME/.local/share}/ecc-homunculus"/{instincts/{personal,inherited},evolved/{agents,skills,commands},projects}

# Project directories are auto-created when the hook first runs in a git repo
```

### 3. Use the Instinct Commands

```bash
/instinct-status     # Show learned instincts (project + global)
/evolve              # Cluster related instincts into skills/commands
/instinct-export     # Export instincts to file
/instinct-import     # Import instincts from others
/promote             # Promote project instincts to global scope
/projects            # List all known projects and their instinct counts
```

## Commands

| Command | Description |
|---------|-------------|
| `/instinct-status` | Show all instincts (project-scoped + global) with confidence |
| `/evolve` | Cluster related instincts into skills/commands, suggest promotions |
| `/instinct-export` | Export instincts (filterable by scope/domain) |
| `/instinct-import <file>` | Import instincts with scope control |
| `/promote [id]` | Promote project instincts to global scope |
| `/projects` | List all known projects and their instinct counts |

## Configuration

Edit `config.json` to control the background observer:

```json
{
  "version": "2.1",
  "observer": {
    "enabled": false,
    "run_interval_minutes": 5,
    "min_observations_to_analyze": 20
  }
}
```

| Key | Default | Description |
|-----|---------|-------------|
| `observer.enabled` | `false` | Enable the background observer agent |
| `observer.run_interval_minutes` | `5` | How often the observer analyzes observations |
| `observer.min_observations_to_analyze` | `20` | Minimum observations before analysis runs |

Other behavior (observation capture, instinct thresholds, project scoping, promotion criteria) is configured via code defaults in `instinct-cli.py` and `observe.sh`.

### Observer platform support

The background observer requires WSL2, Linux, or macOS. On native Windows
(Git Bash / MSYS2) it starts and reports success, but the process is killed
when the spawning hook exits and its Job Object closes, so no analysis ever
runs — setting `observer.enabled: true` there is effectively a no-op
(see issue #2489).

`observe.sh` detects this on the following hook invocation and writes an
explanatory warning to `observer-start.log` once the observer has failed to
survive several times in a row.

| Env var | Default | Description |
|---------|---------|-------------|
| `ECC_OBSERVER_NOSURVIVE_WARN_AFTER` | `3` | Consecutive non-survivals before the warning is logged |

## File Structure

```
${XDG_DATA_HOME:-~/.local/share}/ecc-homunculus/
+-- identity.json           # Your profile, technical level
+-- projects.json           # Registry: project hash -> name/path/remote
+-- observations.jsonl      # Global observations (fallback)
+-- instincts/
|   +-- personal/           # Global auto-learned instincts
|   +-- inherited/          # Global imported instincts
+-- evolved/
|   +-- agents/             # Global generated agents
|   +-- skills/             # Global generated skills
|   +-- commands/           # Global generated commands
+-- projects/
    +-- a1b2c3d4e5f6/       # Project hash (from git remote URL)
    |   +-- project.json    # Per-project metadata mirror (id/name/root/remote)
    |   +-- observations.jsonl
    |   +-- observations.archive/
    |   +-- instincts/
    |   |   +-- personal/   # Project-specific auto-learned
    |   |   +-- inherited/  # Project-specific imported
    |   +-- evolved/
    |       +-- skills/
    |       +-- commands/
    |       +-- agents/
    +-- f6e5d4c3b2a1/       # Another project
        +-- ...
```

## Scope Decision Guide

| Pattern Type | Scope | Examples |
|-------------|-------|---------|
| Language/framework conventions | **project** | "Use React hooks", "Follow Django REST patterns" |
| File structure preferences | **project** | "Tests in `__tests__`/", "Components in src/components/" |
| Code style | **project** | "Use functional style", "Prefer dataclasses" |
| Error handling strategies | **project** | "Use Result type for errors" |
| Security practices | **global** | "Validate user input", "Sanitize SQL" |
| General best practices | **global** | "Write tests first", "Always handle errors" |
| Tool workflow preferences | **global** | "Grep before Edit", "Read before Write" |
| Git practices | **global** | "Conventional commits", "Small focused commits" |

## Instinct Promotion (Project -> Global)

When the same instinct appears in multiple projects with high confidence, it's a candidate for promotion to global scope.

**Auto-promotion criteria:**
- Same instinct ID in 2+ projects
- Average confidence >= 0.8

**How to promote:**

```bash
# Promote a specific instinct
python3 instinct-cli.py promote prefer-explicit-errors

# Auto-promote all qualifying instincts
python3 instinct-cli.py promote

# Preview without changes
python3 instinct-cli.py promote --dry-run
```

The `/evolve` command also suggests promotion candidates.

## Confidence Scoring

Confidence evolves over time:

| Score | Meaning | Behavior |
|-------|---------|----------|
| 0.3 | Tentative | Suggested but not enforced |
| 0.5 | Moderate | Applied when relevant |
| 0.7 | Strong | Auto-approved for application |
| 0.9 | Near-certain | Core behavior |

**Confidence increases** when:
- Pattern is repeatedly observed
- User doesn't correct the suggested behavior
- Similar instincts from other sources agree

**Confidence decreases** when:
- User explicitly corrects the behavior
- Pattern isn't observed for extended periods
- Contradicting evidence appears

## Why Hooks vs Skills for Observation?

> "v1 relied on skills to observe. Skills are probabilistic -- they fire ~50-80% of the time based on Claude's judgment."

Hooks fire **100% of the time**, deterministically. This means:
- Every tool call is observed
- No patterns are missed
- Learning is comprehensive

## Backward Compatibility

v2.1 is fully compatible with v2.0 and v1:
- Existing global instincts can be migrated from `~/.claude/homunculus/instincts/` with `scripts/migrate-homunculus.sh`
- Existing `~/.claude/skills/learned/` skills from v1 still work
- Stop hook still runs (but now also feeds into v2)
- Gradual migration: run both in parallel

## Privacy

- Observations stay **local** on your machine
- Project-scoped instincts are isolated per project
- Only **instincts** (patterns) can be exported — not raw observations
- No actual code or conversation content is shared
- You control what gets exported and promoted

## Related

- [ECC-Tools GitHub App](https://github.com/apps/ecc-tools) - Generate instincts from repo history
- Homunculus - Community project that inspired the v2 instinct-based architecture (atomic observations, confidence scoring, instinct evolution pipeline)
- [The Longform Guide](https://x.com/affaanmustafa/status/2014040193557471352) - Continuous learning section

## New Instincts from Leaked Prompt Analysis (2026-10-30)

The following instincts were extracted from analyzing system prompts of leading AI agents (Claude Code, Cursor, ZCode/GLM-5.3, Perplexity Model Council, Meta Muse). These represent cross-agent patterns that improve orchestration quality.

### Instinct: plan-before-execute
```yaml
---
id: plan-before-execute
trigger: "task complexity >= medium OR type in [architecture, code, debug, research, idea, compare]"
confidence: 0.9
domain: "workflow"
scope: "global"
source: "leaked-prompt-analysis"
source_agents: ["ZCode/GLM-5.3", "Claude Code"]
---

# Plan Before Execute

## Signal
Task requires multi-step execution (estimated >3 turns) or involves architectural decisions.

## Action
Invoke `plan-mode-gate` skill to generate structured plan with user approval gate before any capability execution.

## Evidence
- ZCode/GLM-5.3: Explicit `EnterPlanMode`/`ExitPlanMode` tools with user approval requirement
- Claude Code: Automatic context compaction and planning for complex tasks
- Prevents premature execution and rework
```

### Instinct: delegate-brief-only
```yaml
---
id: delegate-brief-only
trigger: "delegating to subagent"
confidence: 0.95
domain: "orchestration"
scope: "global"
source: "leaked-prompt-analysis"
source_agents: ["ZCode/GLM-5.3"]
---

# Delegate Brief Only

## Signal
Spawning a subagent for a research, exploration, or analysis task.

## Action
Provide ONLY: task description + desired outcome + non-obvious constraints. No implementation details, no tool suggestions, no step-by-step instructions.

## Evidence
- ZCode: "Once you've delegated a search, don't also run it yourself — wait for the result"
- ZCode: "Delegate with: task + outcome + non-obvious constraints only — nothing more"
- Prevents double-work and preserves subagent autonomy
```

### Instinct: lead-with-outcome
```yaml
---
id: lead-with-outcome
trigger: "responding to user after task completion"
confidence: 0.9
domain: "communication"
scope: "global"
source: "leaked-prompt-analysis"
source_agents: ["ZCode/GLM-5.3"]
---

# Lead With Outcome

## Signal
Completing a task and preparing final response.

## Action
First sentence must answer "what happened" (the outcome/result). Then provide evidence/details.

## Evidence
- ZCode: "Lead with the outcome — first sentence answers 'what happened'"
- Improves user experience by delivering value immediately
- Contrasts with process-first responses
```

### Instinct: parallel-batch-independent
```yaml
---
id: parallel-batch-independent
trigger: "multiple independent capabilities selected in route.mjs decision"
confidence: 0.85
domain: "performance"
scope: "global"
source: "leaked-prompt-analysis"
source_agents: ["Claude Code"]
---

# Parallel Batch Independent Capabilities

## Signal
Route.mjs selects multiple capabilities with no data dependencies (different reads/writes, no explicit ordering).

## Action
Group into parallel batches via `analyzeDependencies()` → execute with `Promise.all` → aggregate results.

## Evidence
- Claude Code: "Independent tool calls can run in parallel in one response"
- Reduces turn count by 30-60% for multi-capability tasks
- Implemented in route.mjs via `parallel_groups` and `parallelizable` fields
```

### Instinct: validate-tool-schema-first
```yaml
---
id: validate-tool-schema-first
trigger: "MCP tool about to be called"
confidence: 0.9
domain: "reliability"
scope: "global"
source: "leaked-prompt-analysis"
source_agents: ["Cursor"]
---

# Validate Tool Schema First

## Signal
Any MCP tool invocation (engraphis, firecrawl, browser, rea, etc.)

## Action
Fetch tool schema via `discover_actions` → validate args against JSON Schema → fail fast with actionable error if invalid.

## Evidence
- Cursor: `ToolSearch` — batch-load deferred MCP tools; check schemas BEFORE calling
- Prevents runtime errors from malformed tool calls
- Schema cache at `magicscan/schema-cache.json`
```

### Instinct: memory-first-recall
```yaml
---
id: memory-first-recall
trigger: "session start OR non-trivial task begins"
confidence: 0.9
domain: "context"
scope: "global"
source: "leaked-prompt-analysis"
source_agents: ["Meta Muse"]
---

# Memory First Recall

## Signal
New session or task requiring context from previous work.

## Action
1. Read `~/MEMORY.md` (curated) + Engraphis recall_context (raw)
2. Synthesize briefing: decisions, patterns, preferences, facts
3. Inject into context before planning

## Evidence
- Meta Muse: `~/MEMORY.md` as curated long-term memory; search before acting
- Dual-layer: Engraphis (queryable, provenance) + MEMORY.md (human-readable, portable)
- Prevents re-deciding and re-learning
```

### Instinct: council-synthesis-after-team
```yaml
---
id: council-synthesis-after-team
trigger: "team execution complete (council or arena pattern)"
confidence: 0.85
domain: "decision-making"
scope: "global"
source: "leaked-prompt-analysis"
source_agents: ["Perplexity Model Council"]
---

# Council Synthesis After Team Execution

## Signal
Multi-agent team (council/arena) has completed individual executions.

## Action
Run synthesis phase: collect all outputs → group by agreement/disagreement → structured resolution → final verdict with reasoning trace.

## Evidence
- Perplexity Model Council: 4-phase: decide → dispatch parallel → synthesize (agreement/disagreement) → deliver
- Prevents "last agent wins" or simple majority voting
- Implemented in route.mjs via `council_synthesis` output field
```

### Instinct: compact-context-proactively
```yaml
---
id: compact-context-proactively
trigger: "context window >70% full"
confidence: 0.8
domain: "context-management"
scope: "global"
source: "leaked-prompt-analysis"
source_agents: ["Claude Code"]
---

# Compact Context Proactively

## Signal
Conversation context approaching token limit (>70% window).

## Action
Summarize older messages to: decision + action + result (no dialogue). Retain: last 10 messages, gate decisions, plan-contracts.

## Evidence
- Claude Code: Automatic context compaction with summarization
- Preserves decision trail while freeing tokens
- Complements `@tarquinen/opencode-dcp` plugin
```

---

*Instinct-based learning: teaching Claude your patterns, one project at a time.*
