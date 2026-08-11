# 项目长期笔记：math-skill-tree

## 页面入口与切换
- 主入口：`index.html`（2026-08-10 由 galaxy.html 改名而来，Canvas 星图，性能已优化）。
- 有序视图：`index.ordered.html`（SVG 有序技能河）。
- 互相切换：
  - `index.html` 右上「有序视图」按钮 → `index.ordered.html`
  - `index.ordered.html` 头部「返回星图」按钮 → `index.html`

## 图标来源
- 节点图标统一来自 `assets/mtf-sprite.svg`（702 个 `<symbol>`：503 个 `mt_xxx` 对应 math-topics.json 的 topic id + 199 个 `cn_xxx`）。
- index.html（Canvas）按 topic id 取 `mt_` 符号；index.ordered.html 节点也用 `mt_` 专属符号，未命中回退领域 sigil。

## 数据
- `data/math-topics.json`：702 个知识点（id 形如 `mt_xxx`，含 domain/ageStart/ageEnd/centrality 等）。
- `data/math-dependencies.json`：依赖边（prerequisiteId → topicId）。

## 性能要点（Canvas 大量节点）
- 发光预烘焙 sprite，运行时零 per-frame `shadowBlur`（否则 700+ 节点每帧上千次实时模糊必卡死）。
- 批量连线用实心静线；仅选中节点的邻居边播放流动虚线。

## 本地预览
- 启动：`python -m http.server 8000`（在 D:\projects\math-skill-tree 下）。
- 预览入口（用户指定，记住）：**http://127.0.0.1:8000/index.html**（主入口星图）。
- 有序视图：http://127.0.0.1:8000/index.ordered.html

## 侧边栏背景（items.png 雪碧图用法）
- `#sidebar.glass` 用 `url("assets/items.png") -60px -80px no-repeat` + `background-color #46342B` 抠出 MAIN PANEL TEXTURE (430×460 @ items.png 60,80)。
- **不要预切 sidebar_bg.png**：雪碧图的本意就是整张引用 + background-position。
- 面板带边框不可平铺（上下边缘 RGB 差 128），下沿靠 `background-color` 暗皮革色衔接。
