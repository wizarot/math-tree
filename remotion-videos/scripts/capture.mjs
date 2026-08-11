import { chromium } from 'playwright-core';
import { fileURLToPath } from 'url';
import path from 'path';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const OUT = path.resolve(__dirname, '../public/assets/img');
const EDGE = 'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe';
const BASE = 'http://127.0.0.1:8000';

const browser = await chromium.launch({
  executablePath: EDGE,
  headless: true,
  args: ['--no-sandbox', '--disable-gpu', '--force-device-scale-factor=1', '--disable-dev-shm-usage'],
});

const page = await browser.newPage({
  viewport: { width: 1920, height: 1080 },
  deviceScaleFactor: 1,
});

async function shoot(url, file, waitMs) {
  await page.goto(url, { waitUntil: 'networkidle', timeout: 30000 });
  await page.waitForTimeout(waitMs);
  await page.screenshot({ path: path.join(OUT, file) });
  console.log('captured', file);
}

await shoot(BASE + '/', 'shot-starfield.png', 4500);
await shoot(BASE + '/index.ordered.html', 'shot-ordered.png', 4500);

// a closer crop of the starfield to use as a "detail" shot
await page.goto(BASE + '/', { waitUntil: 'networkidle', timeout: 30000 });
await page.waitForTimeout(3500);
await page.screenshot({ path: path.join(OUT, 'shot-starfield-detail.png'), clip: { x: 360, y: 120, width: 1200, height: 840 } });
console.log('captured shot-starfield-detail.png');

await browser.close();
console.log('ALL_DONE');
