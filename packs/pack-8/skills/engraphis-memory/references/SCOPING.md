# Engraphis scoping: workspace → repo → session → memory

Scope is a work-context boundary, not a personal-identity boundary. Use stable names consistently; recall filters match them literally.

## Scope and type are separate

- Scope answers **where the knowledge applies**: session, repo, or workspace.
- Type answers **what kind of knowledge it is**: working, episodic, semantic, or procedural.
- The Smart MCP interface infers scope from workspace, repo, and session arguments. Do not invent a `scope` argument.

## Choose the narrowest reusable boundary

- **Repo-specific**: pass the canonical repo name. Use for code conventions, design decisions, bug causes and fixes.
- **Workspace-wide**: pass workspace and omit repo only when the fact genuinely applies across repositories.
- **Session-specific**: pass the returned session ID for transient task state and handoffs.
- **User scope**: reserved and unsupported for new writes. Do not treat workspace memory as private personal memory.

Use an explicit user/project workspace when provided. Otherwise use the existing project mapping if available; `default` is the fallback. Explicit workspace values win over mappings. Never assume changing a mapping moves existing records.

## Session lifecycle

1. Start multi-step work with `engraphis_session(action="start", workspace, repo, agent, goal)`.
2. Retain and pass the returned `session_id` to recall and remember calls.
3. End with `engraphis_session(action="end", session_id, summary, outcome, open_threads)`.
4. `open_threads` should contain only unresolved work for the next session.

Starting is idempotent for the same workspace/repo/agent/goal. Use `force_new=true` only when deliberately creating a parallel branch of work.

## Retrieval boundaries

Repo recall should see that repo and its workspace ancestors; session recall should see that session and its repo/workspace ancestors. Do not broaden scope just because a query returns no results. Check the resolved workspace/repo and use the correct stable identifiers.

## Promotion

Start narrow. Promote session knowledge to repo, or repo knowledge to workspace, only when evidence shows it generalizes. Use the discovered governed action and its exact schema; do not manually move or duplicate records.
