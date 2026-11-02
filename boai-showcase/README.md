# 博AI案例制作 v3.2.1

企业AI培训案例开发 Skill。

目标：把甲方真实业务资料加工成“可学、可练、可验证、可复用”的AI业务案例，而非泛化工具演示。

## 核心链路

**识别案例类型 → 找标的物/对标物 → 定义业务决策 → 资料体检 → 主动索资 → 设计冲突 → 学员版/教练版 → 2~4轮AI操作 → 业务产物 → Skill/自动化/HTML资产化**

## 目录

- `SKILL.md`：主Skill规则
- `templates/`：甲方索资、案例brief、学员版、教练版、PPT Agent等模板
- `scripts/`：确定性机械任务脚本
- `benchmarks/`：黄金测试集与回归测试
- `schemas/`：结构化输入输出Schema
- `examples/`：明确标注的通用教学模拟输入

## 推荐使用方式

1. 简单说一下案例，直接提供现有材料。材料可以是原始对象、对标成品、背景、规则或真实结果，不需要先填表。
2. Skill 先读材料，再按实际缺口追问，通常 1～2 个、最多 3 个；材料用途不明才确认。已有答案不重问，多案例共用信息直接沿用，资料体检和评分默认内部完成。
3. 成熟度低于70分时，默认不进入PPT制作，除非用户明确要求先做教学模拟版。
4. 明确“谁用什么材料，完成什么任务，交出什么”后，先推进切入点或任务卡草案；正式案例按证据条件开发学员版、教练版、提示词等需要的交付，不为收齐全量资料反复盘问。

只有明确要求模板或需向甲方统一收集资料时，才提供 [标准资料收集表](templates/INTAKE_TEMPLATE.md)。

## 脚本

```bash
python scripts/route_case.py examples/demo_brief.json
python scripts/case_maturity.py examples/demo_brief.json
python scripts/profile_tabular.py data.csv
python scripts/scaffold_case.py "案例名称" --type data --out ./cases
python scripts/run_benchmarks.py
```

脚本负责确定性检查；业务判断、冲突设计、教学设计由Skill完成。

### 额外工具

```bash
python scripts/build_client_request.py examples/demo_brief.json
python scripts/validate_package.py .
```

## 安装与配置
完整安装 https://github.com/Captainf5/boai-course/tree/main/boai-showcase 目录。无需额外API Key；脚本使用Python，XLSX读取需openpyxl。外部模型或连接器的数据处理按宿主授权执行。命令安装尚未实测，使用目录安装。

## 兼容性与依赖

需要能够读取材料和执行Python的Agent；基础脚本使用Python 3，XLSX读取需openpyxl。制作PPT或图像时使用宿主实际可用的工具，工具未配置时交付文本材料并说明限制。

## 数据与适用边界

客户原件和单次项目结果不写入Skill。模拟材料必须标注；外部模型或连接器仅在任务授权范围处理数据。本Skill设计教学案例，不直接给真实经营活动下结论，也不保证学员实际掌握率。

## 版本来源

当前为 **3.2.1**，已包含BOBO-showcase V3（包内3.0.0）的核心流程与脚本，并保留后续的简短追问规则。[版本差异与2026-11-02核对记录](SOURCE-VERSION.md)。
