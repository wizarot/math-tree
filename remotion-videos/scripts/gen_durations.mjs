// 录制完成后运行：测量 public/assets/clips/*.mp4 时长，写入 clips/durations.json
// 供 durations.ts 计算每幕精确时长（幕时长 = max(配音, 录屏总时长) + pad）
import { execSync } from 'child_process';
import fs from 'fs';
import path from 'path';

const CLIPS = path.resolve('public/assets/clips');
const out = {};
for (const f of fs.readdirSync(CLIPS)) {
  if (!f.endsWith('.mp4')) continue;
  const p = path.join(CLIPS, f);
  let raw = '';
  try {
    execSync(`ffmpeg -hide_banner -i "${p}"`, { stdio: 'pipe' });
  } catch (e) {
    raw = (e.stderr ? e.stderr.toString() : '') + (e.stdout ? e.stdout.toString() : '');
  }
  const m = raw.match(/Duration:\s*(\d+):(\d+):(\d+(?:\.\d+)?)/);
  if (m) {
    const sec = +m[1] * 3600 + +m[2] * 60 + +m[3];
    out[f.replace('.mp4', '')] = +sec.toFixed(2);
  }
}
fs.writeFileSync(path.join(CLIPS, 'durations.json'), JSON.stringify(out, null, 2));
console.log('Wrote clips/durations.json =>', out);
