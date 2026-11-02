---
name: langflow
description: Visual builder for AI agents and workflows (Langflow, MIT) installed locally in a venv — drag-and-drop flows, multi-agent orchestration, RAG pipelines, and deploying flows as APIs or MCP servers. Use when the user wants to build/prototype an agent or workflow visually, export a flow as an API endpoint or MCP tool, or run the Langflow server at localhost:7860; launch via the repo venv, never a global pip install.
---

# Langflow — باني الوكلاء البصري (مثبت محليًا)

مستودع مرجعي: `C:\Users\Admin\.agents\repos\langflow` (github.com/langflow-ai/langflow — MIT)
البيئة: `.venv` داخل المستودع (Python 3.12) والحزمة مثبتة فيها عبر `pip install langflow`.

## التشغيل

```bash
cd C:\Users\Admin\.agents\repos\langflow
# بيئة الإقلاع (لا تحذفها): auto-login للواجهة + سوبريوزر معروف للـAPI
set LANGFLOW_AUTO_LOGIN=true
set LANGFLOW_SUPERUSER=zcode
set LANGFLOW_SUPERUSER_PASSWORD=zcodeLocal2026
.venv\Scripts\langflow.exe run
# المتصفح: http://127.0.0.1:7860 — يدخل مباشرة بلا شاشة تسجيل
```

- الخادم طويل العمر: شغّله في مهمة خلفية **بلا أنبوب `| head`** (الأنبوب يقتله بعد أسطر قليلة!). الإقلاع 1–2 دقيقة.
- التحقق: `curl http://127.0.0.1:7860/health` → `{"status":"ok"}`

## وصفة الـAPI (مجرّبة 2026-10-31)

- `/auto_login` مسار **واجهة** (يرجع HTML) — للـAPI استخدم form-login: `POST /api/v1/login` بـ`application/x-www-form-urlencoded` وبيانات `zcode/zcodeLocal2026` → `access_token`.
- بناء عقدة مخصصة: `POST /api/v1/custom_component` {code} (Bearer token) → الرد `data` هو `node` التدفق مباشرة (لا يوجد `data.node`).
- إنشاء تدفق: `POST /api/v1/flows/` {name, description, data:{nodes:[{id,type:'genericNode',position,data:{id,type,node,showNode:true}}],edges:[]}}.
- **تشغيل تدفق** `POST /api/v1/run/{id}` يتطلب **مفتاح API** (v1.5+): أنشئه بـ`POST /api/v1/api_key/` بالتوكن ثم استخدم ترويسة `x-api-key`. التفويض: `{"tweaks":{"<node-id>":{"<input>":"<قيمة>"}}}` — المخرجات الجانبية (كصور المزرعة) تُدقَّق على القرص لا في الرد.
- مثال جاهز: تدفق «استوديو المانغا (مزرعة الصور)» + مكوّن `MangaFarmComponent` في `D:\book the end of world\manga-experiment\`.

## متى تستخدمه

- بناء وكيل أو سير عمل بصريًا جرّبًا سريعًا (بدل كتابة كود من الصفر)
- RAG جاهز: موصلات Vector DBs وتقسيم مستندات من الواجهة
- نشر التدفق كـ API أو **MCP server** (يتكامل مع THEMAGICSCAN: تدفقك يصبح أداة MCP قابلة للاختيار من الفاحص!)
- تصدير التدفق JSON لتشغيله من كود Python

## قواعد

- مفاتيح LLM تُدخل من واجهة Langflow أو متغيرات بيئة — لا تُكتب في ملفات التدفق المشتركة.
- التدفقات تُحفظ في قاعدة Langflow الداخلية؛ صدّر JSON قبل أي تعديل كبير.
- إن طلب المستخدم سير عمل نهائي بالكود فالكود المباشر أنسب؛ langflow للنمذجة البصرية والتجريب.
