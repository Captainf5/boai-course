# 博AI增效数据案例制作

为培训生成可验证的教学模拟数据、任务卡和老师参考答案，区别于直接分析企业真实经营数据。

## 安装与使用
完整安装 https://github.com/Captainf5/boai-course/tree/main/boai-zengxiao-data-case 目录。示例：“为一天的数据分析课设计同比、环比和异常下探练习，学生版不含答案，老师版包含脚本计算的参考答案。”

## 配置与依赖
无需API Key。脚本运行需要Python、numpy、pandas、openpyxl；先核对依赖，再运行 scripts/gen_dataset_template.py。仅静态检查与本机验证范围有效，不承诺跨平台均已实测。

## 输出与边界
输出学生版与老师版Excel、任务卡和教学讲稿。数据必须标注教学模拟，所有参考答案由脚本计算。默认本地处理；如宿主调用外部模型，应先确认输入资料的数据使用边界。

## 验证
按 references/design-principles.md 的断言核对模拟数据、埋点及勾稽关系；脚本可运行不等同课堂效果验证。
