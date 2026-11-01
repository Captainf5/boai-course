# WORKFLOW：飞书问卷/多维表导出 → 课纲需求 JSON

## 1) 输入来源（优先级）

1. **xlsx/csv 导出文件**（最佳）
2. 从表单后台复制的“汇总文本”
3. 截图/图片（次选，需要先 OCR）

## 2) 字段映射规则（把表单题目映射到 JSON）

> 原则：宁可少映射，也不要“瞎猜”。不确定就进 `notes` 并列出追问。

常见题目 → JSON 字段：
- 公司名称/单位名称 → `company.name`
- 行业/赛道/部门 → `company.industry`
- 学员人数/参训人数 → `audience.total_people`
- 学员岗位/角色 → `audience.roles`（用数组）
- 年龄段 → `audience.age_range`
- AI基础/是否用过AI → `audience.ai_level`
- 设备（手机/电脑）→ `audience.device`
- 课程时长/希望几小时/几天 → `training.duration`
- 形式（线上/线下）→ `training.format`
- 实操比例 → `training.practice_ratio`
- 希望重点（提示词/图片/视频/音乐/工作流/智能体/移动端）→ `training.focus_modules`
- 工具限制（内网/只能国产/禁用）→ `constraints.network`/`constraints.compliance`/`constraints.forbidden_tools`
- 期望产出（作品/模板/方案/工作流）→ `expected_outputs`
- 痛点/困难/最耗时 → `pain_points`

## 3) 去噪与合并（让 JSON 可直接用）

- **同义合并**：如“学员画像/学员情况/参训对象”合并到 `audience`
- **多选题**：保持数组，不要拼成一串
- **开放题**：保留原话，但尽量做 1 句摘要写入 `notes`

## 4) 缺失字段追问清单（输出必须包含）

输出 JSON 之后，列出最多 8 个“关键追问”，优先问：
1. 学员设备（手机/电脑/混合）
2. 外网/内网与工具限制
3. 课程总时长与实操比例
4. 甲方最关心的 3 个场景
5. 希望交付的最终形式（docx/pdf/…）

