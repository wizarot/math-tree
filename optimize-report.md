# 数学天赋星图 · 加载速度优化报告

> 日期：2026-08-18 ｜ 范围：`index.html`（星图主页）及部署资源

## 一、诊断结论

上线后加载慢由两个原因叠加导致：

| 症结 | 具体表现 |
|------|----------|
| **图片清晰度严重超标** | `compass/node/nodec/left` 四张 PNG 源尺寸 2048² / 1184×3588，但页面实际绘制仅 10–136px，解码即浪费 ~22MB 带宽与内存 |
| **一次性加载** | 启动时把 `mtf-sprite.svg` 的 702 个符号各栅格化成 4 种颜色 = **2808 次画布操作**全部同步发起，阻塞首屏 CPU |

此外仓库里有一批**完全未被任何页面引用**的死重图片/字体（items、node1、node2、Gemini 大图、mtf 字体族等，约 31MB+），虽不进首屏请求，但会随部署包一起上传、浪费存储与构建时间。

## 二、已执行的优化

### 1. 图片减肥（按实际显示尺寸等比缩小 + LANCZOS 重压缩）
原地覆盖，覆盖前原图备份至 `bak/heavy_originals/`。

| 文件 | 源尺寸 | 优化后 | 体积变化 |
|------|--------|--------|----------|
| `assets/compass.png` | 2048×2048 | 1024×1024 | 3346 KB → **1000 KB** |
| `assets/node.png` | 2048×2048 | 128×128 | 5249 KB → **30 KB** |
| `assets/nodec.png` | 2048×2048 | 128×128 | 5018 KB → **36 KB** |
| `assets/left.png` | 1184×3588 | 512×1552 | 7852 KB → **1076 KB** |

### 2. 死重移出（可逆）
确认未被引用后，移出 `assets/` 至 `unused-assets/`：
`items.png`、`node1.png`、`node2.png`、`Gemini_Generated_*.png`、`mtf.ttf/.woff/.woff2`、`mtf-font.css`、`mtf-icons.css`、`mtf-codepoints.json`（合计约 31.6MB）。
> 这些文件未从首屏请求链路移除性能，但清理后让 `assets/` 只剩 9 个真正被使用的文件，部署更干净。

### 3. SVG 符号改为懒加载 / 分批栅格化（`index.html`）
- 废弃启动时一次性 `loadSymbols()`（702×4 栅格化）。
- 新增 `ensureSymbol(id)`：仅在**节点进入可见区域**时才发起该符号的栅格化，随视角/缩放逐步加载。
- `mtf-sprite.svg` 文本也延迟到首次需要时再 `fetch`，不再阻塞首屏。
- 渲染坐标、配色（紫/白/青/灰四态）、viewBox `0 0 64 64` 完全保持不变，**视觉零差异**，只是符号会随浏览"按需浮现"。

### 4. 数据 JSON 瘦身（`data/math-topics.json`）
剔除实时渲染未使用的 `standards / source / inDegree / outDegree` 四个字段（共 2808 条），原文件备份至 `bak/math-topics.orig.json`：
917 KB → **741 KB**（省 176 KB），702 条数据完好。

## 三、体积对比（首屏关键资源）

| 项目 | 优化前 | 优化后 |
|------|--------|--------|
| 四大 PNG | ~21.4 MB | ~2.1 MB |
| `math-topics.json` | 917 KB | 741 KB |
| `mtf-sprite.svg` + `math-dependencies.json` | ~792 KB | ~792 KB（结构未动） |
| **合计关键传输量** | **≈ 23.2 MB** | **≈ 3.8 MB（↓约 84%）** |

> **修订（2026-08-18）**：compass 最初压到 256 在 2x 屏（绘制 136px→272 设备像素）显糊，已**回滚后以原图重压到 1024×1024（1000KB）**。中心罗盘为焦点元素且有精细刻度文字，1024 对 136px@2x 有 3.7x 超采样余量，清晰度足够；体积仍比原始 3346KB 小 3.3x。原始 2048 大图保留在 `bak/heavy_originals/compass.png`，如需极致清晰度可直接恢复。

## 四、验证结果
- Node 语法检查：`index.html` 内联脚本 `SYNTAX_OK`。
- 本地 `http.server:8000` 核对：所有关键资源 HTTP 200，减肥后文件就位；移出的 `assets/items.png` 返回 404（确认清理生效）。
- 懒加载正则：对 sprite 中 702 个符号均可正确抽取；`ensureSymbol` 占位幂等逻辑正确。

## 五、后续建议（可选）
1. **开启服务端 gzip/brotli**：`mtf-sprite.svg`(559KB)、`math-topics.json`(741KB) 文本类资源开启压缩后线上体积可再降 60–70%。
2. **部署时排除 `unused-assets/`**：该目录不进首屏请求，但建议从发布包剔除，避免无意义上传。
3. `left.png` 若想再压，可降到 384 宽（≈600KB），但侧边栏金边细节会更软，按观感取舍。

## 六、回滚方式
- 图片原图：`bak/heavy_originals/`；JSON 原文件：`bak/math-topics.orig.json`。
- 移出的死重：`unused-assets/` → 移回 `assets/` 即可。
- 代码：`index.html` 的符号加载改动可用 `git diff` 审查，必要时 `git checkout`。
