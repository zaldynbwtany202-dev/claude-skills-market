---
name: hyperframes
description: Write HTML. Render video. Built for agents. NPM package for HTML-to-MP4 rendering.
tags: [media, video, html, rendering, agent]
---

# HyperFrames — HTML to Video Rendering

**نوع المهارة**: Media / Video Generation
**المصدر**: [heygen-com/hyperframes](https://github.com/heygen-com/hyperframes) على GitHub
**الترخيص**: MIT

## ملخص

`HyperFrames` يكتب HTML ويحرّكه كفيديو. مُصمم خصيصًا للوكلاء:
- اكتب HTML/CSS/JS ← هذا كل ما تحتاجه
- الرندر يحدث في السحابة (browser-as-a-service)
- يدعم CSS متحرك، Canvas، WebGL
- يخرج MP4 جاهز لوس أو مشاركة

## متى تستخدمها

- مهام توليد فيديو بواجهة مستخدم ديناميكية (لوحات تقديم، إعلانات، توضيحات).
- فرق فنية تفضّل HTML على بدائل فيديو مغلقة.
- تكاملٌ سهل مع pipelines سكربت أو agent workflow.
- متطلباتٌ بسيطة: اكتب HTML، احصل على MP4.

## التثبيت

```bash
# مع Claude Code
claude plugin marketplace add heygen-com/hyperframes
claude plugin install hyperframes@hyperframes

# أو كحزمة npm
npm install hyperframes
```

## القدرات المتاحة

| القدرة | الوصف | طريقة الاستدعاء |
|---|---|---|
| `hyperframes.render` | رندر HTML إلى فيديو | `subagent: video-farm` أو `shell: npx hyperframes` |
| `hyperframes.preview` | معاينة سريعة (أول 3 ث) | `shell: npx hyperframes --quick` |
| `hyperframes.batch` | رندر 100 نسخة متغيّرة | `shell: npx hyperframes --batch` |

## قواعد الاستخدام

1. لا تُرسل JavaScript غير موثوق من المستخدم مباشرة — راقبه.
2. استخدم `preview` قبل `render` لتوفير التكلفة.
3. HyperFrames بديل موثوع للوكلاء الذين يطلبون `video_generate` لكنهم ليس لديهم واجهة HTML.

## القيود

- يتطلاب اتصال إنترنت للرندر السحابي.
- بعض تأثيرات CSS قد لا تدعمها المحركات القديمة.

## الروابط

- [NPM package](https://www.npmjs.com/package/hyperframes)
- [الوثائق](https://github.com/heygen-com/hyperframes#readme)
