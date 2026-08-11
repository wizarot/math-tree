// 探针：验证 (1) selectNode 全局可用 (2) recordVideo 能产出 webm (3) 取一个代表性节点 id
import { chromium } from 'playwright-core';
import { fileURLToPath } from 'url';
import path from 'path';
import fs from 'fs';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const EDGE = 'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe';
const BASE = 'http://127.0.0.1:8000';
const CLIPS = path.resolve(__dirname, '../public/assets/clips');
fs.mkdirSync(CLIPS, { recursive: true });

// 挑一个代表性节点：优先"分数"，否则取第一个 inChineseCurriculum 的
const topics = JSON.parse(fs.readFileSync(path.resolve(__dirname, '../../data/math-topics.json'), 'utf-8'));
const arr = Array.isArray(topics) ? topics : (topics.topics || []);
let target = arr.find(t => (t.name_zh || '').includes('分数'));
if (!target) target = arr.find(t => t.inChineseCurriculum);
if (!target) target = arr[0];
const TARGET_ID = target.id;
console.log('TARGET_ID =', TARGET_ID, '| name =', target.name_zh || target.name);

const browser = await chromium.launch({
  executablePath: EDGE,
  headless: true,
  args: ['--no-sandbox', '--disable-gpu', '--force-device-scale-factor=1', '--disable-dev-shm-usage'],
});
const context = await browser.newContext({
  viewport: { width: 1920, height: 1080 },
  deviceScaleFactor: 1,
  recordVideo: { dir: CLIPS, size: { width: 1920, height: 1080 } },
});
const page = await context.newPage();
try {
  await page.goto(BASE + '/', { waitUntil: 'networkidle', timeout: 30000 });
  await page.waitForTimeout(3500);
  // 验证 selectNode 全局可用
  const probe = await page.evaluate((id) => {
    const hasFn = typeof selectNode === 'function';
    let ok = false;
    try { selectNode(id); ok = true; } catch (e) { ok = 'err:' + e.message; }
    return { hasFn, ok, hasView: typeof view !== 'undefined' };
  }, TARGET_ID);
  console.log('PROBE selectNode =>', JSON.stringify(probe));
  await page.waitForTimeout(1500);
} catch (e) {
  console.log('ERR', e.message);
}
await context.close();
const files = fs.readdirSync(CLIPS).filter(f => f.endsWith('.webm'));
console.log('WEBM FILES:', files);
console.log('PROBE_DONE');
await browser.close();
