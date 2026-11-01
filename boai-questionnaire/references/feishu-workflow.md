# 飞书年度数据库与客户子表

优先复用已授权lark-cli，读`lark-base`和`lark-shared`及实际命令帮助。下面是已实跑的命令形状；路径参数使用工作目录下相对路径，JSON通过安全的参数数组传入。不要从认证文件提取token。

脚本解析stdout时显式指定JSON格式：`+record-get`及`+record-list`的默认显示格式是Markdown，不能直接`json.loads(stdout)`。少量索引回读加`--format json`；答卷分析用`--format ndjson --output`及manifest。回读格式错误不代表之前的写入失败，恢复时先查已保存的写入回执，避免重复建表或重复登记索引。

## 年度路由

个人配置`annual_bases`按年份保存真实`base_token`、`url`和`index_table_id`；`legacy_index`可保存用户原问卷Base的入口索引坐标。这些只在本机配置，不能写入发布包。

新建项目时按Asia/Shanghai当前年选库。没有该年映射时：先核对现有项目状态/用户指定链接，再用`+base-create --name "博AI调研分析｜年度" --time-zone Asia/Shanghai --table-name "调研项目索引" --fields '<字段JSON>' --as user`创建，立刻保存响应坐标。2027仅在首次新项目时建库，不提前创建、不迁移旧问卷。读取2026旧问卷时始终用原坐标。

用户指定了既有Base就先保存并复用该年映射，不能为了统一命名重新建库。2026约定执行至12月31日；2027首次新建时，先复核2026实际回收中的题目负担、资料缺口与分析可用性，再沿用已确认规则建2027库，具体题目优化根据证据和用户决定进行。2027未建好时不把新项目默默写回2026库。旧客户/班次的问卷、答卷和链接保持原位。私有入口和邮箱仅保存在个人配置与内部约定，不打包进通用Skill。

索引建议文本字段：项目名称、甲方名称、班次编码、年度、问卷类型、填写链接、数据表链接、年度数据库链接、状态、说明。记录一个年度入口，随后每个客户项目各一行。若旧入口已配置，同步写入这两类记录，方便从原来的链接进入。不要往索引放收件邮箱或原始答卷。

按(base_token, index_table_id/table_id)去重索引目标，物理上是同一表就只登记一次；旧入口未配置时无需补建。个人配置变化只影响新项目，恢复旧项目用项目内已保存的云端坐标。

## 创建客户项目

`workflow.py prepare`会输出`project.json`、`questionnaire.md`、`table-fields.json`、`questions.json`。部署步骤：

1. `base +table-create --base-token <年度Base> --name <客户与班次标题> --fields <table-fields.json的数组> --as user`。第一项是主字段，不直接复制旧表中的答案。表名必须能区别客户和班次。
2. `base +form-create --base-token ... --table-id ... --name <客户与班次标题> --description <简短问卷说明> --as user`。客户名放标题，说明只写保密、材料定义与勿提交敏感信息。保存真实table_id和form_id到project.json。
3. `+form-questions-list`读取默认主字段；用`+form-questions-update --questions '[完整问题对象含id]'`按本次用户确认设置姓名的必填/选填及说明，不能一律设为必填。更新是替换语义，保留所需字段。
4. 其余问题按最多10个一批`+form-questions-create --questions '<数组>'`；用`+view-set-visible-fields --view-id <form_id> --json '{"visible_fields":[真实字段ID...]}'`设定顺序。
5. `+form-share-get`先读分享状态，再按用户的发放方式调用`+form-share-update`。每次仅设置一个选项，已验证参数包括`--access-scope anyone`、`--allow-anonymous=true`、`--enabled=true`。遵守租户限制；不改变底层Base的读取权限。
6. 统一回读问题、顺序、分享状态；从API返回获取填写链接，不凭ID拼一个分享token。用分享token调`+form-detail`核对实际标题与问题。条件、附件、必填阻断需客户端试填才可宣称完整验证；试填如创建测试答卷须标记并排除。
7. 向年度索引和已配置的旧索引登记项目。用`+record-upsert --json '<字段映射>'`：不带record-id是创建，不会按业务键自动去重；已存在记录必须传真实`--record-id`更新。将两个索引record_id保存到project.json。

状态字段可追加到project.json：`cloud: {base_token, table_id, form_id, share_url, table_url, index_record_id, legacy_index_record_id, verified_at}`。写入操作成功即记录；如果响应超时/不明，先按唯一项目名称核查云端，不盲目重试建库、建表或写索引。恢复时只补未完成步骤。仅创建了表、没有分享链接时不能标问卷已完成。

题目标题不加人工序号。修改旧卷时优先保留原链接；删去的题目通过可见字段配置隐藏并保留底层数据。题意或类型变化时新建字段，不能把旧“填写角色”的答案改标成姓名。回读实际字段schema，把field_id与底层field_name保存在项目；题目标题可能只是表单别名，不能当作导出列名。

## 读取与回收

从project.json读取准确坐标，不全库扫其他客户。`+field-list`核对版本/字段语义后，`+record-list --field-id <所需字段> ... --format ndjson --output ./records.ndjson --as user`。读取manifest中的`has_more`、offset与记录数；大表继续分页，合并时保留表ID与record_id。只有分页全完且范围准确才称完整回收快照。附件先读清单，再按获准范围读取；不把全部客户原件随报告发出。

读/写错误按真实scope或ACL修复。没有权限搜索标题时，可用用户明确给出的Base坐标读取或按已授权“新建”请求创建，不要求为不必要的全局搜索扩权。CLI或浏览器启动异常不是用户撤销授权。

## 其他部门与模拟验收

部门补充题放在部门选择之后，用visible_rule={"logic":"and","conditions":[["您所在的部门","intersects",["其他"]]]}，required=true。按批创建时保留前序引用。管理端questions-list回读visible_rule；分享端form-detail可能以filter返回，不能因键名不同判定丢失。旧卷改选项先核对已有答卷，避免重标历史水平。

验收至少覆盖：未选其他时隐藏、选其他后显示、空补充内容阻止提交、姓名和附件选填可空、完整模拟提交及CLI回读。模拟答卷注明用途，记录record_id到项目synthetic_record_ids，分析自动排除；仅CLI提交不能声称网页交互校验已通过。
