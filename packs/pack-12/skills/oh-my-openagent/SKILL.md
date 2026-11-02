---
name: oh-my-openagent
description: OmO: Just type 'mass ulw' keyword with your prompt. Master of graph engineering. Graph-based agent framework with advanced memory.
tags: [agent, graph, memory, omo, graph-engineering]
---

# Oh-My-OpenAgent (OmO) — Graph Engineering

**نوع المهارة**: Agent / Memory / Graph
**المصدر**: [code-yeongyu/oh-my-openagent](https://github.com/code-yeongyu/oh-my-openagent) على GitHub

## ملخص

`OmO` — أطر عمل هندسة الرسوم البيانية (graph engineering) للوكلاء. الفكرة: الوكيل ليس جملة واحدة بل **بيان بياني**، ويبني شبكة من المعرفة والمهام ويربطها.

activate bluntly: اكتب `"mass ulw"` مع طلبك → يعمل في وضع ULW (ultra work) على مستوى الرسوم البيانية.

## متى تستخدمها

- مشاريع معقدة تحتاج ذاكرة رسومية لا نصية (خريطة علاقات).
- تحليل عميق متعدد المستويات مع تتبّع الاعتماديات.
- مهام تحتاج "مسح شامل" (ultra-wide-load) لا خطوات محدودة.

## التثبيت

```bash
# Linux/macOS
curl -fsSL https://get.omo.dev/install.sh | bash
omo

# Windows PowerShell
irm https://get.omo.dev/install.ps1 | iex
```

يضع الـ binary في `~/.local/bin`، يتحقق من checksums، ويتراجع إلى GitHub Releases إذا تعذّر المرآة.

## القدرات المتاحة

| القدرة | الوصف | طريقة الاستدعاء |
|---|---|---|
| `omo.ulw` | تشغيل وضع ULW | `shell: omo "mass ulw <task>"` |
| `omo.graph` | بناء رسم بياني للمعرفة | `shell: omo graph` |
| `omo.memory` | ذاكرة رسومية متقدمة | `mcp: engraphis` كبديل |

## قواعد الاستخدام

1. OmO مثالي للمهام الطويلة/المتشعبة، وليس لجملة واحدة.
2. استخدمه مع `engraphis` — OmO للرسم البياني، engraphis للذاكرة الحاكمة.
3. `mass ulw` expansief — استخدمه للبحث الشامل لا للجزء الصغير من مهمة.

## الروابط

- [الموقع](https://ohmyopenagent.com)
- [التوثيق](https://github.com/code-yeongyu/oh-my-openagent#readme)
