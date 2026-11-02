---
name: deer-flow
description: An open-source long-horizon SuperAgent harness that researches, codes, and creates. With the help of sandboxes, memories, tools, skills, subagents and message gateway.
tags: [agent, orchestration, superagent, sandbox, memory, long-horizon]
---

# DeerFlow — SuperAgent Harness

**نوع المهارة**: Agent / Orchestration
**المصدر**: [bytedance/deer-flow](https://github.com/bytedance/deer-flow) على GitHub
**الترخيص**: MIT

## ملخص

`deer-flow` من بايتدانس هو حَوْل (harness) لسوبر-وكلاء (SuperAgent) مفتوح المصدر، مصمم لمهام على مدى أسبوعين. يدمج:
- **Python 3.12+** خلفية للمنطق والمعالجة
- **Node.js 22+** للواجهة الأمامية وإدارة المهام
- **sandbox** لتشغيل الكود والأمان
- **نظام ذاكرة** يحفظ السياق بين الجلسات
- **subagents** و tools و skills
- **message gateway** للتواصل

يدعم الأهداف المعقدة التي قد تستغرق دقائق إلى ساعات — الأبحاث، البرمجة، الإبداع.

## متى تستخدمها

- هدف طويل الأفق بحاجة لسلوكيات متعددة المراحل (research → analyze → implement → review).
- مشاريع تحتاج sandbox آمن لتشغيل أكواد/نصوص غير موثوقة.
- مطلوب ذاكرة شخصية تستمر بين المهام (ملفات، بيانات، إعدادات).
- سير عمل multi-agent يحتاج تنسيق subagents و tools.

## التثبيت

```bash
git clone https://github.com/bytedance/deer-flow.git
cd deer-flow
# Python backend
pip install -r backend/requirements.txt
# Node.js frontend
npm install
# أو استخدم Docker
docker compose up
```

## القدرات المتاحة داخل هذه المهارة

| القدرة | الوصف | طريقة الاستدعاء |
|---|---|---|
| `deerflow.run` | تشغيل مهمة طويلة الأفق | `subagent: deer-flow` |
| `deerflow.sandbox` | تشغيل كود داخل sandbox آمن | `tool: shell (docker run)` |
| `deerflow.memory` | حفظ/استعادة سياق المهمة | `mcp: engraphis` |
| `deerflow.research` | بحث منهجي + تلخيص مصادر | `subagent: content-marketing__search-specialist` |
| `deerflow.code` | كتابة/مراجعة كود بعد إعداد البيئة | `subagent: backend-development__backend-architect` |

## قواعد الاستخدام

1. لا تُشغّل DeerFlow إذا كانت المهمة قصيرة — استخدم subagent مباشرة.
2. DeerFlow يدير subagents بنفسه، لكن **أنت** المنسق الأعلى — راقب التقدم، صحح الاتجاه.
3. sandbox يُفرض على الأكواد الخارجية — لا تثق بنصوص المستخدم داخل البيئة الرئيسية.
4. الذاكرة تُحفظ في `engraphis` — استخدمها بدلاً من إعادة كتابة السياق.

## مثال

```
المهمة: ابحث عن أحدث أبحاث الـ LLM agents ثم نفذ proof-of-concept
باستخدام DeerFlow:
1) deerflow.run — يوزع على subagents
2) deerflow.sandbox — يشغّل الكود
3) deerflow.memory — يحفظ النتائج
```

## القيود

- يتطلّب Python 3.12+ و Node.js 22+.
- الـ sandbox قد لا يتوفر في بعض بيئات Windows — استخدم WSL أو Docker.
- يفضّل اتصال إنترنت مستقر للـ memory gateway.

## الروابط

- [الموقع الرسمي](https://deerflow.tech)
- [الوثائق](https://github.com/bytedance/deer-flow/tree/main/docs)
- [أمثلة الاستخدام](https://github.com/bytedance/deer-flow/tree/main/examples)
