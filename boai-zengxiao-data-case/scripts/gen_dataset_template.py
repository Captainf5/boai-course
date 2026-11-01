# -*- coding: utf-8 -*-
"""
教学数据集生成骨架（博AI增效数据案例Skill）
用法: 修改 PROJECTS 人设配置和 MONTHS, 直接运行, 打印验证断言
铁律: seed固定 / 埋点三类齐全 / 验证断言全部打印
"""
import random
import statistics

random.seed(42)

# ---------------- 配置区(按课程改这里) ----------------
# (项目, 区域, 业态, 负责人, 1月目标, 目标月增, (模式, 达成率基准, 噪声), 毛利率, 收缴率, 能耗基线, 客诉基线, 增值基线, 增值月增, YoY因子)
PROJECTS = [
    ("项目A", "东区", "业态甲", "经理甲", 118, 2.0, ("stable", 1.03, 0.015), 0.155, 97.5, 40, 3, 8, 0.30, 1.07),
    ("项目B", "东区", "业态乙", "经理乙", 125, 2.0, ("stable", 0.955, 0.012), 0.148, 93.5, 45, 4.5, 15, 0.0, 0.97),
    ("项目C", "南区", "业态丙", "经理丙", 150, 0.5, ("decline", 0.90, 0.006), 0.120, 86.0, 48, 9, 14, -0.35, 0.86),
    ("项目D", "北区", "业态甲", "经理丁", 185, 2.2, ("stable", 1.07, 0.015), 0.168, 98.5, 52, 2, 22, 0.70, 1.12),
]
MONTHS = [(2024, 12)] + [(2025, m) for m in range(1, 13)]  # 13个月 x N项目

# 埋点: (项目, 月份, 列索引, 值, 业务解释) 列索引: 9=能耗 10=客诉 11=增值
ANOMALIES = [
    ("项目D", "2025-07", 9, None, "能耗突刺: 设备故障+极端天气"),   # None=自动算基线x1.4
    ("项目A", "2025-12", 11, None, "增值突刺: 一次性大单"),
    ("项目B", "2025-03", 10, None, "客诉突刺: 群诉事件"),
]

def season_energy(m):
    return {1: 6, 2: 3, 7: 8, 8: 9, 12: 5}.get(m, 0)

def gen_project(cfg):
    (name, region, biz, mgr, t0, tstep, (mode, ac, anoise), margin, coll, ebase, cbase, v0, vstep, yoy) = cfg
    rows, rows24 = [], []
    for idx, (y, m) in enumerate(MONTHS):
        i = idx - 1
        target = t0 + tstep * (i + 1)
        if mode == "decline":
            # 达成率递减(5月起加速, 6期后企稳回升) -> 连续环比下滑
            dip = 0.015 * min(max(i - 3, 0), 6) - 0.005 * max(i - 9, 0)
            achieve = ac - dip + random.uniform(-anoise, anoise)
        else:
            achieve = ac + random.uniform(-anoise, anoise)
        rev = round(target * achieve, 1)
        profit = round(rev * (margin + random.uniform(-0.008, 0.008)), 1)
        collrate = round(coll + random.uniform(-0.8, 0.8), 1)
        energy = round(ebase + season_energy(m) + random.uniform(-1.5, 1.5), 1)
        complaints = max(1, round(cbase + random.uniform(-1.2, 1.2)))
        vas = round(v0 + vstep * max(i, 0) + random.uniform(-0.8, 0.8), 1)
        rows.append([f"{y}-{m:02d}", region, name, biz, mgr, round(target, 1), rev,
                     profit, collrate, energy, complaints, vas])
        rev24 = round(rev / yoy * random.uniform(0.99, 1.01), 1)
        rows24.append([f"{y-1}-{m:02d}", name, rev24, round(rev24 * margin, 1)])
    return rows, rows24

data, data24 = [], []
for cfg in PROJECTS:
    r, r24 = gen_project(cfg)
    data.extend(r); data24.extend(r24)

# 埋异常(自动取该项目该列中位数x1.4或客诉x2.5)
for name, ym, col, val, why in ANOMALIES:
    for r in data:
        if r[2] == name and r[0] == ym:
            if val is None:
                series = sorted(x[col] for x in data if x[2] == name)
                med = statistics.median(series)
                val = round(med * (2.5 if col == 10 else 1.4), 1)
            r[col] = val

data.sort(key=lambda r: (r[2], r[0]))
data24.sort(key=lambda r: (r[1], r[0]))

# ---------------- 验证断言(铁律: 全部打印) ----------------
print("=" * 60)
print("验证断言")
print("=" * 60)
print(f"[1] 行数={len(data)} 列数={len(data[0])}")
rev25 = {c[0]: sum(r[6] for r in data if r[2] == c[0] and r[0].startswith("2025")) for c in PROJECTS}
tgt25 = {c[0]: sum(r[5] for r in data if r[2] == c[0] and r[0].startswith("2025")) for c in PROJECTS}
rev24 = {c[0]: sum(r[2] for r in data24 if r[1] == c[0] and r[0].startswith("2024")) for c in PROJECTS}  # 必须过滤年份!
print(f"[2] 公司整体: 达成率={sum(rev25.values())/sum(tgt25.values())*100:.1f}% "
      f"同比={(sum(rev25.values())/sum(rev24.values())-1)*100:+.1f}%  <- 结构假象应成立(0~2%)")
for c in PROJECTS:
    n = c[0]
    print(f"[3] {n}: 达成率={rev25[n]/tgt25[n]*100:.1f}% 同比={(rev25[n]/rev24[n]-1)*100:+.1f}%")
# 最长连跌
for c in PROJECTS:
    if c[6][0] != "decline":
        continue
    n = c[0]
    revs = [r[6] for r in data if r[2] == n]
    streak = mx = 0
    for i in range(1, len(revs)):
        streak = streak + 1 if revs[i] < revs[i-1] else 0
        mx = max(mx, streak)
    print(f"[4] {n} 最长连续环比下滑={mx}个月  <- 应>=5")
# 异常z-score
for name, ym, col, _, why in ANOMALIES:
    vals = [r[col] for r in data if r[2] == name]
    mu, sd = statistics.mean(vals), statistics.stdev(vals)
    v = [r[col] for r in data if r[2] == name and r[0] == ym][0]
    print(f"[5] 异常 {name} {ym} 值={v} z={(v-mu)/sd:.2f} ({why})  <- 应>2")
print("\n骨架运行正常。接入 openpyxl 写 xlsx 即可(参考 SKILL.md 第4步)。")
