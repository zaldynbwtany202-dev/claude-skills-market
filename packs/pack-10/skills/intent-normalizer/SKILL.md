---
name: intent-normalizer
description: Interpret each user request before acting, especially Arabic or multilingual requests. Preserve the real intent, desired outcome, constraints, deliverables, and prior context in a concise internal task brief.
user-invocable: false
---

# Intent normalization

Before using tools, choosing skills, delegating, or writing code:

1. Identify the user's actual desired outcome rather than only the literal wording.
2. Resolve references using the current conversation and the persistent user memory. Do not ask again for information already provided.
3. For Arabic requests, formulate a concise English task brief internally when it improves tool and capability matching. Preserve all nuance, conditions, negation, and scope. Do not translate loosely or change the user's intent.
4. Keep Arabic as the default response language unless the user asks for another language.
5. Identify deliverables, quality criteria, constraints, resource limits, and actions that must not be taken.
6. If information is missing but a safe, reasonable assumption exists, state the assumption and proceed. Ask only when an essential decision cannot safely be inferred.
7. Do not expose private chain-of-thought. Share only a concise understanding summary when it materially helps the user.
