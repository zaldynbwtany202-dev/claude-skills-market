---
id: tool-schema-validator
name: Tool Schema Validator
version: "1.0.0"
description: |
  Cursor-pattern: fetches tool schema via discover_actions, validates args
  against JSON Schema before invocation. Fails fast with actionable error.
  Caches schemas per session.
author: THEMAGICSCAN
tags:
  - validation
  - schema
  - mcp
  - tool-safety
trigger:
  - before any MCP tool call
  - "validate tool"
  - "check schema"
  - "tool validation"
capabilities:
  - schema_fetch
  - schema_validation
  - schema_cache
  - error_reporting
dependencies: []
hooks:
  - pre_tool_call: "validate_args_against_schema"
---

# Tool Schema Validator Skill

## Purpose
Implements Cursor's schema-first tool access pattern: before any MCP tool invocation, fetch the tool's JSON Schema (via `discover_actions` / `engraphis_discover_actions`), validate the arguments against it, and fail fast with a clear error if invalid. Prevents runtime errors from malformed tool calls.

## When to Trigger
- **Automatic**: Before EVERY MCP tool call (via `pre_tool_call` hook)
- Manual: User asks "validate tool X" or "check schema for Y"

## Workflow

### 1. Schema Fetch (with caching)
```
Cache key: "tool_schema::{server}::{tool_name}"
TTL: session lifetime (or until schema_version changes)

On cache miss:
  - Call discover_actions(capability_id) → returns {schema, schema_digest}
  - Store in memory cache + persist to .opencode/schema-cache.json
```

### 2. Argument Validation
```
Input: tool_name, args_object
Process:
  1. Resolve full tool identifier (server + name)
  2. Fetch schema (from cache or discover_actions)
  3. Validate args against JSON Schema (draft-07 compatible)
  4. If valid: return {valid: true}
  5. If invalid: return {valid: false, errors: [...], schema_path}
```

### 3. Error Reporting (actionable)
```
On validation failure:
  - Error message: "Tool 'X' argument validation failed at path 'Y': expected Z, got W"
  - Include: JSON pointer to failing field, expected type/format, actual value
  - Suggest: corrected example based on schema
  - Log to decisions.jsonl with validation_failure flag
```

### 4. Cache Invalidation
- On `engraphis_discover_actions` returning different `schema_digest`
- On MCP server restart detection
- Manual: `tool-schema-validator:clear-cache`

## Integration Points
- `route.mjs`: wrap all capability invocations with `validateToolSchema()`
- `engraphis` tools: automatic via hook
- `themagicscan-decision`: include schema validation in decision flow
- `continuous-learning-v2`: instinct for "MCP tool about to be called"

## Configuration
```yaml
tool_schema_validator:
  cache_enabled: true
  cache_path: ".opencode/schema-cache.json"
  strict_mode: true          # fail on unknown properties
  coerce_types: false        # don't auto-coerce strings to numbers
  validate_before_every_call: true
  log_failures: true
```

## Example Validation Error
```
Tool 'engraphis.engraphis_remember' argument validation failed at path '/arguments/mtype':
  expected: "semantic" | "episodic" | "procedural" | "instinct"
  got: "fact"
  
  Schema allows: semantic, episodic, procedural, instinct
  Suggestion: use "semantic" for factual knowledge
  
  Corrected example:
  {
    "capability_id": "engraphis_remember",
    "schema_digest": "abc123",
    "arguments": {
      "workspace": "default",
      "mtype": "semantic",
      "subject_key": "user.preference.language",
      "content": "Arabic"
    }
  }
```

## Proof of Completion
- Zero tool invocations with schema violations in session logs
- All validation failures caught pre-invocation with actionable errors
- Schema cache hit rate > 90% after warm-up
- `decisions.jsonl` entries include `schema_validated: true` for each tool call