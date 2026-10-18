#!/bin/bash
# 把 $1（snapshot.py 輸出，含表頭）接到 data/depth_YYYYMMDD.csv（UTC 日期，依第一列 ts_utc），commit 並推送。
# 推送失敗：先 git pull --rebase 再推；rebase 衝突則改成「重置到 origin/main 後重新接上本次資料」再推。最多 5 次。不 force push。
set -u
ROWS="$1"
day=$(sed -n '2p' "$ROWS" | cut -c1-10 | tr -d '-')
[ -n "$day" ] || { echo "no rows, skip commit"; exit 1; }
FN="data/depth_${day}.csv"; n=$(( $(wc -l < "$ROWS") - 1 ))
append() { mkdir -p data; if [ -f "$FN" ]; then tail -n +2 "$ROWS" >> "$FN"; else cp "$ROWS" "$FN"; fi; git add "$FN"; git commit -q -m "depth $(sed -n '2p' "$ROWS" | cut -d, -f1) UTC (${n} rows)"; }
append
for i in 1 2 3 4 5; do
  git push -q origin HEAD:main && { echo "pushed $FN +$n rows (try $i)"; exit 0; }
  echo "push failed (try $i), pull --rebase"
  if ! git pull -q --rebase origin main; then
    git rebase --abort 2>/dev/null; git fetch -q origin main; git reset -q --hard origin/main; append
  fi
  sleep $((i*3))
done
echo "push failed after 5 tries"; exit 1
