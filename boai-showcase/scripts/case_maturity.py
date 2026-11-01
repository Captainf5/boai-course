#!/usr/bin/env python3
import json, sys
from pathlib import Path

WEIGHTS = {
    "artifact": 15,
    "business_question": 15,
    "inputs": 10,
    "rules": 10,
    "evidence": 10,
    "benchmark_output_or_result": 15,
    "conflict": 10,
    "expected_output": 10,
    "safety_boundaries": 5,
}

def truthy(v):
    return bool(v) and v != "unknown"

def score(brief):
    parts = {}
    parts["artifact"] = WEIGHTS["artifact"] if truthy(brief.get("artifact")) else 0
    parts["business_question"] = WEIGHTS["business_question"] if truthy(brief.get("business_question")) else 0
    parts["inputs"] = WEIGHTS["inputs"] if truthy(brief.get("inputs")) else 0
    parts["rules"] = WEIGHTS["rules"] if truthy(brief.get("rules")) else 0
    parts["evidence"] = WEIGHTS["evidence"] if truthy(brief.get("evidence")) else 0
    parts["benchmark_output_or_result"] = WEIGHTS["benchmark_output_or_result"] if (truthy(brief.get("benchmark_output")) or truthy(brief.get("real_result"))) else 0
    parts["conflict"] = WEIGHTS["conflict"] if truthy(brief.get("conflict")) else 0
    parts["expected_output"] = WEIGHTS["expected_output"] if truthy(brief.get("expected_output")) else 0
    parts["safety_boundaries"] = WEIGHTS["safety_boundaries"] if truthy(brief.get("safety_boundaries")) else 0
    total = sum(parts.values())

    p0 = []
    if not truthy(brief.get("artifact")): p0.append("缺少原始标的物")
    if not truthy(brief.get("business_question")): p0.append("缺少一句话业务问题")
    if not truthy(brief.get("inputs")): p0.append("缺少输入资料")
    if not truthy(brief.get("expected_output")): p0.append("缺少期望业务产物")

    ctype = brief.get("case_type")
    warnings = []
    if ctype in ("data", "mixed"):
        if brief.get("data_dictionary") is False: warnings.append("缺数据字典/指标口径")
        if brief.get("yoy_baseline") is False: warnings.append("缺同比基期，无法严谨做同比")
        if brief.get("business_events") is False: warnings.append("缺业务事件/原因字段，无法严谨归因")
        if brief.get("cost_parameters") is False: warnings.append("缺成本/毛利参数，无法做盈亏平衡")
        if brief.get("reason_detail") is False: warnings.append("缺问题原因明细，无法做帕累托")
        if brief.get("api_docs") is False and "api" in " ".join(brief.get("inputs") or []).lower(): warnings.append("涉及API但无正式文档，不得猜接口")

    if p0:
        gate = "BLOCK"
    elif total >= 85 and warnings:
        gate = "READY_WITH_RISKS"
    elif total >= 85:
        gate = "READY"
    elif total >= 70:
        gate = "READY_WITH_RISKS"
    elif total >= 50:
        gate = "SUPPLEMENT_FIRST"
    else:
        gate = "BLOCK"
    return {"score": total, "gate": gate, "parts": parts, "p0_blockers": p0, "warnings": warnings}

if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("Usage: case_maturity.py case_brief.json")
    brief = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    print(json.dumps(score(brief), ensure_ascii=False, indent=2))
