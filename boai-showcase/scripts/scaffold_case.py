#!/usr/bin/env python3
import argparse, re
from pathlib import Path

DIRS = [
    "00_场景与Brief",
    "01_原始资料",
    "02_学员版",
    "03_教练版",
    "04_Prompt",
    "05_Skill_Workflow",
    "06_HTML_自动化",
    "07_PPT",
    "08_测试结果",
]

def safe(s):
    return re.sub(r'[\\/:*?"<>|]+', '_', s).strip()

def main():
    p = argparse.ArgumentParser()
    p.add_argument("name")
    p.add_argument("--type", choices=["data", "nondata", "mixed"], default="mixed")
    p.add_argument("--out", default=".")
    args = p.parse_args()
    root = Path(args.out) / safe(args.name)
    root.mkdir(parents=True, exist_ok=True)
    for d in DIRS:
        (root / d).mkdir(exist_ok=True)
    brief = root / "00_场景与Brief" / "README.md"
    brief.write_text(f"# {args.name}\n\n- 案例类型：{args.type}\n- 一句话业务问题：\n- 标的物：\n- 对标物：\n- 最终业务产物：\n", encoding="utf-8")
    print(root.resolve())

if __name__ == "__main__": main()
