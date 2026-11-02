---
name: themagicscan
description: Full-capability routing and orchestration for Qoder. Before non-trivial tasks, scan skills, agents, commands, MCP servers, plugins, bundles, local tools and memory; choose an execution mode (solo, team, council, arena, adversarial); use every relevant capability; execute, verify with evidence, and record outcomes. Use when the user asks what capabilities exist, to remember something, or to verify installed tools.
---

# THEMAGICSCAN — مسح القدرات وتنسيق التنفيذ

## في كل طلب غير بسيط

1. اقرأ كتلة `[THEMAGICSCAN]` المحقونة تلقائيًا في بداية الرسالة (خطاف `UserPromptSubmit`).
2. إن لم تظهر، شغّل:
   `node C:\Users\Admin\.qoder\themagicscan\router.mjs "<الطلب>"`
3. اقرأ حقول الكتلة: فهم المهمة، وضع التنفيذ، الفريق، التغطية، القدرات، البوابة، و`plan_path`.
4. اقرأ `SKILL.md` لكل مهارة مختارة، وملف الدور لكل وكيل أدوار. اقرأ الخطة الكاملة من `plan_path` عند الحاجة.
5. نفّذ كل بند مختار فعليًا. شغّل المستقل منها بالتوازي، والمعتمد منها بالترتيب. عند إنشاء وكيل فرعي، ضمّن `plan_path` في prompt لأن الخطاف لا يعمل داخل الوكلاء الفرعيين.
6. تحقّق بدليل قابل للفحص: ملف ناتج، خروج أمر، اختبار، أو استدعاء أداة حقيقي.
7. سجّل النتيجة:
   - `node C:\Users\Admin\.qoder\themagicscan\feedback.mjs record --name <المهارة> --outcome pass|fail --note "<ملاحظة>"`
   - `node C:\Users\Admin\.qoder\themagicscan\memory.mjs add --key <مفتاح> --text "<حقيقة دائمة>" --tags <وسوم>`

## أوضاع التنفيذ

| الوضع | متى يُختار | التشكيلة |
|---|---|---|
| `solo` | مهمة محددة أو بسيطة | مهارة رئيسية + قدرات مساندة |
| `team` | بناء متعدد الأدوار (واجهة + بيانات + اختبار) | قائد + منفذ + مراجع، ومهام متوازية |
| `council` | قرار غامض أو تقييم فكرة | 4 زوايا ثم قرار واحد + حكم |
| `arena` | بدائل تحتاج مقارنة نقدية | 3 منافسين فقط، ثم حكم — لا 100 |
| `adversarial` | مخاطر أمنية أو تغيير حساس | مراجعان مستقلان + بوابة تحقق مزدوجة |

المهام البسيطة لا تستدعي مجلسًا ولا منافسة. والوضع يحدده الراوتر من نص المهمة، لا المستخدم.

## قراءة التغطية

- سطر التغطية يوضح ما فُحص: المهارات والوكلاء والأوامر والحزم وخوادم MCP والأدوات المحلية.
- القائمة القصيرة ليست كل المخزون؛ الفهرس الكامل في `index.json` ويُقرأ عند الحاجة.
- إذا لم يجد الراوتر مطابقة قوية، استخدم `skill-scout` للبحث ثم سجّل سبب عدم المطابقة.
- لا تستدعِ كل ما في الفهرس، ولا تُسقط قدرة مناسبة دون سبب مكتوب.

## قواعد إلزامية

- لا تسأل المستخدم أي أداة أو مهارة أو وكيل يستخدم. قرّر أنت وبرّر.
- الفهرس يثبت الإدراج فقط. الاتصال والتشغيل يحتاجان استدعاءً فعليًا.
- لا تدّعِ نجاحًا بلا مخرج. لا تخلط بيانات الاختبار بالإنتاج.
- الذاكرة: `memory.jsonl` للاسترجاع السريع، وEngraphis للأحداث الدائمة عبر الجلسات.
- لا تخزّن أسرارًا أو كلمات مرور أو رموز وصول في الذاكرة أو السجلات.
- أي قدرة لم تُستخدم فعليًا لا تُذكر في التقرير.

## الاعتمادية والعقد الرفيع

- يكتب الخطاف الخطة الكاملة ذريًا تحت `plans/`، ويحقن عقدًا لا يتجاوز 1,200 حرف مع `plan_path`.
- تحوي الخطة الأسماء والمسارات ومفاتيح الذاكرة فقط؛ لا تحفظ نص الطلب، ولا نص الذاكرة، ولا `context`، ولا أوصاف القدرات الخام.
- مسارات `THEMAGICSCAN_PLAN_DIR` و`THEMAGICSCAN_LOG_DIR` و`THEMAGICSCAN_INDEX_PATH` و`THEMAGICSCAN_LAST_GOOD_INDEX_PATH` و`THEMAGICSCAN_MEMORY_PATH` و`THEMAGICSCAN_FEEDBACK_PATH` مقبولة فقط داخل مجلد النظام أو المجلد المؤقت؛ غير ذلك يعود إلى المسار الافتراضي.
- يسجل `logs/routes.jsonl` سبب كل تجاوز (`empty` أو `simple` أو `slash-command` أو `subagent`)، ولا يسجل نص الطلب. حقول `session_id` و`cwd` تُطبع في سطر واحد وتصُحح أسرارها قبل التسجيل، فلا يمكن لمدخل خارجي تزييف سطر سجل. أخطاء الخطاف تُسجل كحدث JSON واحد برسالة محدودة ومصححة.
- عند تلف الفهرس الأساسي أو محتواه غير الصالح يُستخدم `index.last-good.json`؛ وتظهر تحذيرات التدهور أو القدم في العقد ولا تُحذف عند ضيق المساحة.
- عند فشل التوجيه يُحقن عقد احتياطي صادق ومحدود، ويُسجل `routing-error` بدل ادعاء مطابقة قدرات غير موثوقة.

## الوكلاء

- 202 ملف دور في `C:\Users\Admin\agents\plugins\*\agents\*.md`، تُستدعى عبر `general-purpose` مع تعليمات الملف.
- 70 وكيلًا أصليًا من إضافة ECC (`ecc:code-reviewer`, `ecc:security-reviewer`, `ecc:architect`, `ecc:agent-evaluator`...) تُستدعى مباشرة.
- في وضع `team`: قائد يقسّم، منفذون متوازون، مراجع مستقل يتحقق قبل التسليم.

## الاكتشاف والتحديث

- عند إضافة مهارة أو خادم MCP: `node build-index.mjs` ثم `node status.mjs`.
- `status.mjs` يفحص أيضًا حداثة الفهرس مقابل آخر تعديل للمهارات المثبتة.
- `node status.mjs` وحده يفحص الإعداد فقط. ادّعاء نجاح الاختبارات يحتاج `node status.mjs --run-tests` الذي يشغّل ثلاث المجموعات فعليًا ويبلغ عن عدد الناجح والفاشل.
- خوادم MCP الحية تُدمج من إعدادات Qoder عند بناء الفهرس.

## أوامر التحقق

```powershell
node C:\Users\Admin\.qoder\themagicscan\status.mjs
node C:\Users\Admin\.qoder\themagicscan\router.mjs --json "<الطلب>"
node C:\Users\Admin\.qoder\themagicscan\memory.mjs search "<كلمة>" --limit 5
node C:\Users\Admin\.qoder\themagicscan\feedback.mjs stats
Get-Content C:\Users\Admin\.qoder\themagicscan\logs\routes.jsonl -Tail 5
node C:\Users\Admin\.qoder\themagicscan\build-index.mjs
node --test C:\Users\Admin\.qoder\themagicscan\themagicscan.test.mjs
node C:\Users\Admin\.qoder\themagicscan\scenario-tests.mjs
node C:\Users\Admin\.qoder\themagicscan\routing-eval.mjs
node C:\Users\Admin\.qoder\themagicscan\status.mjs --run-tests
node --experimental-test-coverage --test C:\Users\Admin\.qoder\themagicscan\themagicscan.test.mjs
```

- `scenario-tests.mjs` يشغّل الخطاف كعملية حقيقية بملفات خطة وسجل وذاكرة ومع تغذية راجعة معزولة في مجلد مؤقت، فيقرأ الفهرس الحقيقي دون لمس حالة المستخدم المتراكمة.
- `verify-all.mjs` يخرج بكود غير صفري عند كسر حقيقي: مسار مهارة أو وكيل مفقود، أو ملف أمر مفقود، أو خطاف غير مُعدّ. المداخل بلا مسار (كتالوج خارجي) تُبلَّغ كـ `virtual` ولا تُحسب كسرًا.
- `routing-eval.mjs` يفرض وضع كل مطالعة مصنّفة ويبلغ `capabilityGaps`: مطالبة خطر (`مرتفع`) تُوجَّه بلا قدرات تُعدّ فشلًا، لا نجاحًا صامتًا.
- العقد المحقن لا يتجاوز 1,200 حرف لكل مطالعة في مجموعة التقييم، ولا يسقط القدرة الأولى لمطالبة خطرة — يختبرها `themagicscan.test.mjs`.

## الذاكرة الدائمة

- محلية سريعة: `C:\Users\Admin\.qoder\themagicscan\memory.jsonl`
- دائمة عبر الجلسات: Engraphis MCP — `engraphis_session` ثم `engraphis_remember` ثم `engraphis_recall_context`.
- ملفات الذاكرة التلقائية في Qoder: `C:\Users\Admin\.qoder\memory\`.
- الأعداد الحالية (مهارات مثبتة وفهرس ووكلاء وأوامر) تُقرأ من `node verify-all.mjs`؛ لا تُثبَّت في هذه الوثيقة لأنها تتقادم مع كل تثبيت.
