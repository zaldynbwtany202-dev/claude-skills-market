---
name: github-repository-evaluation
description: Evaluate GitHub repositories for capability migration, installation, adaptation, or knowledge extraction. Use when inspecting the user's 1,404-repository URL list or any new repository.
---

# GitHub Repository Evaluation

For each URL:
1. Normalize the URL and identify owner/repository. Reject malformed links as invalid, but retain the source row in the audit.
2. Verify repository existence and whether the URL points to a repository, organization, user, issue, discussion, settings page, or other GitHub route.
3. Read README, license, package manifests, installation docs, supported platforms, releases, recent commit activity, and architecture.
4. Inspect the source code and critical dependencies rather than trusting the README alone.
5. Determine Windows support, Node/Python/Rust/Go requirements, GPU/VRAM/RAM/disk needs, network needs, API credentials, and ongoing service costs.
6. Compare against existing capabilities in ZCode, OpenCode, and Claude Code. Identify overlap and unique value.
7. Check security risks: install scripts, postinstall hooks, broad shell access, credential handling, telemetry, and untrusted binary downloads.
8. Choose one strategy:
   - DIRECT: use/install with minimal adaptation.
   - ADAPT: port instructions or source to Claude Code conventions.
   - ADAPTER: wrap external behavior with a documented bridge.
   - REBUILD: reproduce the useful behavior with Claude Code-native primitives.
   - KNOWLEDGE_ONLY: extract architecture, docs, patterns, prompts, or reusable code concepts without running the full project.
   - SKIP: invalid, duplicate, abandoned, unsafe, costly, incompatible, or irrelevant.
9. Record exact evidence, source date, license, dependencies, and reason.

Do not clone or install a repository merely because it appears in the URL list. A heavyweight project can still be valuable as a knowledge source.
