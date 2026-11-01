# 博AI增效课程 Skill 套件

为企业培训提供可分别安装、按任务组合使用的 Skill：从课程理念、课前调研与分析、课纲定制、案例开发、教学数据制作到 PPT 制作。每个目录维护自己的 `SKILL.md`、依赖和验证边界，不把所有规则拼成一个大 Skill。

课程设计七项Skill独立合集。先按下表选择任务，再安装对应完整目录。

**理念 → 调研 → 课纲 → 案例与教学数据 → 教学PPT → 授课复盘**

[版本与验证边界](VERSIONS.md) · [通用工作周报PCR实战案例](examples/weekly-report-pcr.md) · [作者项目主页](https://github.com/Captainf5)

GitHub源码与SkillHub上架分别验收；本页不表示SkillHub已上架。

## 已纳入的 Skill

| Skill | 用途 | 安装入口 |
|---|---|---|
| **boai-course-value · 博AI课程理念** | 课前讨论与课后验收；以用户需求及“三少三多，大展宏图”检查课程方向，重点用于个人课后复盘 | [Skill入口](boai-course-value/SKILL.md) |
| **boai-questionnaire · 课前调研与分析** | 在年度飞书Base为每个客户独立创建学员问卷，每次确认姓名必填；回收后调用归藏PPT并按授权邮件交付 | [Skill入口](boai-questionnaire/SKILL.md) |
| **boai-kegang · 博AI课纲** | 沿用13份课程基线，定制课纲并生成 Word/PDF，保留手机分包与云端排版 | [说明与完整包](boai-kegang/README.md) |
| **boai-ppt · 博AI PPT工作室** | 逐页脚本、博AI品牌版式、PPT制作与批量修改 | [使用说明](boai-ppt/README.md) |
| **boai-showcase · 课程案例制作** | 从业务材料开发学员版、教练版及可核验产物 | [使用说明](boai-showcase/README.md) |
| **boai-zengxiao-data-case · 数据案例制作** | 合成标注为教学模拟的数据、埋点及双版本练习材料 | [使用说明](boai-zengxiao-data-case/README.md) |
| **boai-recording-review · 讲课录音复盘** | 首次确认手动/API来源，定位具体课程与篇章，依据课程价值观复盘、提炼案例与改课；含Get笔记只读适配 | [Skill入口](boai-recording-review/SKILL.md) |

## 独立维护的技能

| 项目 | 范围 |
|---|---|
| 数据分析4.0.1 | 供讲师和学员直接分析数据、学习操作，不纳入课程设计合集。 |
| 提示词优化 | 供讲师和学员优化日常提示词；已有prompt-factory 2.0.0，独立发布，不以旧TODO草稿判断其完成度。 |

讲课录音复盘1.1.0已完成一次真实Get笔记逐字稿复盘；不等于逐秒听审或课堂效果验证。个人来源配置与凭据不随包公开。

## 安装与使用

把想安装的目录链接发给 Agent，例如：

> 请安装本套件中的 boai-kegang，完整保留所需 references、scripts 和 assets，先说明依赖与未验证项。仓库地址：https://github.com/Captainf5/boai-course 。安装前核对依赖，不覆盖我已有的个人配置和业务文件。

也可以下载仓库，将选定的完整目录放入宿主的 Skill 目录。课纲优先使用目录内 README 链接的完整 ZIP；不要只复制 `SKILL.md`。命令安装尚未实测，不提供未经验证的安装命令。

自然语言示例：
- 用 boai-course-value 审阅这份课纲，删减非必要概念与工具，明确团队作品、展示反馈和验收方式。
- 帮我给某甲方做一个课前调研；问卷回收后用 boai-questionnaire 分析、制作归藏PPT并邮件交付。
- 用 boai-kegang，基于现有课程模板定制一天的办公增效课纲。
- 用 boai-ppt，把确认后的逐页脚本制作成博AI红白PPT。
- 用 boai-showcase，根据我提供的业务材料设计学员版和教练版案例。
- 用 boai-zengxiao-data-case，制作明确标注为教学模拟的数据分析练习。

## 依赖与数据边界

套件不要求填写统一 API Key。实际调用模型、图像工具和连接器取决于宿主现有授权；工具可能将用户提交的材料发送到对应服务，应按任务授权和客户数据边界使用。客户原件不随安装包公开。

课纲 Word 排版使用 Python 与 python-docx；云端 PDF 排版依赖 LibreOffice。PPT入口按宿主选择两套已有实现，WorkBuddy实现优先slidep，Codex实现使用宿主演示文稿工具；两者不承诺视觉行为完全等效。数据案例脚本使用 Python、pandas、numpy、openpyxl。详见各目录说明。

问卷Skill单独使用归藏`guizang-ppt-skill`，依赖已授权飞书与邮件能力；公开包不携带个人邮箱、飞书坐标或授权凭据。年度路由、独立项目与结构化分析脚本已测试，真实客户回收→归藏成稿→邮件发送的完整闭环仍需首次客户项目验收。

## 合集边界

本仓库仅维护课程设计、备课和教学复盘相关 Skill。通用 Agent 工具、学员日常数据分析及提示词优化独立维护。归藏 PPT 是问卷分析所调用的外部依赖，与教学课件 boai-ppt 分开。

## 维护与验证

原 `bopai_kegang` 课纲以 `boai-kegang/` 纳入本套件；迁移来源与验收范围见 [MIGRATION.md](MIGRATION.md)。独立旧仓库保留历史，本套件完成云端验证前不宣称旧端点已停用。

仓库源码纳入不等同 SkillHub 上架或真实课堂效果验收。七项均提供完整源码入口；真实运行、跨端效果及外部账号授权以各项说明为准。
