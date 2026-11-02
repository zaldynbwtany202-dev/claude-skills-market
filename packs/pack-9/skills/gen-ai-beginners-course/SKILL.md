---
name: gen-ai-beginners-course
description: Reference library of Microsoft's "Generative AI for Beginners" course (v3, 21 lessons, MIT) cloned locally — Learn lessons (prompt engineering, RAG, agents, fine-tuning, function calling, embeddings, safety) and Build lessons with Python/TypeScript samples. Use when the user wants to learn or review a GenAI concept, asks for an explanation with a worked code example, or needs course material cited for a lesson; read the specific lesson's README on demand — never load the whole course.
---

# دورة الذكاء التوليدي للمبتدئين (مرجع محلي)

مستودع مرجعي مستنسخ: `C:\Users\Admin\.agents\repos\generative-ai-for-beginners`
(المصدر: github.com/microsoft/generative-ai-for-beginners — MIT، v3، 21 درسًا).
نسخة sparse بلا مجلدات الترجمات لتقليل الحجم.

## كيف تستخدمها

1. حدد المفهوم الذي يطلبه المستخدم (RAG؟ وكلاء؟ هندسة أوامر؟) وابحث عن درسه:
   ```
   ls C:\Users\Admin\.agents\repos\generative-ai-for-beginners
   ```
   كل درس مجلد مرقّم `NN-name` فيه `README.md` هو الدرس نفسه.
2. اقرأ README الدرس المطلوب فقط (تحميل تدريجي — لا تحمّل الدورة كلها).
3. عينات الكود (Python/TypeScript) داخل كل درس في مجلدات `code/` بجوار README.
4. الإعداد بيئة API (OpenAI/Azure/Foundry Local) موثق في `00-course-setup`.

## خرائط الدروس السريعة

- المفاهيم: 01 مقدمة، 02 مقارنة LLMs، 03 الاستخدام المسؤول، 05 أوامر متقدمة،
  11 تقييم وfunctions، 13 الأمان، 14 الدورة الكاملة، 18 ضبط دقيق، 19 SLMOps،
  20 Mistral، 21 Meta
- التطبيق العملي: 06 توليد نص، 07 تطبيقات محادثة، 08 بحث (RAG/Vector DBs)،
  09 توليد صور، 10 بناء تطبيقات low-code، 12 تصميم UX للـGenAI، 15-17 وكلاء
  (مقدمة/تصميم/مشاريع تحليلية)، 17 وكلاء DevOps

## قواعد

- هذه مرجع للقراءة لا أداة تنفيذ: عند طلب «اشرح RAG» اقرأ درس 08 ولخّص بمثاله.
- لا تعدّل محتوى المستودع (يبقى قابلاً لـ git pull).
- ذكر رقم الدرس ومصدره عند الاستشهاد («الدرس 08: Building Search Applications»).
