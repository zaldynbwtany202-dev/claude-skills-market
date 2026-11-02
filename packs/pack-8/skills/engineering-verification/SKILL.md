---
name: engineering-verification
description: Verify implementations and integrations with repeatable tests, logs, and acceptance criteria. Use before declaring a task or capability complete.
---

# Engineering Verification

1. Turn the user's goal into explicit acceptance criteria before implementation.
2. Identify the right verification level: static inspection, syntax validation, unit tests, integration tests, end-to-end test, or real session invocation.
3. Capture baseline state and identify the files changed.
4. Run the smallest meaningful test first, then relevant regression tests.
5. For MCP, confirm server discovery, tool listing, session visibility, and a real safe invocation.
6. For skills and agents, confirm Claude Code discovers them and can invoke them; a file on disk is not sufficient.
7. For memory, verify recall across independent sessions.
8. For media outputs, inspect the actual rendered artifact and validate dimensions, duration, codec, consistency, and quality.
9. Record exact command, exit code, relevant output, environment, and limitations.
10. Classify each result as DISCOVERED, REVIEWED, INTEGRATED, SESSION_VISIBLE, INVOCATION_PASSED, or ACCEPTED.

Never claim success based only on installation, config presence, README assertions, or an unverified model response.
