#!/usr/bin/env python3
from pathlib import Path
import sys
REQUIRED=[
    "SKILL.md","README.md",
    "templates/INTAKE_TEMPLATE.md","templates/CASE_BRIEF_TEMPLATE.md",
    "templates/DATA_CASE_TEMPLATE.md","templates/NONDATA_CASE_TEMPLATE.md",
    "scripts/route_case.py","scripts/case_maturity.py","scripts/profile_tabular.py",
    "scripts/scaffold_case.py","scripts/build_client_request.py","scripts/run_benchmarks.py",
    "benchmarks/golden_cases.json","benchmarks/QUALITATIVE_CHECKLIST.md",
    "schemas/case_brief.schema.json"
]
root=Path(sys.argv[1] if len(sys.argv)>1 else Path(__file__).resolve().parents[1])
missing=[x for x in REQUIRED if not (root/x).exists()]
if missing:
    print("MISSING:")
    print("\n".join(missing))
    raise SystemExit(1)
print(f"PASS: package complete ({len(REQUIRED)} required files)")
