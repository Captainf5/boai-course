#!/usr/bin/env bash
# batch_upsert.sh <项目目录> <pptx文件名> <总页数>
# 逐页 lint -> 全过后 upsert-dsl --page-index 原位替换。建议 run_in_background 执行。
set -u
export PATH="/usr/bin:/bin:$PATH"

DIR="$1"; PPTX="$2"; TOTAL="$3"
cd "$DIR" || { echo "DIR NOT FOUND: $DIR"; exit 1; }

fail=0
for i in $(seq -w 1 "$TOTAL"); do
  idx=$((10#$i - 1))
  f="slides/$i.slide"
  [ -f "$f" ] || { echo "MISSING $f"; fail=1; break; }
  r=$(slidep lint "$PPTX" --dsl-file "$f" 2>/dev/null)
  echo "$r" | grep -q '"ok":true' || { echo "LINT FAIL $i"; echo "$r" | head -5; fail=1; break; }
  u=$(slidep upsert-dsl "$PPTX" --dsl-file "$f" --page-index "$idx" 2>/dev/null)
  echo "$u" | grep -q '"ok":true' || { echo "UPSERT FAIL $i"; echo "$u" | head -3; fail=1; break; }
  echo "done $i"
done
[ "$fail" -eq 0 ] && echo "ALL $TOTAL PAGES UPDATED"
