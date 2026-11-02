#!/usr/bin/env node
// يجمع لوحات المراجع في لوحة واحدة. بلا ffmpeg (غير موجود على هذا الجهاز):
// التركيب يتم بـ System.Drawing عبر PowerShell، وهو مُختبَر هنا.
// Usage: node assemble-board.mjs --out refs/master.png [--width 3840] [--height 2160] [--gap 24] panel1.png panel2.png ...
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { execFileSync } from 'node:child_process';

const PS = `
param([string]$PlanFile)
Add-Type -AssemblyName System.Drawing
$plan = Get-Content -LiteralPath $PlanFile -Raw | ConvertFrom-Json
$canvas = New-Object System.Drawing.Bitmap ([int]$plan.width), ([int]$plan.height)
$g = [System.Drawing.Graphics]::FromImage($canvas)
$g.InterpolationMode = [System.Drawing.Drawing2D.InterpolationMode]::HighQualityBicubic
$g.SmoothingMode = [System.Drawing.Drawing2D.SmoothingMode]::HighQuality
$g.Clear([System.Drawing.Color]::FromName([string]$plan.bg))
foreach ($cell in $plan.cells) {
  $img = [System.Drawing.Image]::FromFile([string]$cell.file)
  $scale = [Math]::Min([double]$cell.w / $img.Width, [double]$cell.h / $img.Height)
  $dw = [int]([double]$img.Width * $scale)
  $dh = [int]([double]$img.Height * $scale)
  $x = [int]$cell.x + [int](($cell.w - $dw) / 2)
  $y = [int]$cell.y + [int](($cell.h - $dh) / 2)
  $g.DrawImage($img, $x, $y, $dw, $dh)
  $img.Dispose()
}
$fmt = if ("$($plan.format)" -eq 'jpg') { [System.Drawing.Imaging.ImageFormat]::Jpeg } else { [System.Drawing.Imaging.ImageFormat]::Png }
$canvas.Save([string]$plan.out, $fmt)
$g.Dispose()
$canvas.Dispose()
`;

const args = process.argv.slice(2);
const opt = (name, dflt) => {
  const i = args.indexOf(`--${name}`);
  return i >= 0 ? args.splice(i, 2)[1] : dflt;
};
const out = opt('out', '');
const width = Number(opt('width', 3840));
const height = Number(opt('height', 2160));
const gap = Number(opt('gap', 24));
const bg = opt('bg', 'White');
// الشبكة تُحسب بنسبة اللوحة نفسها لا بنسبة القماش: ثلاث لوحات 16:9 في قماش 16:9
// تحتاج 2x2 لا 3x1، وإلا بقي نصف كل خلية فراغًا وخرجت اللوحة الشاملة صغيرة التفاصيل.
const panelAspect = Number(opt('panel-aspect', 16 / 9));
const lockHeight = args.includes('--lock-height') && (args.splice(args.indexOf('--lock-height'), 1), true);
// opt() تحذف الراية وقيمتها من args، فلا يجوز حساب اللوحات قبل كل قراءة خيار:
// كان --panel-aspect 1.7778 يترك «1.7778» في قائمة اللوحات كملف مفقود.
const files = args.filter((a) => !a.startsWith('--')).map((f) => path.resolve(f));

if (!out || files.length < 1) {
  console.error('usage: node assemble-board.mjs --out master.png [--width 3840 --height 2160 --gap 24 --panel-aspect 1.7778] panel1.png panel2.png ...');
  process.exit(2);
}
const missing = files.filter((f) => !fs.existsSync(f));
if (missing.length) {
  console.error(JSON.stringify({ ok: false, reason: 'missing-panels', missing }, null, 2));
  process.exit(1);
}
const empty = files.filter((f) => fs.statSync(f).size === 0);
if (empty.length) {
  console.error(JSON.stringify({ ok: false, reason: 'zero-byte-panels', empty }, null, 2));
  process.exit(1);
}

const n = files.length;
const cols = Math.min(n, Math.max(1, Math.round(Math.sqrt((n * (width / height)) / panelAspect))));
const rows = Math.ceil(n / cols);
const pad = gap;
const innerW = width - 2 * pad;
const cellW = Math.floor((innerW - (cols - 1) * gap) / cols);
// ارتفاع اللوحة الشاملة يُشتق من ارتفاع لوحاتها، لا من قماش ثابت: لوحة 16:9 داخل
// قماش 16:9 لا تتمدد، فكل خانة أعرض منها فراغ. «--lock-height» وحده يعيد القماش الثابت.
const cellH = lockHeight
  ? Math.floor((height - 2 * pad - (rows - 1) * gap) / rows)
  : Math.round(cellW / panelAspect);
const canvasH = rows * cellH + (rows - 1) * gap + 2 * pad;
// خلايا موحدة القياس بنسبة اللوحة نفسها (لا فراغ داخل الخلية)، والصف الناقص يُوسَّط
// ككتلة: تمديد آخر صف على العرض كاملًا كان يعطي خانة أعرض من اللوحة فيبقى الفراغ فيها.
const cells = [];
for (let r = 0; r < rows; r++) {
  const slice = files.slice(r * cols, r * cols + cols);
  const blockW = slice.length * cellW + (slice.length - 1) * gap;
  const x0 = pad + Math.round((innerW - blockW) / 2);
  slice.forEach((file, c) => {
    cells.push({ file, x: x0 + c * (cellW + gap), y: pad + r * (cellH + gap), w: cellW, h: cellH });
  });
}

const outPath = path.resolve(out);
fs.mkdirSync(path.dirname(outPath), { recursive: true });
const tmp = fs.mkdtempSync(path.join(os.tmpdir(), 'board-'));
const planFile = path.join(tmp, 'plan.json');
const psFile = path.join(tmp, 'tile.ps1');
const format = /\.jpe?g$/i.test(outPath) ? 'jpg' : 'png';
fs.writeFileSync(planFile, JSON.stringify({ width, height: canvasH, bg, format, out: outPath, cells }));
fs.writeFileSync(psFile, PS);
try {
  execFileSync('powershell', ['-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', psFile, '-PlanFile', planFile],
    { stdio: ['ignore', 'pipe', 'pipe'], timeout: 180000, maxBuffer: 8 * 1024 * 1024 });
} catch (error) {
  console.error(JSON.stringify({
    ok: false,
    reason: 'compositing-failed',
    detail: String(error.stderr || error.message).slice(-600),
  }, null, 2));
  process.exit(1);
} finally {
  fs.rmSync(tmp, { recursive: true, force: true });
}

const bytes = fs.existsSync(outPath) ? fs.statSync(outPath).size : 0;
console.log(JSON.stringify({
  ok: bytes > 0,
  out: outPath,
  bytes,
  layout: `${cols}x${rows}`,
  canvas: `${width}x${canvasH}`,
  heightRequested: height,
  // عرض الخلية يختلف بين الصفوف الآن (الصف الأخير يملأ عرضه)، فتُدرج العروض الفعلية.
  cells: cells.map((c) => `${c.w}x${c.h}@${c.x},${c.y}`),
  panels: files.map((f) => path.basename(f)),
}, null, 2));
process.exit(bytes > 0 ? 0 : 1);
