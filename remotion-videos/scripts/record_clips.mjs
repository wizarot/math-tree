// 录制数学天赋星图真实交互操作录屏：C0-C8 九段，输出 public/assets/clips/Cx.mp4
import { chromium } from 'playwright-core';
import { fileURLToPath } from 'url';
import { execSync } from 'child_process';
import path from 'path';
import fs from 'fs';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const EDGE = 'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe';
const BASE = 'http://127.0.0.1:8000';
const CLIPS = path.resolve(__dirname, '../public/assets/clips');
const FFMPEG = 'C:\\Program Files (x86)\\Captura\\ffmpeg-5.0.1-essentials_build\\bin\\ffmpeg.exe';
fs.mkdirSync(CLIPS, { recursive: true });

// 选一个家长熟悉、且在中国课标内的核心演示节点
const raw = JSON.parse(fs.readFileSync(path.resolve(__dirname, '../../data/math-topics.json'), 'utf-8'));
const arr = Array.isArray(raw) ? raw : (raw.topics || []);
const target =
  arr.find(t => t.name_zh === '20 以内加减法') ||
  arr.find(t => t.name_zh === '等值分数') ||
  arr.find(t => t.inChineseCurriculum) ||
  arr[0];
const TID = target.id;
console.log('TARGET node =>', TID, '|', target.name_zh || target.name);

const browser = await chromium.launch({
  executablePath: EDGE,
  headless: true,
  args: ['--no-sandbox', '--disable-gpu', '--force-device-scale-factor=1', '--disable-dev-shm-usage'],
});

const sleep = (page, ms) => page.waitForTimeout(ms);

async function record(name, fn) {
  const ctx = await browser.newContext({
    viewport: { width: 1920, height: 1080 },
    deviceScaleFactor: 1,
    recordVideo: { dir: CLIPS, size: { width: 1920, height: 1080 } },
  });
  const page = await ctx.newPage();
  // 每次导航前清空进度，保证从干净“未点亮”状态演示
  await page.addInitScript(() => { try { localStorage.removeItem('mathtree.learned.v1'); } catch (e) {} });
  await fn(page);
  const vp = await page.video().path();
  await ctx.close();
  const out = path.join(CLIPS, name + '.mp4');
  try {
    execSync(`"${FFMPEG}" -y -i "${vp}" -c:v libx264 -pix_fmt yuv420p -crf 18 -an "${out}"`, { stdio: 'inherit' });
    fs.unlinkSync(vp);
    const dur = execSync(`"${FFMPEG}" -hide_banner -i "${out}" 2>&1 | grep -i duration`).toString();
    console.log(`RECORDED ${name}.mp4  ${dur.trim().replace(/\r?\n/g, ' ')}`);
  } catch (e) {
    console.log(`WARN ${name} transcode failed, kept raw: ${vp}`);
  }
}

// 工具：选中并真实点击画面中心的节点
async function focusAndClickNode(page, id) {
  await page.evaluate(i => selectNode(i), id);
  await sleep(page, 1000); // centerOn 动画
  await page.mouse.move(960, 540, { steps: 30 });
  await page.mouse.click(960, 540);
  await sleep(page, 800);
}

// C0 全景：拖拽平移 + 滚轮缩放 + 适应屏幕
await record('C0', async (page) => {
  await page.goto(BASE + '/', { waitUntil: 'networkidle', timeout: 30000 });
  await sleep(page, 3500);
  await page.mouse.move(960, 540, { steps: 20 });
  await page.mouse.down();
  await page.mouse.move(720, 420, { steps: 25 });
  await page.mouse.move(1180, 700, { steps: 25 });
  await page.mouse.up();
  await sleep(page, 600);
  await page.mouse.move(960, 540);
  await page.mouse.wheel(0, -320); await sleep(page, 350);
  await page.mouse.wheel(0, -320); await sleep(page, 350);
  await page.mouse.wheel(0, -260); await sleep(page, 350);
  await page.mouse.wheel(0, 900); await sleep(page, 500); // 缩回
  await page.click('#btn-fit').catch(() => {});
  await sleep(page, 1200);
});

// C1 点击节点：弹出详情 + 前序/后续可点击
await record('C1', async (page) => {
  await page.goto(BASE + '/', { waitUntil: 'networkidle', timeout: 30000 });
  await sleep(page, 3500);
  await page.mouse.move(600, 400, { steps: 20 });
  await page.mouse.move(1200, 700, { steps: 20 });
  await focusAndClickNode(page, TID);
  // 点前序里第一项，演示“顺着链路追”
  await page.locator('#p-pre .item, #p-pre li, #p-pre [data-id]').first().click({ timeout: 3000 }).catch(() => {});
  await sleep(page, 1200);
});

// C2 中国课标过滤
await record('C2', async (page) => {
  await page.goto(BASE + '/', { waitUntil: 'networkidle', timeout: 30000 });
  await sleep(page, 3500);
  await page.click('#cur-chips [data-cur="cn"]').catch(() => {});
  await sleep(page, 1400);
  await page.click('#cur-chips [data-cur="cn"]').catch(() => {}); // 取消
  await sleep(page, 1000);
});

// C3 领域 + 年龄过滤
await record('C3', async (page) => {
  await page.goto(BASE + '/', { waitUntil: 'networkidle', timeout: 30000 });
  await sleep(page, 3500);
  const dom = await page.evaluate(() => { const s = document.querySelector('#sel-domain'); return s ? s.options[1]?.value : null; });
  if (dom) { await page.selectOption('#sel-domain', dom); await sleep(page, 1200); }
  await page.locator('#age-chips .chip', { hasText: '7-9' }).click({ timeout: 3000 }).catch(() => {});
  await sleep(page, 1400);
  // 复位
  if (dom) { await page.selectOption('#sel-domain', { index: 0 }); }
  await page.locator('#age-chips .chip', { hasText: '全部' }).click({ timeout: 3000 }).catch(() => {});
  await sleep(page, 900);
});

// C4 点亮节点 + 点亮前序演示“解锁”
await record('C4', async (page) => {
  await page.goto(BASE + '/', { waitUntil: 'networkidle', timeout: 30000 });
  await sleep(page, 3500);
  await focusAndClickNode(page, TID);
  await page.click('#p-master').catch(() => {});
  await sleep(page, 1500);
  // 点亮一个前序节点
  await page.locator('#p-pre .item, #p-pre li, #p-pre [data-id]').first().click({ timeout: 3000 }).catch(() => {});
  await sleep(page, 1200);
  await page.click('#p-master').catch(() => {});
  await sleep(page, 1500);
});

// C5 依赖高亮：聚焦模式邻居流动虚线
await record('C5', async (page) => {
  await page.goto(BASE + '/', { waitUntil: 'networkidle', timeout: 30000 });
  await sleep(page, 3500);
  await focusAndClickNode(page, TID);
  await page.click('#toggle-flow').catch(() => {}); // 确保流动开
  await sleep(page, 1800);
  // 在面板里 hover 前序/后续强调
  await page.locator('#p-post .item, #p-post li, #p-post [data-id]').first().hover({ timeout: 3000 }).catch(() => {});
  await sleep(page, 1200);
});

// C6 切换有序视图
await record('C6', async (page) => {
  await page.goto(BASE + '/', { waitUntil: 'networkidle', timeout: 30000 });
  await sleep(page, 3500);
  await page.click('#btn-ordered').catch(() => {});
  await sleep(page, 4000); // 有序页加载
  await page.mouse.move(960, 540);
  await page.mouse.wheel(0, -320); await sleep(page, 350);
  await page.mouse.wheel(0, -320); await sleep(page, 400);
  await page.mouse.wheel(0, 700); await sleep(page, 500);
  await page.click('#btn-fit').catch(() => {});
  await sleep(page, 1200);
});

// C7 有序页操作：点击节点 + 领域过滤 + 课标过滤 + 点亮 + 返回星图
await record('C7', async (page) => {
  await page.goto(BASE + '/index.ordered.html', { waitUntil: 'networkidle', timeout: 30000 });
  await sleep(page, 4000);
  await page.locator('.node').first().click({ timeout: 4000 }).catch(() => {});
  await sleep(page, 1200);
  const dom = await page.evaluate(() => { const s = document.querySelector('#domain-select'); return s ? s.options[1]?.value : null; });
  if (dom) { await page.selectOption('#domain-select', dom); await sleep(page, 1000); }
  await page.click('#cur-chips [data-cur="cn"]').catch(() => {});
  await sleep(page, 1200);
  await page.click('#d-master').catch(() => {});
  await sleep(page, 1400);
  await page.click('#btn-galaxy').catch(() => {});
  await sleep(page, 2500);
});

// C8 控件总览（快剪）
await record('C8', async (page) => {
  await page.goto(BASE + '/', { waitUntil: 'networkidle', timeout: 30000 });
  await sleep(page, 3500);
  await page.click('#search').catch(() => {});
  await page.type('#search', '分数', { delay: 90 }); await sleep(page, 1100);
  await page.fill('#search', ''); await sleep(page, 500);
  await page.click('#toggle-lines').catch(() => {}); await sleep(page, 600);
  await page.click('#toggle-lines').catch(() => {}); await sleep(page, 400);
  await page.click('#toggle-flow').catch(() => {}); await sleep(page, 500);
  await page.click('#toggle-labels').catch(() => {}); await sleep(page, 500);
  await page.click('#toggle-labels').catch(() => {}); await sleep(page, 400);
  await page.locator('#legend-list .item').first().click({ timeout: 3000 }).catch(() => {}); await sleep(page, 900);
  await page.locator('#legend-list .item').first().click({ timeout: 3000 }).catch(() => {}); await sleep(page, 400);
  await page.click('#btn-reset').catch(() => {}); await sleep(page, 600);
  await page.locator('#confirmDlg').getByText(/确认|确定|是|清空|重置/).click({ timeout: 3000 }).catch(() => {});
  await sleep(page, 900);
});

await browser.close();
console.log('ALL_CLIPS_DONE');
