---
name: system-prompts-leaks
description: Documented system prompts from Anthropic Claude, OpenAI ChatGPT, Google Gemini, xAI Grok and more. Reference and security research.
tags: [reference, security, system-prompts, research]
---

# System Prompts Leaks — Reference & Security Research

**نوع المهارة**: Reference / Security
**المصدر**: [asgeirtj/system_prompts_leaks](https://github.com/asgeirtj/system_prompts_leaks) على GitHub

## ملخص

مجموعة من الـ **system prompts الكاملة** (verbatim) لأكثر النماذج الذكاء الاصطناعية شعبية في العالم:

- **Anthropic**: Claude Fable 5.1, Claude Opus 5.5, Claude Design, Claude Code
- **OpenAI**: ChatGPT GPT-6-Astra, Codex
- **Google**: Gemini 3.8 Flash, Gemini 3.1 Pro, Gemini Antigravity
- **xAI**: Grok، Grok Bot
- **أخرى**: Cursor، Kimi، وأكثر

تُحدَّث بانتظام.

## متى تستخدمها

- أمان: افحص ما يُرى من system prompt للـ agents التي تبنيها — احذف التعليمات الخطرة.
- توافق: تحط مواصفات سلوك الـ agent لتطابق نماذج إنتاجية.
- تعديل: استشهد بالسلوك الفعلي للنماذج لتكتب system prompts أفضل.
- بحث: دراسة كيف تُصمم أنظمة الـ safety لكل مزوّد خدمات.

## التثبيت

```bash
git clone https://github.com/asgeirtj/system_prompts_leaks.git
cd system_prompts_leaks
# استخدم python لاستخراج الملفات:
python -m json.tool prompts/*.json
```

## القدرات المتاحة

| القدرة | الوصف | طريقة الاستدعاء |
|---|---|---|
| `prompts.browse` | استعراض الـ system prompts حسب المزوّد | `shell: grep -r . prompts/` |
| `prompts.compare` | مقارنة سلوكين نموذجيين | `shell: diff prompts/claude.md prompts/gemini.md` |
| `prompts.audit` | فحص agent system prompt مقابل المرجع | `prompt-engineer` كـ subagent |

## قواعد الاستخدام

1. هذه مرجعية — لا تنسخ الـ system prompts مباشرة لأنها ربما تحتون IP أو قيود استخدام.
2. استخدم للمقارنة والبحث فقط.
3. إذا وجدت تعارضًا بين سلوك الـ model ومقابضة security — أبلغ المطور.

## الروابط

- [الموقع المصغر](https://go.asgeirtj.workers.dev/latitude)
- [Latitute — تحليل الـ agents في الإنتاج](https://go.asgeirtj.workers.dev/latitude)
