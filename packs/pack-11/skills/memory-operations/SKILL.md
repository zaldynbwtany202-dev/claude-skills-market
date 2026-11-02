---
name: memory-operations
description: Operate the lightweight Claude Code local JSONL fallback memory only when Engraphis is unavailable or when reading/writing Claude Code system bootstrap facts. Engraphis is the primary durable project and repository memory.
user-invocable: false
---

# Memory Operations — Local Fallback

## Memory hierarchy

1. Engraphis is the primary durable memory for project/repository facts, decisions, procedures and multi-session handoffs.
2. Claude Code Auto Memory holds project-local working knowledge.
3. This local JSONL store is a small bootstrap/fallback store for Claude Code system architecture, shared configuration and Engraphis outage recovery. Do not duplicate every Engraphis record here.

## Engraphis first

The user-scope MCP server is `engraphis`. Claude Code may defer its tools until they are searched.

Before attempting an Engraphis operation:
1. Call the built-in `ToolSearch` with `query="engraphis"` and `max_results=20`.
2. Use the exact fully qualified tool references returned, such as:
   - `mcp__engraphis__engraphis_recall_context`
   - `mcp__engraphis__engraphis_remember`
   - `mcp__engraphis__engraphis_session`
   - `mcp__engraphis__engraphis_get_memory`
3. Never guess shortened names such as `mcp__engraphis__recall_context`.
4. If the tool is not returned, search for the exact suffix (for example `engraphis_recall_context`) or inspect `claude mcp list` outside the model. Do not claim recall occurred.

## Local fallback commands

Database: `D:\ClaudeCodeSystem\memory\shared\records.jsonl`

- Search: `node D:\ClaudeCodeSystem\tools\memory-cli.mjs search "<query>" --limit 12`
- Read: `node D:\ClaudeCodeSystem\tools\memory-cli.mjs get <record-id>`
- Add/update: `node D:\ClaudeCodeSystem\tools\memory-cli.mjs add --title "<title>" --type "<type>" --content "<fact>" --source "<origin/date>" --confidence high --tags "tag1,tag2"`
- List: `node D:\ClaudeCodeSystem\tools\memory-cli.mjs list --type "<type>"`
- Stats: `node D:\ClaudeCodeSystem\tools\memory-cli.mjs stats`

Use this fallback only when Engraphis is unavailable or the record specifically concerns Claude Code system bootstrap state.

## Safety

- Never store tokens, API keys, passwords, private identifiers, or other secrets.
- Do not store full conversations or temporary chatter.
- Use stable titles/types and preserve source/date/confidence/evidence.
- Read before updating; do not hard-delete or reset the store as cleanup.
- The local self-test is not proof of automatic retrieval in a fresh Claude Code session.
