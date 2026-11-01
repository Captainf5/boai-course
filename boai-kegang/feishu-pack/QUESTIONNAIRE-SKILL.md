---
name: 问卷接入
description: 从客户问卷结果（飞书表单、多维表导出的 xlsx/csv 等）提取并整理为标准化课纲需求 JSON，供下游课纲设计使用。
---

# 问卷接入 Skill：把飞书问卷导出变成“课纲需求 JSON”

## 何时使用

当用户说“我有问卷/表单/飞书多维表导出，帮我整理需求/生成课纲输入信息”时使用。若用户要新建甲方课前问卷、做完整分析、生成归藏PPT并邮件交付，转交已安装的`boai-questionnaire`；本入口只负责转成课纲需求JSON。直接读取飞书优先复用已授权连接器或lark-cli，从明确的Base/子表坐标读取；不要求在聊天中提供app_secret或访问令牌。

## 目标（输出给下游 Skill）

把问卷结果（xlsx/csv 或粘贴文本）整理成一份**标准化需求 JSON**，用于直接喂给「课纲设计」Skill。

## 输出格式（固定 JSON 骨架）

输出时只要包含这些字段（缺失就留空并列出追问）：

```json
{
  "company": {
    "name": "",
    "industry": "",
    "size": "",
    "business_summary": ""
  },
  "audience": {
    "total_people": null,
    "roles": [],
    "age_range": "",
    "ai_level": "",
    "device": "手机/电脑/混合/未知"
  },
  "training": {
    "duration": "",
    "format": "线下/线上/混合/未知",
    "practice_ratio": "",
    "focus_modules": []
  },
  "constraints": {
    "network": "外网/内网/未知",
    "compliance": "只能国产/可外网/未知",
    "forbidden_tools": [],
    "required_tools": []
  },
  "pain_points": [],
  "expected_outputs": [],
  "notes": ""
}
```

## 工作流（高层）

```
导出文件/粘贴内容 → 字段映射 → 去噪合并（同义项） → 补齐缺失 → 输出 JSON + 追问清单
```

## 参考文件（渐进式披露）

- 字段映射与追问：`WORKFLOW.md`
- 示例：`EXAMPLES.md`
- 可选脚本（解析 xlsx/csv）：`scripts/feishu_export_to_json.py`
- 直接接飞书多维表：`直接接飞书多维表说明.md`（需用户提供飞书应用凭证与表标识）

