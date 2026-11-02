---
id: memory-first
name: Memory-First Protocol
version: "1.0.0"
description: |
  Meta Muse pattern: searches ~/MEMORY.md + Engraphis before planning.
  On task complete: writes outcome to MEMORY.md (curated) + Engraphis (raw).
  Format: YAML frontmatter + dated entries.
author: THEMAGICSCAN
tags:
  - memory
  - context
  - recall
  - knowledge-management
trigger:
  - session start
  - "recall memory"
  - "what did we do"
  - "remember this"
  - "memory first"
  - "الذاكرة أولاً"
capabilities:
  - memory_recall
  - memory_write
  - memory_curated_file
  - session_bootstrap
dependencies:
  - engraphis (MCP)
hooks:
  - session_start: "bootstrap_memory"
  - pre_task: "recall_relevant_memory"
  - post_task: "persist_task_outcome"
---

# Memory-First Protocol Skill

## Purpose
Implements Meta Muse's memory-first discipline: **always search memory before acting**, and **always persist outcomes after completing**. Uses dual-layer memory: Engraphis (raw, queryable, provenance-tracked) + `~/MEMORY.md` (curated, human-readable, portable).

## When to Trigger
- **Automatic**: Session start (via `session_start` hook)
- **Automatic**: Before any non-trivial task (via `pre_task` hook)
- **Automatic**: After task completion (via `post_task` hook)
- Manual: User asks "what did we do about X?" or "remember this"

## Dual-Layer Memory Architecture

### Layer 1: Engraphis (Raw, Queryable)
- **Scope**: workspace-scoped, agent-scoped, repo-scoped
- **Types**: semantic, episodic, procedural, instinct
- **Provenance**: automatic (agent, timestamp, session, trigger)
- **Query**: `engraphis_recall_context` with filters
- **Write**: `engraphis_remember` with structured fields

### Layer 2: MEMORY.md (Curated, Human-Readable)
- **Location**: `C:\Users\Admin\.engraphis\MEMORY.md` (or `~/MEMORY.md`)
- **Format**: YAML frontmatter + markdown sections
- **Sections**: decisions, patterns, preferences, facts, project_state
- **Updated**: manually curated after significant work
- **Portable**: can be copied across machines/projects

## Workflow

### 1. Session Bootstrap (session_start hook)
```
1. Read MEMORY.md → parse frontmatter + sections
2. Engraphis recall_context(query="recent", limit=20)
3. Synthesize into session briefing:
   - Active decisions (from decisions section)
   - Relevant patterns (from patterns section)
   - Current project state (from project_state)
   - User preferences (from preferences)
4. Inject briefing into system context
```

### 2. Pre-Task Recall (pre_task hook)
```
Input: task description + context
Process:
  1. Extract keywords/entities from task
  2. Query Engraphis: recall_context(keywords, workspace, limit=10)
  3. Search MEMORY.md sections (grep for keywords)
  4. Rank results by recency + relevance
  5. Return: memory_brief (top 3-5 relevant entries)
  
Output injected into task context as `memory_brief`
```

### 3. Post-Task Persist (post_task hook)
```
Input: task outcome + evidence + metadata
Process:
  1. Write raw to Engraphis:
     engraphis_remember(
       workspace="default",
       mtype="episodic",
       subject_key="task.{task_id}.outcome",
       content={summary, evidence, decisions, artifacts}
     )
  2. If significant (new pattern, decision, preference):
     - Extract curated entry
     - Append to appropriate MEMORY.md section
     - Update frontmatter `last_updated`
  3. Log to decisions.jsonl with memory_persisted: true
```

## MEMORY.md Format
```yaml
---
version: "1.0"
last_updated: "2026-10-30T02:30:00Z"
workspace: "default"
project: "VIDEOMAKERGEN"
tags: [opencode, magicscan, video-generation]
---

# MEMORY.md — Curated Knowledge Base

## Decisions
### 2026-10-27 | Route.mjs Fix | Questions no longer trigger mandatory capabilities
- **Decision**: Guards demote to 'recommended' for direct/question patterns
- **Context**: Fixed over-triggering on simple questions
- **Impact**: Reduced unnecessary capability scans
- **Ref**: decisions.jsonl line 142

## Patterns
### Parallel Tool Batching (from ZCode/Claude Code)
- **Pattern**: Group independent calls → Promise.all
- **Applies to**: route.mjs capability dispatch
- **Confidence**: high

### Plan Mode Gate (from ZCode/GLM-5.3)
- **Pattern**: Explicit plan + user approval before execution
- **Applies to**: Complex tasks (>3 turns, architecture type)
- **Confidence**: high

## Preferences
- Language: Arabic (primary), English (technical)
- Plan mode: auto-enabled for medium+ complexity
- Delegation style: brief (task + outcome + constraints only)
- Output style: lead with outcome first sentence

## Facts
- OpenCode config: C:\Users\Admin\.config\opencode\
- Workspace: C:\Users\Admin\Videos\VIDEOMAKERGEN
- Engraphis session: ses_01M653PK1X7SS66FMCKYFD3F0B
- THEMAGICSCAN capabilities: 1947 total (skills=1623, agents=203, commands=107, plugins=10, mcp=4)

## Project State: VIDEOMAKERGEN
- Phase: Initial setup / pattern extraction
- Active skills: plan-mode-gate, tool-schema-validator, memory-first, parallel-batch-executor
- Next: Implement route.mjs council synthesis, update AGENTS.md
```

## Integration Points
- `route.mjs`: call `bootstrapMemory()` at session start, `recallMemory()` before decision
- `engraphis`: primary read/write via MCP tools
- `continuous-learning-v2`: instincts reference MEMORY.md patterns
- `themagicscan-decision`: includes memory_brief in decision context

## Configuration
```yaml
memory_first:
  memory_file: "C:\\Users\\Admin\\.engraphis\\MEMORY.md"
  engraphis_workspace: "default"
  recall_limit: 10
  curation_threshold: "significant"  # only curate decisions/patterns/prefs
  auto_curate: true
  briefing_injection: true
```

## Proof of Completion
- MEMORY.md exists and is updated after each significant task
- Every session starts with memory briefing injected
- Every non-trivial task has `memory_brief` in context
- Engraphis entries have provenance (agent, session, timestamp)
- `decisions.jsonl` entries include `memory_persisted: true`
- Zero "I don't remember" moments for previously decided items