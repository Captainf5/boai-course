# 卡通小人概念页规范（页型B · 默认推荐）

已定稿样本：`assets/style-ref/concept-map-sample.png`（AI核心概念关系图）、`assets/style-ref/ocr-machine-sample.png`（OCR机器页）、`assets/style-ref/sketch-machine-sample.png`（**B2 手绘风官方参照**，2026-10-05 用户供图"图2"）。boai-ppt 并入参照（2026-10-12）：`compact-01.png`、`compact-03.png`（紧凑构图实例）、`handdrawn-01.png`、`style-reference.jpg`（ian 手绘风源参照，MIT 许可见 LICENSE-ian.txt）。**最新用户供图优先于一切内置参照。**

## 0. 构思方法：认知锚点 → 物理隐喻（源自 boai-ppt，写 prompt 前必走）

1. 先写清本页的**认知锚点**（学员听完应记住的那一个判断），再用恰当物理关系解释。例：权限是闸门，Context是材料漏斗，Skill是可替换规则组件——这些只是教学比喻，**物理隐喻不能冒充真实技术架构**。
2. 再想**输入/处理/输出**：道具的位置和连接即概念的数据流；人物只在确实参与解释时安排动作（递交/审核/扳闸/验收），不做贴纸装饰。
3. 标签贴近对应道具，避免"左侧人物贴纸+右侧重复文字"两张皮。
4. 白板、文件、齿轮、闸门、轨道等随概念选择，**不重复同一机器**；内容适合白板或分镜时变化构图。
5. 现成构图直接挑：`references/handdrawn-scenes.md`（河北移动课10页实例：OCR/Agent/Skill/自动化/选型等主题速查）。

## 1. 讲师IP（锁定，不可换）

**BOBO**（官方名字，2026-10-05 用户在河北移动课纲中命名）= 红衣 + 戴眼镜 + 黑发男孩，Q版/可爱比例，表情自信亲切，手持教鞭或指向内容。所有课程、所有概念页沿用同一形象，形成品牌识别。

ImageGen 角色描述（直接复用）：
> A cute chibi cartoon boy with black hair and round glasses, wearing a red shirt/jacket and dark pants, confident friendly smile, holding a pointer stick. Flat vector illustration style, clean white background.

## 2. 两种已验证变体（**B2 为用户当前钦定默认**，2026-10-05"都改成图2这种的"）

### B2 手绘 sketchnote 风（默认，用户钦定）
参照 sketch-machine-sample：
- **黑色手绘线稿为主，无彩色填充**；红色仅用于小人领带/关键标注，**橙色手绘弯箭头**表流程/迭代，**蓝色手写体批注**做补充说明
- BOBO 手绘形态：白衬衫+红领带+黑乱发+圆眼镜（与 B1 红衣形态是同一 IP 的两种画风，不冲突）
- 拟物隐喻（机器=框架、流水线=流程），checklist 打勾、回环箭头表迭代
- 实测 prompt 风格块（14 页量产验证）：
  > Hand-drawn sketchnote doodle illustration, pure white background only, floating elements, no scenery. Black ink outlines only, no color fills. Red ink accents on the character's tie and key labels. Orange hand-drawn curved arrows showing flow. Blue handwritten annotation notes. Character: cute hand-drawn cartoon boy with black messy hair, round glasses, white shirt with red tie.
- 中文标签仍写全逐个核对；签名/日期类手写字易出戏（出现过 "小明 2023.12"），prompt 加 "no signature, no date" 更稳
- **墨色两种规格**（2026-10-12 合并 boai-ppt 规则）：默认 = 黑线稿+红（领带/标注）+橙箭头+**蓝批注**（sketch-machine-sample 系）；若用户给 compact/handdrawn 系参考图，则**严格黑红橙三色**，脸和手白底黑线，禁肤色、腮红、大眼高光、蓝绿紫黄填色和金属渲染。拿不准就问用户一句或按最新参考图走。

### B1 信息图插画风（旧默认，已被 B2 取代，仅用户点名时用）
参照 concept-map-sample：
- 白底，红色 `#E8443A` 为主强调色，黑灰辅助
- 结构：**标题（黑粗体+红色下划线）→ 副标题一句 → 中央流程/关系图 → 右侧「一句话理解」卡片 → 底部浅红底金句横幅**
- 小人站左侧做引导位，带对话框气泡
- 节点用圆角卡片+小图标，虚线/实线箭头连接
- 中文标签清晰可读，字不要太小

## 3. ImageGen prompt 模板

```
Flat vector infographic illustration, white background, 16:9.
Main accent color red (#E8443A), black and gray supporting.
[B2变体换：Black-and-white hand-drawn sketchnote style with orange accent arrows.]
Character: a cute chibi cartoon boy with black hair, round glasses, red jacket,
holding a pointer, standing at the left side with a speech bubble saying "[气泡文案]".
Scene: [用一句话描述概念机制，如 "a machine labeled OCR with three input trays
marked 材料/样例/产出, gears inside, outputting documents to a result tray"].
Layout: flow from left to right, rounded cards with small icons, dashed arrows,
Chinese labels: [列出图中需要的全部中文文案，逐个写清楚].
Bottom: a light-red rounded banner with the Chinese sentence "[底部金句]".
Style: clean, minimal, presentation-slide quality, high readability.
```

负面约束（写进 prompt 或自行把关）：
- 不要照片写实风、不要 3D 渲染、不要复杂渐变背景
- 不要出现页码、不要出现英文装饰文字（除 Embrace AI 由 DSL 画）
- **必须写：no signature, no date, no watermark, no page numbers**（B2 手绘风极易自作主张加签名/日期/角标，2026-10-05 实测 P03 出"小明 2023.12"、P06 出"2018.11.18 PM 10:30"、P15 出蓝色签名）
- 中文必须准确——prompt 里把每个中文标签写全，生成后逐字核对，错字就重抽（或图改图定点修，见 §8）

## 4. 嵌入页面

- 插图放主体区（left≈40, top≈120, width≈1010），右侧留竖排英文位置
- 标题、左侧红条、竖排英文、页脚仍用 DSL 绘制——**插图不包标题**，保证整本模板骨架统一
- 生成比例 16:9 或按主体区 1010×520 约 2:1

## 5. 生成后检查清单

1. 小人形象按变体核对：B1=红衣+戴眼镜+黑发；B2=白衬衫+红领带+黑乱发+圆眼镜（对比 style-ref）
2. 所有中文标签无错字
3. 主色是红（B2 允许橙），无第二个主色
4. 无页码、无水印、无乱入英文
5. 金句横幅文案与用户确认的一致

## 6. ImageGen 量产踩坑（2026-10-05 实测）

1. **并行生图同名覆盖**：ImageGen 输出文件名只精确到秒（`...T10-11-25.png`），同一秒返回的多张图互相覆盖。→ **批量生图必须串行**；若并行，每批后立即 `ls` 核对文件数，缺的补生成。
2. **返回顺序 ≠ prompt 顺序**：必须逐张 Read 按内容重命名（pXX.png），禁止按时间戳盲映射。
3. **背景失控**：prompt 写 "white background" 仍可能出教室/绿植场景。加 "pure white background only, floating elements on white, no scenery, no wall" 才稳。
4. **序号错乱**：图内编号卡片（1-5）容易张冠李戴，prompt 里写 "numbered strictly in this exact order: 1.x, 2.y..."，生成后重点核对序号。
5. **角标水印**：部分图右下带 "AI生成 WORKBUDDY" 小水印，白底上不显眼可接受；显眼时换 seed 重抽。
6. size 用 `1536x1024`（3:2），quality 用 `high`（中文标签准确率明显更高），单张约 5-10 credits。

## 7. 嵌入大坑（2026-10-05 用户反馈"图片显示不全"后实测定位）

1. **`<Image objectFit:'contain'>` 不生效，被当 cover 处理**：转换器会写 `<a:srcRect t/b>` 按盒子比例裁切图。盒子 940×482（1.95:1）配 3:2 插图 = 上下各被裁 11.5%，图内标题/金句横幅直接被砍掉。
   → **必须显式给精确比例尺寸**：按图实际宽高比算 `width/height`（区域限高则 height=区域高、width=height×ratio），不写 objectFit。
2. **插图先裁白边再排版**：ImageGen 出图自带白边，PIL `ImageChops.difference` 裁掉（阈值 245），内容有效面积更大、字更显。
3. **PNG 转 JPG q88**：1.8MB→约250KB，14 张图 deck 减重约 20MB，本地编辑器打开明显更快。平涂插画 JPG 无损感。
4. 批量重生成 .slide 时**别用 Python str.format() 填 JSX 模板**（`{{}}` 转义坑），用 `__TOKEN__` + `str.replace()`。
5. 修复后验证嵌入参数：解包 pptx 查 `<a:srcRect>` 应为 `l=0 t=0 r=0 b=0`（或不存在），`<a:ext>` 比例应等于图比例。

## 8. 出图后修补术（2026-10-05 用户验收后补，比重抽省钱）

1. **灰底→纯白**：ImageGen 的 "white background" 常出浅灰纸纹底。PIL 批量白化：像素 `min(RGB)≥208 且 max-min≤32` → 纯 white。彩色墨迹（红/橙/蓝饱和色）与黑线稿不受影响；浅灰铅笔阴影会被抹掉（可接受，画面更干净）。脚本样板：项目 `whiten_fix.py`。
2. **角落签名/日期/水印**：白块覆盖即可（按相对坐标 fill 纯白矩形）。常见位置：右下签名（x0.74-1, y0.89-1）、底部中央日期、左下签名、右下 "AI生成 WORKBUDDY" 水印（x0.88-1, y0.90-1）。覆盖前 Read 确认该角落无正文。
3. **图中部错字**：用 ImageGen **图改图模式**（image1=当前图，input_fidelity=high），prompt 写"Fix exactly N Chinese typos, keep everything else pixel-identical: 错→对 列表"。比重抽省且构图零风险。
4. 修完**保持原像素尺寸**（1536×1024），.slide 盒子不用重算，直接 re-upsert 即可。
