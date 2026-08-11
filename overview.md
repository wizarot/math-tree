# 60 秒产品解说视频生成完成

## 交付物
- `remotion-videos/output/math-skill-tree.mp4`
  - 分辨率：1920×1080
  - 帧率：30 fps
  - 时长：60.05 秒
  - 格式：H.264 + AAC（立体声 48 kHz）
  - 大小：39.7 MB

## 分镜结构（8 幕，共 60 秒）
1. **开场提问**（0–5s）：“数学，到底该先学什么？”
2. **痛点**（5–14s）：知识点散落、依赖关系不清、不知道从哪开始
3. **产品定位**（14–22s）：数学天赋星图 = 一张能看清脉络的星图
4. **核心规模**（22–30s）：702 个知识点、1002 条依赖边、按领域着色、节点大小代表核心度
5. **交互与依赖**（30–38s）：点击节点，前后置依赖一目了然
6. **有序视图**（38–44s）：按年龄排成“学习之河”
7. **智能筛选**（44–50s）：按领域、按年龄侧边栏一键筛选
8. **行动号召**（50–60s）：打开数学天赋星图，给数学学习一张全局地图

## 关键实现
- 配音：edge-tts `zh-CN-XiaoxiaoNeural` 声线，`+30%` 语速，8 段 MP3。
- 截图素材：Playwright 驱动系统 Edge 无头截取 `127.0.0.1:8000/index.html` 与 `index.ordered.html` 的 1920×1080 实机图。
- 动画：Remotion 组件实现镜头平移/缩放、标题淡入、卡片入场、金蓝色调匹配产品风格。
- 渲染：通过 `@remotion/cli` 直接渲染，1800 帧全部编码成功。

## 后续可选
- 如需修改解说词、语速、或画面镜头，改 `remotion-videos/scripts/generate_audio.py` 和对应 `Scene*.tsx` 后重新运行 `./node_modules/.bin/remotion.cmd render src/index.ts math-skill-tree output/math-skill-tree.mp4`。
