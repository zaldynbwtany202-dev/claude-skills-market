---
name: capability-scout
description: Discover and evaluate relevant capabilities from Claude Code, ZCode, OpenCode, Qoder, THEMAGICSCAN, Engraphis and the GitHub inventory. Classify intent, inspect full source definitions, verify compatibility, and recommend a dynamic task-specific capability set.
---

# Capability Scout

Follow the companion subagent `capability-scout` and the global rules in `~/.claude/CLAUDE.md`.

## Task model before searching

Classify the request as direct, research, build, debug, compare, security, media, operations, or review. Extract:
- Required outcome and deliverables.
- Domain(s), complexity, uncertainty and risk.
- Whether work is decomposable into independent streams.
- Which functions are needed: research, implementation, testing, review, alternatives or operations.
- Hard constraints: platform, hardware, budget, permissions and prohibited changes.

Do not trigger a team for a simple direct answer.

## Sources

- Unified capability metadata: `D:\ClaudeCodeSystem\catalog\capabilities-index.json`
- Master inventory: `D:\ClaudeCodeSystem\catalog\CAPABILITY_MASTER.md`
- GitHub URL archive: `D:\ZCodeSessionsAnalysis\Full_Transcripts_20261101\all_github_urls_deduplicated.md`
- OpenCode canonical THEMAGICSCAN: `C:\Users\Admin\.config\opencode\magicscan`
- Qoder THEMAGICSCAN: frozen legacy evidence only; do not extend it.
- Engraphis: use the connected `engraphis` MCP server for durable scoped memory.

## Decision rules

1. Search by task intent and capability domain, not only exact words.
2. Indexes and scripts retrieve candidates; they never make the final selection.
3. Read complete serious candidate definitions and relevant supporting files.
4. Choose roles before names: researcher, implementer, tester, reviewer/judge, security analyst, media specialist, or operator.
5. Map each role to an actually callable Claude Code subagent. Never select a catalogue-only or namespaced OpenCode agent as if Claude Code could invoke it.
6. Choose 0..N useful capabilities. There is no fixed cap, but do not inflate the set.
7. Mark each candidate DIRECT, CONVERT, ADAPTER, REBUILD, KNOWLEDGE_ONLY, or SKIP.
8. Check runtime availability, tools, MCP connection, license, dependencies, credentials, Windows support and hardware cost.
9. Separate REQUIRED, RECOMMENDED and FALLBACK. A generic skill must not become mandatory merely because it ranked highly.
10. Preserve complementary capabilities; reject exact or functional duplicates unless one is demonstrably stronger.

## THEMAGICSCAN-derived reasoning

Use the OpenCode canonical implementation as a source of design patterns:
- Intent and task-model classification before keyword ranking.
- Role-first team selection and explicit rejected alternatives.
- Independent judge selection after the execution team is fixed.
- A per-task contract with expected outputs, invocation method, fallback and verification criteria.
- Evidence-based completion; a planned skill or read SKILL.md is not proof of execution.

Do not copy OpenCode plugin hooks, SQLite telemetry or route code directly. Adapt them to Claude Code native Skills, Agents, Hooks and MCP. Qoder's THEMAGICSCAN directory is frozen.

## Output

Intent and task model; selected capabilities with exact source paths and compatibility; team roles and execution order; required/recommended/fallback contracts; excluded candidates and reasons; dependencies; evidence gaps and confidence.

You are read-only. Do not install, modify, enable, delete or reconfigure anything.
