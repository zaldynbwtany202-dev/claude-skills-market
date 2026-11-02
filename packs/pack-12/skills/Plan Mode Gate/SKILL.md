---
id: plan-mode-gate
name: Plan Mode Gate
version: "1.0.0"
description: |
  Enforces ZCode-style plan mode: generates plan, presents for user approval,
  blocks execution until explicit "approved". Integrates with OpenCode
  review pane for plan display.
author: THEMAGICSCAN
tags:
  - planning
  - gate
  - user-approval
  - workflow
trigger:
  - "plan mode"
  - "planning mode"
  - "enter plan mode"
  - "exit plan mode"
  - "requires approval"
  - "معاينة الخطة"
  - "نمط التخطيط"
capabilities:
  - plan_generation
  - user_approval_gate
  - plan_display
  - plan_storage
dependencies: []
hooks:
  - preflight: "check_plan_mode_state"
  - post_task: "update_plan_mode_state"
---

# Plan Mode Gate Skill

## Purpose
Implements the ZCode (GLM-5.3) pattern of explicit planning phase with user approval gate before execution. Prevents premature execution of complex tasks.

## When to Trigger
- Task complexity ≥ medium (estimated >3 turns)
- Task type = architecture, migration, refactor, new feature
- User explicitly requests "plan mode" or "planning mode"
- `themagicscan-decision` recommends plan mode in its output

## Workflow

### 1. Plan Generation (on trigger)
```
Input: task description + context
Output: structured plan with:
  - objective (one sentence)
  - steps (ordered, each with: action, tool/capability, expected outcome)
  - risks/unknowns
  - estimated turns
  - approval_criteria (what "done" looks like)
```

### 2. Plan Display
- Render in OpenCode review pane (markdown with checkboxes)
- Show: objective, steps, risks, estimate
- Provide: "Approve", "Modify", "Cancel" actions

### 3. Approval Gate
- Block ALL execution until user clicks "Approve" or types "approved"/"proceed"
- Store plan in session context (`plan_contract`)
- On approval: transition to execution phase
- On modify: return to step 1 with user feedback
- On cancel: end task, log decision

### 4. Execution Phase
- Execute steps sequentially (or parallel where independent)
- Update checkboxes in review pane in real-time
- If deviation needed: pause, show diff, request re-approval

## Integration Points
- `route.mjs`: call `planModeCheck()` before capability dispatch
- `AGENTS.md`: plan mode rules section (see AGENTS.md edits)
- `commands/plan-mode.md`: CLI toggle for plan mode state
- `continuous-learning-v2`: instinct for "task needs planning"

## Configuration
```yaml
plan_mode:
  auto_enable_threshold:
    complexity: "medium"
    estimated_turns: 3
    types: ["architecture", "migration", "refactor", "new_feature"]
  display: "review-pane"
  require_explicit: true
  storage: "session_context"
```

## Example Plan Output
```markdown
## Plan: Refactor Authentication Module

**Objective**: Replace legacy auth with JWT-based system (est. 8 turns)

### Steps
- [ ] 1. Audit current auth flows (codebase-inspection)
- [ ] 2. Design JWT schema + token rotation (architecture-decision-records)
- [ ] 3. Implement token service (backend-patterns)
- [ ] 4. Update middleware + guards (security-review)
- [ ] 5. Migrate existing sessions (database-migrations)
- [ ] 6. E2E test + verification (verification-loop)

### Risks
- Session migration may break active users
- Token refresh edge cases

### Approval Criteria
- All tests pass
- No regression in auth flows
- Documentation updated
```

## Proof of Completion
- Plan file created in `.opencode/plans/{task-id}.md`
- User approval logged in `decisions.jsonl` with `gate: "plan_approved"`
- Execution only proceeds after approval
- Review pane shows live progress