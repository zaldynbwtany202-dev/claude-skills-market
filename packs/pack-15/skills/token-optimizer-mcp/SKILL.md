---
name: token-optimizer-mcp
description: Use the local Token Optimizer MCP tools for token/context audits, measured context optimization, project knowledge-graph retrieval and durable findings, cache analysis, and optimizer diagnostics. Use when a coding task has repeated reads, large tool output, tight context, or a non-obvious project conclusion worth retaining.
---

# Token Optimizer MCP

Use the locally registered `token-optimizer` MCP server when its tools add value. The server exposes a bounded core profile of 19 tools, verified through the MCP protocol.

## Tool selection

- **Before revisiting project knowledge:** use `wiki_read` with absolute file anchors before re-deriving an existing conclusion. Use `wiki_query` for graph overview, search, a keyed finding, or graph audit.
- **After a real discovery:** use `wiki_write` only for durable, non-obvious project conclusions: a verified command, a design decision and rejected alternatives, a failure and its cause, or a subsystem map. Include file anchors, concrete evidence, and when the finding applies. Leave scope at `project` unless a broader scope is explicitly justified.
- **Context and tool-output audits:** use `token_audit`, `waste_audit`, `cache_audit`, and `get_optimization_report` to inspect context efficiency. Use `optimize_text` for a bounded text payload and `optimize_session` only when an optimization report or the current context indicates a need.
- **Code and file access:** the server provides `smart_read`, `smart_write`, `smart_edit`, `smart_glob`, and `smart_grep`. These overlap with Claude Code's native tools; prefer native tools for ordinary small operations and use these only when their context/cache behavior is useful.
- **Diagnostics:** use `install_doctor`, `fleet_audit`, and `model_routing` for read-only diagnostics. Do not turn on proxy routing, auto-repair, shell hooks, or client installation as a side effect of a diagnostic.

## Memory boundaries

There are two deliberately distinct stores:

1. **Claude shared memory** — `claude-system-local` backed by `D:\ClaudeCodeSystem\memory\shared\records.jsonl`. Use it for cross-project user preferences, system architecture decisions, global environment constraints, and facts that should follow the user across unrelated projects. This remains the authoritative shared memory and uses the existing `UserPromptSubmit`, `PreCompact`, and `SessionStart` hooks.
2. **Token Optimizer project knowledge graph** — use it for file-anchored findings that belong to a specific repository/project. The per-project stores and shared graph are routed to D through the MCP environment.

Do not duplicate general user preferences or system-level memory into every project graph. Do not claim that this MCP replaces the existing shared memory or its hooks. Do not store API keys, passwords, private tokens, personal secrets, or raw sensitive file contents.

## Required write discipline

For `wiki_write`, always provide:
- one clear actionable `claim`;
- one or more absolute file `anchors` inside the target project;
- concrete `evidence` from a test, command result, source inspection, or explicit decision;
- specific `applicability`;
- a correct `type` and `confidenceLabel`.

Prefer `verified` only when the claim was directly tested. Never write an unverified hypothesis as a fact. Let the tool infer the project from the first anchor unless an explicit project root is necessary.

## Safety and integration rules

- This server is a local stdio MCP process registered in Claude Code user scope.
- The active profile is `core`; do not expand to the 100+ tool profile without a concrete capability need.
- Telemetry, beacon upload, update check, and install repair are disabled in the MCP environment.
- Never run `token-optimizer-install`, `token-optimizer-install-client`, or `TOKEN_OPTIMIZER_AUTO_INSTALL=1` in this environment. Those paths can add hooks or alter client configuration.
- Do not modify `C:\Users\Admin\.claude\settings.json` hooks. Existing shared-memory hooks must remain intact.
- Keep all optimizer home, shared graph, unrooted graph, SQLite, state, logs, and cache paths on D.
- The server was installed with lifecycle scripts disabled and the Windows N-API SQLite binary was verified independently. The dependency lock includes local security overrides for `minimatch` and `qs`; do not remove those overrides without a fresh audit.
