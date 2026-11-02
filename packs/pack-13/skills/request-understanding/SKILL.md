---
name: request-understanding
description: Understand the user's actual intent, context, deliverables, language, and constraints before choosing tools or planning execution. Use at the start of every task, especially Arabic requests, ambiguous requests, and tasks referencing prior work.
---

# Request Understanding

Before choosing a skill, agent, repository, tool, or implementation:

1. Read the user's request as intent, not a keyword list.
2. Identify the end state the user wants, the deliverables, quality bar, and what success looks like.
3. Recover relevant project history, durable preferences, corrections, and decisions from Auto Memory and the shared memory/catalog when applicable.
4. Identify constraints: Windows paths, hardware, budget, privacy, licensing, deadlines, and whether any operation is read-only or mutating.
5. If Arabic technical phrasing is involved, formulate a faithful internal English task brief to improve technical retrieval. Do not show a translation unless helpful, and do not change the meaning or response language.
6. Detect hidden dependencies and assumptions. Ask only one essential question when the work genuinely cannot proceed; otherwise state a reasonable assumption and proceed.
7. Write a one- or two-sentence task brief for the capability-scout or execution plan.

Do not start installing or coding before the actual goal and constraints are understood.
