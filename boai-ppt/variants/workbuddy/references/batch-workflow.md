# 批量修改工作流 + lint 踩坑清单

## 标准批量替换流程

```bash
export PATH="/usr/bin:/bin:$PATH"
cd "<项目目录>"

# 1. 干跑确认命中
grep -c "旧值" slides/*.slide | grep -v ":0"

# 2. sed 批量改（可同时多条）
sed -i "s/博派AI/博AI/g" slides/*.slide

# 3. 批量 lint + upsert（见 scripts/batch_upsert.sh，后台执行）
```

## batch_upsert.sh 用法

```bash
bash scripts/batch_upsert.sh "<项目目录>" "<pptx文件名>" <总页数>
# 例：bash scripts/batch_upsert.sh "E:\Workbuddy\WBase\x\进入Agent新时代" "进入Agent新时代.pptx" 64
```

脚本逻辑：逐页 lint → 失败即中断打印页码 → 全过后逐页 `upsert-dsl --page-index` 原位替换 → 写 update_log.txt。

## 五条踩坑（实测）

1. **upsert 必须显式 `--page-index $((10#$i - 1))`**：不加会 append 新页，46页变92页。`10#` 是为了把 "08" 当十进制而非八进制。
2. **40+ 页前台必超时**：用 `run_in_background` + 日志文件，收到 task-notification 后 tail 日志确认 "ALL PAGES UPDATED"。
3. **旋转竖排文字**：lint 按**未旋转**盒子判溢出，盒子必须整体落在画布内（left+width≤1280），靠旋转中心定位。
4. **小圆形数字标**：用 Box 包 Text，别让 Text 设 height+lineHeight（会报 bottom+5px 溢出）。
5. **containment 溢出快速修**：sed 批量调 padding（如 `padding:'24px 28px'` → `'18px 26px'`）。
6. **upsert 偶发瞬态失败**（2026-10-05 实测）：后台循环第一页报 UPSERT FAIL 但无任何错误详情，前台重跑同一页即成功。→ 单页失败先重试一次再排查 DSL。

## 向已有 deck 中间插页（merge 场景）

slidep **没有 insert 语义**（`--page-index` 只能替换或 -1 追加）。向 N 页旧 deck 插入 M 页新页的标准做法：

1. 提取旧 deck 每页标题定锚点：`unzip` 后 `grep -o '<a:t>[^<]*</a:t>' ppt/slides/slideN.xml`。
2. 新页全部 lint 过后 **append** 到 deck 尾部。
3. 用 python zipfile 重写 `ppt/presentation.xml` 的 `<p:sldIdLst>`：按目标顺序重排 `<p:sldId>` 元素（顺序即放映顺序，r:id 不用改）。
4. 重排前 `cp` 备份 pptx；重排后断言总数 = N+M。
参考实现：河北移动2D 项目 `reorder.py`（64+19→83 页实战验证）。

## 改完必做

- 把用户新确认的偏好（颜色值/署名/版式参数）回写 `references/design-tokens.md`——Skill 是事实源，不是聊天记录。
- 用户级偏好（跨课程的）同步写 `~/.workbuddy/MEMORY.md`。

## 备份铁律（2026-10-05 用户指令，跨场景适用）
**每次改 PPT 前必须先留时间戳备份**：`cp deck.pptx deck.bak-YYYYMMDD-HHMMSS.pptx`，备份与 deck 同目录。图片资产批量改动前同样先整批复制到 `assets/orig_<批次名>/`。任何时候用户要回滚都能找到上一版。

## 踩坑 7：新转换器吞拉丁/数字片段（2026-10-08 实证，严重）
- 症状：upsert 后页面里**两端带 ASCII 空格的英文/数字片段整体消失**（`说 AI 话`→说话、`HEARD`、`100 字`→字、`Grill me` 没了）。10-06 运行时重装后的 converter（0.4.4-alpha）有此回归；此前的旧 deck 页面正常。
- 规则：`说AI话`无空格反而正常；纯拉丁整串（`Yes And`/`Markdown / HTML / JSON`）正常；`Temperature：控制发散`（全角冒号贴边）正常。
- **解法（已验证）**：CJK↔拉丁/数字边界的 ASCII 空格换成 NBSP（U+00A0）；`·` `×` `/` 周围空格直接删。样板脚本：河北移动2D 项目 `fix_latin.py`。
- **验收习惯**：upsert 后必跑 runs 抽检——python 读 slide XML 的 `<a:t>`，确认关键词（HEARD/Grill me/Temperature/数字）存活，不要只看 lint ok。

### 踩坑 7 补充（2026-10-12）：吞字范围比预想大
不仅单个拉丁词，**带括号/斜杠的拉丁短语前边界有 ASCII 空格也会被整体吞**：`单一执行者 (The Solo Maker)`→括号整段消失；`豆包 / WorkBuddy`→WorkBuddy 消失。规则统一：CJK 与任何拉丁片段（词/短语/括号）之间的 ASCII 空格一律换 NBSP（U+00A0），`/` 两侧空格直接删。upsert 后必跑关键词 runs 抽检。

### 踩坑 7 再补充（2026-10-17）：`" = "`（等号带空格）整段吞
`BOBO-123 = 练习路径`→ 整段消失；`补数据 = C的燃料`→"补数据的燃料"（` = C`消失）；`讲不清楚 = 没真懂`→整句消失。**`=`、`/`、`·`、`×`、`+` 等 ASCII 符号带两侧空格、夹在 CJK 与拉丁之间时，连同相邻片段一起被吞**。写法统一：删空格（`BOBO-123=练习路径`）或用全角符号（`＝`）。
审计正则升级为（排注释后扫描）：`[\u4e00-\u9fff][ ][A-Za-z0-9]|[A-Za-z0-9][ ][\u4e00-\u9fff]|[\u4e00-\u9fffA-Za-z0-9] [=+×] | [=+×] [\u4e00-\u9fffA-Za-z0-9]`。

### 踩坑 7 三补充（2026-10-19）：`" → "`、`" · "`（带空格）同样整段吞
`共情 → 核实 → 行动`→"共情核实行动"（箭头全消失）；`开聊 · 干活 · 装傻 · 充钱`→"开聊干活装傻充钱"（中点全消失）。**带空格的 → 和 · 也进黑名单**——写 `共情→核实→行动`、`开聊·干活·装傻·充钱`。审计时把 `→`、`·` 两侧空格一并扫。

### 踩坑 8（2026-10-13，最严重）：slidep 保存会毁掉整个存量 deck
`upsert-dsl` 对目标 pptx 是**全量重序列化**，不是局部追加：
1. **旧页文本被重新过一遍转换器**——踩坑 7 的吞拉丁 bug 会施加到 deck 里**所有存量页**（90 页旧版"什么是 Agent"→"什么是"）；
2. **存量媒体全部丢失**——slidep 只保留自己管线产生的媒体（放在非标准 `ppt/slides/media/`），旧页引用的 `ppt/media/` 整个消失，图片页全毁；
3. 实体引用被改写（`&quot;`→`"`）等隐性改写无数。

**铁律：绝不用 slidep 直接 upsert 含有"非本次 slidep 生成页面"的珍贵母版。** 合并新页进母版的唯一安全路径 = **纯 zip 手术**（本项目 `inject_surgery.py` 模板）：
- 新页先用 slidep 做成独立 inject.pptx（自洽）；
- python zipfile 把 inject 的 slide XML/rels/媒体原样搬进母版（slide 重编号、presentation.xml.rels 加 rId、Content_Types 加 Override、sldIdLst 按锚点插入）；
- 母版旧页字节级不动；搬完跑旧页关键词复原核验 + python-pptx 打开校验。
- 图片 rels 里 slidep 写的 `Target="media/imageN.jpg"`（相对 slides/）合法，媒体跟着放 `ppt/slides/media/` 即可。

### 踩坑 7 补充（2026-10-13）：`\u00A0` 转义只在 JS 字符串里有效
- `{"...\u00A0..."}`（双引号 JS 表达式）和数组里的单引号字符串 `'...\u00A0...'` → 转换器会正确解析为 NBSP。
- **但 JSX 纯文本节点里写 `\u00A0` 会原样显示成字面量**（页面上出现 "\u00A0" 六个字符）。
- 铁律：JSX 文本节点里禁止写 `\u00A0`，要么包成 `{"..."}`，要么直接用真 NBSP 字符。**验收加一项**：runs 抽检时全文扫 `u00A0` 字面量，有残留即失败。

### 踩坑 9（2026-10-19 美蓓亚课实证）：乱码/缺字四类与预防铁律
做 PPT 出的"乱码"绝大多数是这四类，对症下药：
1. **吞拉丁字符（最常见）**：中文与英文/数字/符号之间打 ASCII 空格，整段被吞（`P 管问法`→`管问法`、`vs`/`·` 消失）。铁律：中英、中数之间**不留普通空格**（紧贴写，或换全角符号）；`·` `/` `×` `+` `=` 两侧一律不留空格。写完必跑 runs 抽检（解包查 `<a:t>` 关键词），别只看 lint 通过。
2. **方框/豆腐块**：只设 `latin` typeface 缺中文字形 → 中文变 □。对策：`latin`+`ea`+`cs` 三件套都设中文字体（见 design-tokens.md §3）。
3. **不换行溢出（看着像乱排）**：slidep 默认给全 deck 文本框 `wrap="none"`（实测 1783 处/125页），字号一大就横向溢出。对策：正文/表格单元格/提示词卡片改 `wrap="square"`；短标签、角标、竖排英文保留 none。
4. **编码（锟斤拷）**：读写必须全程 UTF-8，python 处理 pptx 显式 `encoding='utf-8'`。
配套字号规范见 design-tokens.md §3（核心观点 ≥14pt、正文 ≥12pt、小字能删则删）。
