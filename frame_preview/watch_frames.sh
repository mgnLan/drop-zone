#!/bin/bash
# Monitor all 12 frame generation logs until terminal state
OUT="I:/Kimi project/Drop Zone/frame_preview/frames_status.txt"
: > "$OUT"
while true; do
  done_n=0; fail_n=0
  for f in /tmp/imgen_f*.log; do
    name=$(basename "$f" .log)
    if grep -q "^done:" "$f" 2>/dev/null; then
      echo "$name DONE $(grep '^done:' $f | tail -1)" >> "$OUT.tmp"
      done_n=$((done_n+1))
    elif grep -qiE "error|failed|Traceback|rejected" "$f" 2>/dev/null; then
      echo "$name FAIL $(grep -iE 'error|failed|rejected' $f | tail -1)" >> "$OUT.tmp"
      fail_n=$((fail_n+1))
    else
      echo "$name RUNNING" >> "$OUT.tmp"
    fi
  done
  mv "$OUT.tmp" "$OUT"
  total=$((done_n+fail_n))
  if [ "$total" -ge 12 ]; then echo "ALL_TERMINAL done=$done_n fail=$fail_n" >> "$OUT"; break; fi
  sleep 20
done
