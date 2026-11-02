---
name: subagent-orchestration
description: Use for complex tasks with independent research, implementation, testing, architecture, media, operations or review streams. Coordinates native Claude Code subagents with role-first selection, evidence contracts and independent review.
user-invocable: false
---

# Subagent Orchestration for Claude Code

The main Claude Code agent owns the result. Subagents are bounded specialists who return artifacts and evidence.

## 1. Build the task model

Before spawning, establish:
- Outcome, deliverables and acceptance criteria.
- Domains, complexity, uncertainty and risk.
- Decomposability and independent workstreams.
- Required research, implementation, testing, review, comparison or operations.
- Constraints, dependencies, resource budget and prohibited actions.

Direct/simple tasks need no team.

## 2. Select roles before agents

Choose only the roles required by the task:
- Researcher: sources, repositories, compatibility and requirements.
- Implementer: bounded changes with exclusive file ownership. Use scoped-implementer when multiple workers need disjoint file scopes; use implementation-engineer for broader integration work.
- Debugger: one-hypothesis read-only investigation with confirming/contradicting evidence. Use hypothesis-debugger for competing-root-cause analysis.
- Tester: executable acceptance and regression checks.
- Reviewer/judge: independent inspection against a fixed rubric.
- Security/risk analyst: threat, permissions, secrets and supply chain.
- Domain specialist: only when the task needs that expertise.

Map roles to callable native agents in `C:\Users\Admin\.claude\agents`. Do not use OpenCode/Qoder catalogue names as if they were callable. Create/adapt a specialist only when no existing native agent fits.

## 3. Persist a task contract

For each workstream record:
- Task/plan ID and session context.
- Role and actual agent name.
- Exact scope and owned files.
- Expected output and acceptance criteria.
- Priority: REQUIRED, RECOMMENDED or FALLBACK.
- Invocation method, dependencies and fallback.
- Verification command/check and required evidence.

Do not make generic skills mandatory simply because they ranked highly. A fallback satisfies a requirement only if it was actually invoked and met the same acceptance criteria.

## 4. Parallel execution

- Parallelize independent research and isolated implementations.
- One owner per file set; never run concurrent edits to the same file.
- Sequence shared interfaces, schemas, migrations and global configuration.
- Batch work according to provider reliability and hardware resources.
- Give each agent only the relevant context, memory, constraints and source links.

## 5. Implementation and independent judge

For meaningful implementation:
1. Dispatch bounded tasks and capture exact outputs.
2. Inspect changed files and diffs independently.
3. Run tests and preserve command, exit code, output and artifact path.
4. Select an independent reviewer only after the execution team is fixed.
5. The reviewer must not be an implementation participant or sign off its own work.
6. Resolve critical/important findings before declaring completion.

The independent reviewer returns PASS, PASS WITH CONDITIONS, FAIL or UNVERIFIED against an explicit rubric. Structural separation does not prove cognitive independence.

## 6. Evidence-based completion gate

Before final delivery, check:
- Every REQUIRED capability was actually invoked.
- Every required role returned its expected artifact.
- A skill read proves only that its instructions were loaded, not that the procedure ran.
- An agent listed in a plan is not an executed agent.
- Fallbacks have real invocation evidence.
- Required tests passed and evidence is inspectable.
- Any exception is explicit, justified and does not silently become PASS.

A direct task with no required capabilities has no team or gate debt. The gate is currently a procedural Claude Code workflow, not a hard runtime lock; never claim the harness technically blocked completion.

## 7. Synthesis and handoff

Main agent consolidates artifacts, disagreements, test evidence, incomplete work and residual risks. Update the durable plan ledger and Engraphis session handoff. A subagent self-report alone is not proof.
