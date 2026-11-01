#!/usr/bin/env python3
import json, subprocess, sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
fixtures=json.loads((ROOT/"benchmarks"/"golden_cases.json").read_text(encoding="utf-8"))
route=ROOT/"scripts"/"route_case.py"
maturity=ROOT/"scripts"/"case_maturity.py"
tmp=ROOT/"benchmarks"/"_tmp_case.json"
failed=[]
for c in fixtures:
    tmp.write_text(json.dumps(c["brief"],ensure_ascii=False),encoding="utf-8")
    r=json.loads(subprocess.check_output([sys.executable,str(route),str(tmp)],text=True))
    m=json.loads(subprocess.check_output([sys.executable,str(maturity),str(tmp)],text=True))
    if r["case_type"] != c["expected_type"]:
        failed.append(f'{c["name"]}: route {r["case_type"]} != {c["expected_type"]}')
    if c.get("expected_gate") and m["gate"] != c["expected_gate"]:
        failed.append(f'{c["name"]}: gate {m["gate"]} != {c["expected_gate"]}')
try: tmp.unlink()
except FileNotFoundError: pass
if failed:
    print("FAILED")
    print("\n".join(failed))
    raise SystemExit(1)
print(f"PASS: {len(fixtures)} benchmark cases")
