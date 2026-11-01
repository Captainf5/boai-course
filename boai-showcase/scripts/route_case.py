#!/usr/bin/env python3
import json, sys
from pathlib import Path

DATA_EXTS = {".xlsx", ".xls", ".csv", ".tsv", ".parquet", ".db", ".sqlite"}
NONDATA_EXTS = {".docx", ".doc", ".pdf", ".pptx", ".ppt", ".txt", ".md", ".eml", ".msg", ".png", ".jpg", ".jpeg"}
DATA_WORDS = {"同比", "环比", "趋势", "指标", "数据分析", "异常", "看板", "roi", "成本", "毛利", "销量", "经营", "营销", "库存", "人效"}
NONDATA_WORDS = {"客诉", "会议", "纪要", "简历", "招聘", "合同", "制度", "话术", "方案", "总结", "文案"}

def load(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))

def route(brief):
    files = brief.get("file_types") or []
    exts = {x.lower() if x.startswith(".") else "." + x.lower() for x in files}
    text = " ".join(str(brief.get(k, "")) for k in ["case_name", "business_question", "expected_output"] ).lower()
    data_score = sum(3 for e in exts if e in DATA_EXTS) + sum(1 for w in DATA_WORDS if w in text)
    non_score = sum(3 for e in exts if e in NONDATA_EXTS) + sum(1 for w in NONDATA_WORDS if w in text)
    if data_score and non_score and abs(data_score - non_score) <= 3:
        typ = "mixed"
        confidence = min(95, 65 + (data_score + non_score) * 2)
    elif data_score > non_score:
        typ = "data"
        confidence = min(98, 65 + (data_score - non_score) * 5)
    elif non_score > data_score:
        typ = "nondata"
        confidence = min(98, 65 + (non_score - data_score) * 5)
    else:
        typ, confidence = "unknown", 40
    return {"case_type": typ, "confidence": confidence, "data_score": data_score, "nondata_score": non_score}

if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("Usage: route_case.py case_brief.json")
    print(json.dumps(route(load(sys.argv[1])), ensure_ascii=False, indent=2))
