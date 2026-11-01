# 录音来源与课程定位

## 首次互动

1. 来源：手动上传／Get笔记API／其他API。
2. API已有连接则优先核对，缺连接时询问接口名称或文档入口，不索取聊天中的明文密码。
3. 首次最小只读请求成功后保存非敏感偏好；不改录音、不删笔记、不归档、不添加标签。
4. 用户指定课程目标后进入定位与复盘；偏好不是访问任意账号或上传文件的许可。

包外profile示例（示例不是作者账号默认值）：

```json
{
  "source_mode": "api",
  "provider": "getnote",
  "client_id_env": "GETNOTE_CLIENT_ID",
  "api_key_env": "GETNOTE_API_KEY"
}
```

手动方式仅需 `{"source_mode":"manual"}`。特定用户的安全调用器和服务别名只在其包外profile保存，不带入发行包。新增或覆盖偏好应来自用户确认；切换来源不删除历史录音。

## Get笔记只读适配

优先使用已授权的Get笔记连接器；无连接器时可调用 `scripts/getnote_readonly.py`。凭据仅由目标进程读取指定环境变量，不读取磁盘凭据，不枚举其他环境变量，也不输出密钥。脚本只访问固定Get笔记域名，拒绝重定向，避免鉴权头被带往其他域名。

以当前Get笔记接口与响应结构为准：

- 域名：`https://openapi.biji.com/open/api/v1`。
- 凭据：`X-Client-ID`与`Authorization`，后者为接口密钥原值，不自行加Bearer。
- 列表：`GET /resource/note/list`；按`has_more`、`next_cursor`/`cursor`分页，保留是否完整及页数。最多扫描页数后仍有下一页须标记不完整。
- 详情：`GET /resource/note/detail?id=...`，笔记在`data.note`。编号全程用字符串，不转为JavaScript Number。
- 观察到的成功信封为`success:true`；不能只看HTTP 200。错误信息只输出状态分类与HTTP码，不转储原始响应或请求头。
- 已有适配记录的内容路径：`note.audio.original`为转写原文、`note.content`为AI摘要、`note.chapter_timeline.items`为章节；`attachments[].duration`的单位按实际接口核实。字段缺失、格式变化时先检查结构，不能将摘要冒充原文。

```text
python scripts/getnote_readonly.py check
python scripts/getnote_readonly.py search --query 数据分析 --start-date 2026-10-01 --end-date 2026-10-31
python scripts/getnote_readonly.py detail --note-id <选中的编号> --output <包外项目目录>/source-note.json
```

如果安全调用器使用自定义环境变量名称，追加 `--client-id-env <变量名> --key-env <变量名>`；参数中不得填凭据值。输出文件必须在本次客户/课程项目内，不放公开Skill目录，已有文件不覆盖。

列表仅用于定位；搜索不匹配时可依据别名再查一次。发生401/403时说明登录或权限缺口，不反复请求；429或网络错误保留状态，按明确重试策略处理，不循环全库。脚本不提供自动刷新、写笔记或后台监听。

## 复盘证据与交付

最终报告开头写明课程、录制日期、所分析篇章、材料类型与缺失。全课和局部复盘分别标注。原稿、平台摘要与分析结果分文件保存。

读取 `boai-course-value` 后，输出价值观校对、3—5项关键结论、可复用案例候选与最多3项优先改进。每项能回到原文段落或时间锚点；学员效果依赖作品证据，不能用平台AI摘要或讲师自评替代。

首次联调的成功标准是：连接验证、唯一课程定位、详情读取、篇章核对、价值观校对、报告全部完成。只有check成功时，只能称“API连通”，不能称“课程自动分析已跑通”。
