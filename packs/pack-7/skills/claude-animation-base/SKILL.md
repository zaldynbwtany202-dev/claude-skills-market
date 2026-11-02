---
name: claude-animation-base
description: Generate hand-painted 2D cartoon animation videos (MP4) with the Clawd character — p5.js + p5.brush starter kit with 31 acted emotions, views, hats, emotes and dances. Use when the user asks for a cartoon/animated video in hand-painted style, a Clawd animation, or storyboarding an animated clip; read ANIMATION_GUIDE.md in the repo first, storyboard, build shot by shot, render contact sheets to check, then output MP4 via render.mjs.
---

# ClaudeAnimationBase — تحريك كرتوني مرسوم يدوياً

مستودع عامل مثبّت محلياً: `C:\Users\Admin\.agents\repos\ClaudeAnimationBase`
(المصدر: github.com/JohnHeibel/ClaudeAnimationBase — MIT)

## الاستخدام

1. اقرأ أولًا `ANIMATION_GUIDE.md` في المستودع (القواعد وسير العمل وواجهة API كاملة).
2. حوِّط (Storyboard) الفيديو المطلوب مشهداً بمشهد قبل كتابة أي كود.
3. ابنِ المشاهد في `src/scenes/` (يوجد demo جاهز) باستخدام:
   - `src/clawd.js` — شخصية Clawd: الاتجاهات، 31 عاطفة ممثلة، عيون، أفواه، قبعات، إيماءات، رقصات
   - `src/core.js` — الرسم والتوقيت والحركة والكاميرا والإضاءة والورق
   - `src/timeline.js` — اللقطات والحلقات وانتقال brush-wipe
   - `src/config.js` — الطول والإيقاع
4. تحقق من عملك: صيّر contact sheets ثم عدّل قبل الإخراج النهائي.
5. صيّر الفيديو:
   ```
   cd C:\Users\Admin\.agents\repos\ClaudeAnimationBase
   node render.mjs --clip --out=out/video.mp4
   ```
6. للمعاينة التفاعلية: افتح `studio.html` في Chrome (أضف `?loop=emotions` أو `?loop=views` لصفحات النماذج).

## الاعتماديات (مثبتة ومتحقق منها 2026-10-30)

- Node.js v24 ✅ — `npm install` نُفّذ داخل المستودع
- Chrome: `C:\Program Files\Google\Chrome\Application\chrome.exe` ✅ (مرر `--chrome` إن لزم)
- ffmpeg 9.0.2 ✅ في `C:\Users\Admin\.local\bin\ffmpeg`

## أعلام الرندر المفيدة

- `--chrome=<path>` أو متغير `CHROME_PATH`
- `--soft-gl` عند غياب GPU
- `--gpu-angle=gl-egl` أو `gl-vulkan` لرندر headless على NVIDIA
- `node gpu_probe.mjs <chrome-path>` لفحص معدّات الرندر

## أمثلة على الطلبات

- «اصنع فيديو 15 ثانية لـ Clawd يحاول الإمساك بفراشة» → اقرأ الدليل، حوِط، ابنِ المشهد في src/scenes، صيّر، تحقق، سلّم out/video.mp4.
- عاطفة محددة من الـ31؟ انظر docs/ (model sheets: emotions + views/motion/hats).
