---
name: implementation-planning
description: Use before non-trivial multi-step work, system changes, migrations, integrations or projects with multiple deliverables. Creates a task model, execution contract, dependencies, acceptance tests and durable progress ledger.
user-invocable: false
---

# Implementation Planning

A plan is an execution instrument, not a reason to stop and repeatedly ask for permission.

## Workflow

1. Understand the outcome, deliverables, prior decisions and constraints.
2. Recall relevant Engraphis memory and inspect the actual project before designing.
3. Run Capability Scout and read complete serious candidate definitions.
4. Establish the baseline: paths, versions, settings, processes, tests and existing implementation.
5. Model complexity, risk, uncertainty, decomposability and required work types.
6. Define observable acceptance criteria for function, quality, compatibility, security, resource use and delivery.
7. Create a task contract for each workstream.
8. Assign exact file ownership, dependencies, outputs, tests and rollback notes.
9. Parallelize independent streams; serialize shared interfaces and global configuration.
10. Continue autonomously for safe reversible decisions. Escalate destructive changes, credential rotation, purchases/quota use, publication or essential unknowable choices.

## Task contract

Every non-trivial task records:
- Stable task ID and Claude Code session context.
- Outcome and acceptance criteria.
- Owner role and actual callable agent.
- Required / recommended / fallback priority.
- Exact source paths and owned output files.
- Dependencies and invocation method.
- Verification command, expected result and evidence location.
- Status: DISCOVERED → SELECTED → INVOKED → COMPLETED → VERIFIED, or BLOCKED.

Do not use a global unscoped “latest task” when several sessions exist. Resolve by explicit task ID or the current session/context.

## Completion gate

Before reporting success:
- Confirm each REQUIRED capability was invoked, not merely selected.
- Confirm every expected output exists and is inspectable.
- Confirm tests actually ran and passed; record command, exit code and relevant output.
- Distinguish loaded skill instructions from executed skill procedure.
- Distinguish planned agents from completed agent invocations.
- Require independent review for complex/high-risk changes when an independent reviewer is available.
- Report unresolved requirements as BLOCKED or UNVERIFIED; never manufacture a PASS.

The gate is procedural, not a hard harness lock. A direct/simple answer with no required capabilities does not need a gate.

## Durable plan and progress

- System plans: `D:\ClaudeCodeSystem\plans\`
- Repository plans: project-local `.claude\plans\` or the existing documented plan directory.
- Maintain task IDs, status, decisions, changed files, test evidence, blockers and next actions.
- Before compaction, update the ledger; the local PreCompact hook creates a supplemental checkpoint.
- After resume, inspect the ledger and current files before repeating work.
- Use the native planning-with-files skill only when its durable files add value; keep one plan owner and avoid competing ledgers.

## Execution rules

- No plan for trivial questions or one-step edits.
- Do not over-decompose tightly coupled work.
- Main Claude agent owns integration and final verification.
- Complete prerequisites and gates before dependent phases.
- A plan is complete only when deliverables and acceptance tests are verified.
