# 博AI课纲 Skill

在原有仓库里维护同一套课纲规则、13份当前课程基线、历史母版与排版模板。手机写稿使用同源分包，不降级成简版；电脑和手机查看同一份PDF，分页一致。

[手机使用流程](MOBILE-WORKFLOW.md) · [手机排版入口](https://github.com/Captainf5/boai-course/issues/new?template=course-render.yml) · [云端排版记录与下载](https://github.com/Captainf5/boai-course/actions/workflows/render-course.yml)

## 当前课程产品

- [甲方选课版课程方案与13份完整课纲](outputs/博AI增效-课程销售矩阵.md)：按客户对象、问题、成果、时长和软件选择课程。
- [当前课程包参考基线](references/CURRENT-COURSE-PACK.md)：定制课纲先选最接近的一份当前成稿，历史母版只作补充。
- [AI客服基础Q&A](outputs/博AI增效-课程销售客服Q&A.md)：用于课程咨询、初步选课与转人工判断，价格和生产接入不自动承诺。
- [命名与产品规则](references/COURSE-CATALOG.md)：时长放品牌之后；OPC按独立名称；WorkBuddy两份稿仅改标题与文件名。
- Word/PDF请从实际完成的云端排版运行下载；不提供缺失的旧标题成品链接。

## WorkBuddy正文与上轮排版参考

- 一天版：[完整课纲](outputs/catalog/博AI增效-1D-10倍职场办公_6X畅销版.md)
- 两天版：[完整课纲](outputs/catalog/博AI增效-2D-10倍职场办公_6X畅销版.md)
- 一天版围绕一个岗位任务，练习个性化设置、Skill、连接器、专家团与自动化；两天版保留文档、数据、图文视频、PPT及HTML实操。每章先列关键词，成果统一整理为岗位AI工作台。
- [Skill入口](SKILL.md)、[课程参考体系](references/README.md)、[表达与排版标杆](references/STYLE-BENCHMARK.md)
- [课程研发方法](大展宏图方法论.md)、[交付检查表](CHECKLIST.md)
- [本次实测与验收范围](VERIFICATION.md)：手机与电脑使用同一份固定版式PDF，实际页数与检查结果见记录。

## 手机怎么用

同一Skill支持Codex与WorkBuddy。默认下载[完整便携Skill包](releases/boai-kegang.zip?raw=true)，它包含13份当前课纲、Word模板、7张配图和全部排版脚本；按[双工具与移动端使用说明](CROSS-PLATFORM.md)安装/导入。只写稿的手机入口可使用下面的同源附件，不需要新增办公插件。

1. 下载[手机核心规则包](mobile/博AI课纲-手机核心规则包.md)，再按方向下载[通用办公与管理](mobile/博AI课纲-手机参考包-通用办公与管理.md)、[营销增长与智能体](mobile/博AI课纲-手机参考包-营销增长与智能体.md)或[行业专项](mobile/博AI课纲-手机参考包-行业专项.md)。把两个附件与客户需求一起上传。
2. 让AI按包内规则生成完整Markdown，继续语音或文字修改；确认后复制全文到“手机排版入口”。
3. 在GitHub登录仓库所有者账号提交；打开“云端排版记录与下载”，进入本次运行，在Artifacts下载文件包并解压。固定版式PDF用于查看，Word用于修改。下载包保留7天，及时保存到手机文件。

这是一条不依赖办公室电脑开机的两步AI写稿＋云端排版流程，不是“只填一句需求，GitHub自动调用模型写稿”。没有新增模型API或付费订阅。首次手机AI读取附件和手机浏览器下载体验需在所选客户端确认。

## 电脑怎么用

Codex与WorkBuddy默认都安装[完整Skill包](releases/boai-kegang.zip?raw=true)。[纯写稿精简包](releases/boai-kegang-authoring.zip?raw=true)只在客户端明确拒绝大包、且只需要Markdown时使用；它不含Word模板、图片、Python脚本或本地排版能力。不要只复制SKILL.md。排版命令见[交付流程](delivery-pack/DELIVERY-WORKFLOW.md)，移动分包由脚本生成。

需要跨设备严格一致时，手机和电脑都使用同一次GitHub云端运行生成的固定版式PDF。Word保留编辑用途，不能用不同客户端各自打开或另行转PDF后声称分页一致。下载包中的清单会记录源稿、模板、主排版脚本、Word与PDF的SHA256，且自动拦截纯空白页。

## 公开范围

仓库与Issue公开，只放通用课程与脱敏资料。13份当前课程是默认成稿基线；十份历史母版为通用重编版，不公开客户原稿。历史参考不作为当前定制依据。排版机器人仅有代码读取权限，不自动提交文件或发布消息；push不等于给客户发送消息。

## 配置与迁移边界

独立课纲已迁入本套件 boai-kegang 目录。写稿无需额外API Key；排版依赖见 delivery-pack/requirements-cloud.txt。这里的旧验证记录只描述原仓库；新仓库的云端排版尚待实际运行验证。用户资料默认保持在任务目录，公开Issue只允许提交已确认可公开的内容。
