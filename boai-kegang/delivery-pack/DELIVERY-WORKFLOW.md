# 课纲交付流程

## 手机

按根目录[MOBILE-WORKFLOW.md](../MOBILE-WORKFLOW.md)操作：手机AI读取同源加载包并写稿，GitHub表单接收完整Markdown，Actions生成Word和PDF下载包。无需本地Word或电脑开机。

## 电脑

安装依赖 `pip install -r delivery-pack/requirements.txt`。

生成Word：

```bash
python delivery-pack/scripts/课纲排版toWord带图版.py --input "课纲.md"
```

客户名称使用输出目录承载，文件名使用 Markdown H1 的完整文字；生成后必须执行 `scripts/validate_title_sync.py`，校验 Markdown H1、Word 首页标题、Word 属性 Title 与 Word/PDF 文件名一致后，才能交付。

模板为同目录的“课纲模板.docx”，由用户认可样稿去除客户正文、缩略图与个人元数据派生；保留样式、主题和编号。图片均与仓库已有公开素材逐字节核对。

本地PDF助手仍支持已安装Word的环境：

```bash
python delivery-pack/scripts/docx_to_pdf.py --input "课纲_带图.docx"
```

若Word启动失败，不把本地导出能力当作移动流程依赖；直接使用云端排版。云端Linux使用requirements-cloud.txt、LibreOffice和Noto中文字体，不依赖Windows COM。

## 一致性与检查

同一份MD＋Skill＋模板生成Word，再统一导出PDF。正式跨设备成品以GitHub云端同一次运行的PDF为准：手机和电脑都下载这一个文件，不能分别导出再比较。本地Word/PDF仅作编辑与预检；Word阅读模式可能重排。

正式交付前检查全部页面；修改内容或版式后重新渲染。清单与规则见根目录CHECKLIST.md。下载包内`render-result.json`会记录Skill版本、Git提交、源稿、模板、主排版脚本、整套排版资源、Word与PDF的SHA256，以及章节、表格、图片和逐页空白检查。清单仅用于内部校验，不写进客户正文。
