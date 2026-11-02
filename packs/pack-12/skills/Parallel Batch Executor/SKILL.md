---
id: parallel-batch-executor
name: Parallel Batch Executor
version: "1.0.0"
description: |
  Claude Code pattern: groups independent tool calls, executes in single
  Promise.all batch. Returns combined results. Reduces turn count.
author: THEMAGICSCAN
tags:
  - parallel
  - batch
  - performance
  - orchestration
trigger:
  - "parallel"
  - "batch"
  - "simultaneous"
  - independent sub-tasks detected
  - "تنفيذ متوازي"
capabilities:
  - dependency_analysis
  - batch_grouping
  - parallel_execution
  - result_aggregation
dependencies: []
hooks:
  - pre_decision: "analyze_parallelizability"
  - post_decision: "execute_parallel_batches"
---

# Parallel Batch Executor Skill

## Purpose
Implements Claude Code's explicit parallel tool calling pattern: when multiple independent capabilities are selected, group them into batches and execute concurrently via `Promise.all` instead of sequentially. Reduces turn count and latency.

## When to Trigger
- **Automatic**: `themagicscan-decision` output includes `parallelizable: true` for capabilities
- **Automatic**: Multiple independent capabilities selected (no data dependencies)
- Manual: User requests "run in parallel" or "batch execute"

## Independence Detection
Two capabilities are independent if:
- Neither reads/writes the same file/memory key
- Neither depends on the other's output
- Both are read-only OR write to disjoint namespaces
- No ordering constraint in decision rationale

## Workflow

### 1. Dependency Analysis (pre_decision hook)
```
Input: decision.capabilities[] (from themagicscan-decision)
Process:
  1. Build capability graph: nodes=capabilities, edges=data dependencies
  2. For each capability, declare:
     - reads: [memory_keys, file_paths, mcp_resources]
     - writes: [memory_keys, file_paths, mcp_resources]
     - requires: [capability_ids that must complete first]
  3. Topological sort → identify parallelizable groups (anti-chains)
  4. Annotate decision: {capability_id, group_id, parallelizable: boolean}
```

### 2. Batch Grouping
```
Groups = connected components of independence graph
Each group = set of capabilities that can run simultaneously

Example:
  Group A (parallel): [capability-scout, grounded-citations, engraphis_recall]
  Group B (sequential after A): [themagicscan-decision]
  Group C (parallel): [engineer-system-change, architecture-decision-records]
```

### 3. Parallel Execution (post_decision hook)
```
For each group in topological order:
  if group.size == 1:
    execute sequentially (await single)
  else:
    results = await Promise.all(
      group.map(cap => invokeCapability(cap, context))
    )
    aggregate results → merged context for next group
```

### 4. Result Aggregation
```
- Preserve order within group for deterministic output
- Merge context updates: later writes override earlier (by group order)
- Collect errors: if any fail, report all, decide retry/skip/abort
- Log batch execution metrics: group_id, capabilities, duration, success_rate
```

## Integration Points
- `route.mjs`: main integration point — replace sequential dispatch with batch dispatch
- `themagicscan-decision`: output includes `parallelizable` flags + `reads/writes/requires`
- `engraphis`: memory operations in same batch must use different keys
- `continuous-learning-v2`: instinct for "multiple independent capabilities"

## Configuration
```yaml
parallel_batch_executor:
  enabled: true
  max_parallelism: 8          # max concurrent invocations per batch
  timeout_per_batch: 120000   # ms
  fail_fast: false            # collect all errors before deciding
  dependency_analysis: true   # auto-detect from capability declarations
  log_metrics: true
```

## Capability Declaration Schema (for independence analysis)
```json
{
  "capability_id": "engraphis_recall_context",
  "reads": ["engraphis:workspace:default:*"],
  "writes": [],
  "requires": [],
  "side_effects": "none"
}
```

## Example: Before vs After

### Before (Sequential - 4 turns)
```
Turn 1: capability-scout → result
Turn 2: grounded-citations → result  
Turn 3: engraphis_recall_context → result
Turn 4: themagicscan-decision → result
Total: ~40s
```

### After (Parallel - 2 turns)
```
Turn 1: Batch [capability-scout, grounded-citations, engraphis_recall_context] → all results
Turn 2: themagicscan-decision (depends on Turn 1) → result
Total: ~15s (62% reduction)
```

## Proof of Completion
- `route.mjs` dispatches capabilities in parallel batches per dependency graph
- Turn count reduced ≥30% for multi-capability tasks
- No data races (verified by dependency analysis)
- Batch execution metrics logged: group_id, duration, success_count
- `decisions.jsonl` includes `parallel_batches: N` field