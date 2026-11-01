# 课纲验证范围

版本见`VERSION`。本包保留已有44项课纲回归测试，测试入口为`python -m unittest discover -s tests -v`，需先安装`delivery-pack/requirements-cloud.txt`。

修改规则或资源后先执行`python delivery-pack/scripts/build_skill_package.py`，再执行同命令加`--check`，最后运行测试。该流程会同时核对手机包。

本机脚本和包结构检查不证明新仓库云端排版、手机端查看或真实客户验收均已完成。云端运行以仓库Actions为准；用户提交私人客户材料前应核对仓库可见性，公开仓库Issue与提交不可用于客户机密。
