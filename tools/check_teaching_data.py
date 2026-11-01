"""Validate actual generated data rather than trusting printed expectations."""
from pathlib import Path
import contextlib
import io
import runpy
import statistics

ROOT = Path(__file__).resolve().parents[1]
with contextlib.redirect_stdout(io.StringIO()):
    ns = runpy.run_path(str(ROOT / 'boai-zengxiao-data-case/scripts/gen_dataset_template.py'))
rows = ns['data']
assert len(rows) == 52 and all(len(row) == 12 for row in rows)
yoy = sum(ns['rev25'].values()) / sum(ns['rev24'].values()) - 1
assert 0 <= yoy <= .02
for name, month, column, _, _ in ns['ANOMALIES']:
    values = [r[column] for r in rows if r[2] == name]
    actual = next(r[column] for r in rows if r[2] == name and r[0] == month)
    assert (actual - statistics.mean(values)) / statistics.stdev(values) > 2
revenue = [r[6] for r in rows if r[2] == '项目C']
streak = longest = 0
for previous, current in zip(revenue, revenue[1:]):
    streak = streak + 1 if current < previous else 0
    longest = max(longest, streak)
assert longest >= 5
print('PASS: 52 rows, structural divergence, 3 outliers and declining trend')
