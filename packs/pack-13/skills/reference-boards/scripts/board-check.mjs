#!/usr/bin/env node
// بوابة القرص بعد أي تشغيل توليد: ما يُعدّ «تم» في الحالة قد يكون ملفًا قديمًا
// من تشغيل سابق، و`done` يعدّ تلك الملفات القديمة نفسها. لذلك الحكم هنا على
// ما يوجد على القرص فعلًا بحجمه، لا على ما تقوله الحالة.
// Usage: node board-check.mjs --scenes scenes.json --out boards [--min-bytes 40000]
import fs from 'node:fs';
import path from 'node:path';

const args = process.argv.slice(2);
const opt = (name, dflt) => {
  const i = args.indexOf(`--${name}`);
  return i >= 0 ? args.splice(i, 2)[1] : dflt;
};
const scenesFile = opt('scenes', 'scenes.json');
const outDir = path.resolve(opt('out', 'boards'));
const minBytes = Number(opt('min-bytes', 40000));

if (!fs.existsSync(scenesFile)) {
  console.error(JSON.stringify({ ok: false, reason: 'no-scenes-file', scenesFile }));
  process.exit(2);
}
const parsed = JSON.parse(fs.readFileSync(scenesFile, 'utf8'));
const scenes = Array.isArray(parsed) ? parsed : (parsed.scenes || []);
if (!scenes.length) {
  console.error(JSON.stringify({ ok: false, reason: 'no-scenes-parsed', scenesFile }));
  process.exit(2);
}

const slugify = (s) => String(s || '').toLowerCase()
  .replace(/[^a-z0-9]+/g, '-').replace(/^-+|-+$/g, '').slice(0, 64);

// نفس قاعدة تسمية المولّد: scene-NN-<slug>.png — وأي افتراض آخر ينتج فحصًا لملفات لا توجد.
const expected = scenes.map((scene, i) => {
  const n = Number(scene.n) || i + 1;
  const slug = slugify(scene.slug || scene.name || scene.prompt) || `scene-${n}`;
  return { n, slug, file: path.join(outDir, `scene-${String(n).padStart(2, '0')}-${slug}.png`) };
});

const report = expected.map((item) => {
  let stat = null;
  try { stat = fs.statSync(item.file); } catch { stat = null; }
  return {
    slug: item.slug,
    file: path.basename(item.file),
    on_disk: Boolean(stat),
    bytes: stat ? stat.size : 0,
    // صورة مرجعية صالحة تُرى: حجمٌ معقول لا مجرد ملف موجود.
    usable: Boolean(stat) && stat.size >= minBytes,
  };
});

// المولد يحذف المسار غير الموجود من refs بصمت (chatgpt.js: files.filter(existsSync)) —
// فمرجع مكتوب بخطأ يعني برومبت بلا صورة مرجعية بلا أي خطأ. لذلك يُفحص قبل التشغيل.
const scenesDir = path.dirname(path.resolve(scenesFile));
const refsReport = scenes.map((scene, i) => {
  const n = Number(scene.n) || i + 1;
  return (Array.isArray(scene.refs) ? scene.refs : []).map((ref) => {
    const abs = path.resolve(scenesDir, String(ref));
    let stat = null;
    try { stat = fs.statSync(abs); } catch { stat = null; }
    return {
      scene: n,
      ref: String(ref),
      exists: Boolean(stat),
      bytes: stat ? stat.size : 0,
      usable: Boolean(stat) && stat.size >= minBytes,
    };
  });
}).flat();
const deadRefs = refsReport.filter((r) => !r.exists).map((r) => `scene ${r.scene}: ${r.ref}`);
const thinRefs = refsReport.filter((r) => r.exists && !r.usable).map((r) => `scene ${r.scene}: ${r.ref} (${r.bytes}B)`);
const tooManyRefs = scenes
  .map((scene, i) => ({ n: Number(scene.n) || i + 1, count: (scene.refs || []).length }))
  .filter((r) => r.count > 3)
  .map((r) => `scene ${r.n}: ${r.count} refs (واجهة ChatGPT تقبل 3 كسقف مجرَّب)`);

const saved = new Set();
const stateRoot = path.join(path.dirname(path.resolve(scenesFile)), '.scene-forge', 'runs');
try {
  for (const key of fs.readdirSync(stateRoot)) {
    const state = JSON.parse(fs.readFileSync(path.join(stateRoot, key, 'state.json'), 'utf8'));
    for (const entry of state?.summary?.saved || []) saved.add(path.basename(String(entry)));
  }
} catch { /* لا حالة مخزّنة: الحكم على القرص وحده يكفي */ }

const missing = report.filter((r) => !r.on_disk).map((r) => r.file);
const thin = report.filter((r) => r.on_disk && !r.usable).map((r) => `${r.file} (${r.bytes}B)`);
const ok = missing.length === 0 && thin.length === 0 && deadRefs.length === 0 && thinRefs.length === 0 && tooManyRefs.length === 0;

console.log(JSON.stringify({
  ok,
  outDir,
  expected: report.length,
  on_disk: report.filter((r) => r.on_disk).length,
  usable: report.filter((r) => r.usable).length,
  min_bytes: minBytes,
  missing,
  too_small: thin,
  refs_checked: refsReport.length,
  refs_missing: deadRefs,
  refs_thin: thinRefs,
  refs_over_limit: tooManyRefs,
  state_saved: [...saved],
  verdict: ok ? 'complete' : missing.length ? 'incomplete' : thin.length ? 'present-but-thin' : 'refs-unusable',
}, null, 2));
process.exit(ok ? 0 : 1);
