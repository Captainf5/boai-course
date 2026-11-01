#!/usr/bin/env python3
import json, sys
from pathlib import Path

def has(v): return bool(v) and v != "unknown"

def build(b):
    ctype=b.get("case_type","unknown")
    asks=[]
    def add(priority,name,why,minver):
        asks.append({"priority":priority,"material":name,"why":why,"minimum":minver})
    if not has(b.get("artifact")):
        add("P0","原始标的物","确认学员真实要处理的对象","一份脱敏原件/截图/样本")
    if not (has(b.get("benchmark_output")) or has(b.get("real_result"))):
        add("P1","对标物/真实最终结果","用于课堂最后验证AI和人的判断","最终结论、关键页面或优秀样例即可")
    if not has(b.get("business_question")):
        add("P0","一句话业务目标","锁定案例最终需要做的决策","一句‘如果你是X，你要决定什么’")
    if ctype in ("data","mixed"):
        if b.get("data_dictionary") is not True: add("P0","数据字典/指标口径","避免AI误解字段和计算口径","字段名、定义、单位、计算方式")
        if b.get("yoy_baseline") is not True: add("P1","同比基期数据","支持同比与结构变化判断","去年同期同口径数据")
        if b.get("business_events") is not True: add("P1","重大业务事件/原因背景","支持异常归因验证","异常期的活动、故障、策略、排班等事件清单")
        if b.get("cost_parameters") is not True: add("P2","成本/毛利参数","支持盈亏平衡和经营价值判断","固定成本、毛利率、单位变动成本/补贴")
        if b.get("reason_detail") is not True: add("P2","问题原因明细","支持帕累托改进","问题原因+次数/金额")
        if b.get("api_docs") is False:
            inputs=" ".join(b.get("inputs") or []).lower()
            if "api" in inputs or "接口" in inputs:
                add("P0","正式API文档","避免猜内部接口并支持自动化","接口、鉴权、样例返回、权限、限流")
    else:
        if not has(b.get("rules")): add("P1","制度/规则/边界","判断什么能做、什么不能做","关键条款或规则摘录")
        if not has(b.get("evidence")): add("P1","证据/往来过程","支持交叉验证和人工裁决","关键邮件、检测、审批、发言或过程材料")
    order={"P0":0,"P1":1,"P2":2}
    asks.sort(key=lambda x:order[x["priority"]])
    return asks

def to_md(asks):
    if not asks: return "当前资料基本齐全，可以进入案例开发。"
    lines=["为了把案例做成真实业务场景，还建议补充以下资料：",""]
    for i,a in enumerate(asks,1):
        lines += [f"{i}. **[{a['priority']}] {a['material']}**", f"   - 用途：{a['why']}", f"   - 最小版本：{a['minimum']}", "   - 可脱敏：是", ""]
    return "\n".join(lines)

if __name__=="__main__":
    if len(sys.argv)!=2: raise SystemExit("Usage: build_client_request.py case_brief.json")
    b=json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    print(to_md(build(b)))
