# depth-backup

MyLIQ 訂單簿收集器（box 上的 `myliq-depth-collector`）的**公開備援**。box 暫停時，這裡的快照用來補缺口。

- 資料：24 幣現貨訂單簿彙總（公開市場資料），**不含任何金鑰或個人資訊**。
- 觸發：只有 `workflow_dispatch`，由外部定時器（Cloudflare Worker）約每 5 分鐘觸發一次；本 repo 沒有 schedule。
- 算法與欄位跟 `collector_live.py` 相同：來源依序 Coinbase → Bitstamp → Gate → KuCoin（TRX：Bitstamp → Gate → KuCoin），計算中間價 ±1/2/5/10% 內買／賣盤名目金額。
- 檔案：`data/depth_YYYYMMDD.csv`（UTC 日期），每列 = 1 幣 1 次快照，往後加。

| 欄位 | 說明 |
|---|---|
| ts_utc | 快照分鐘（UTC，秒數歸零） |
| exchange, symbol | 實際來源與交易對 |
| mid | 最佳買賣價中間價 |
| bid_reach_pct / ask_reach_pct | 抓到的盤口離中間價最遠的距離（%） |
| bid_W / ask_W | 中間價 ±W% 內買／賣盤名目金額（W=1,2,5,10） |
| full_W | 1=盤口深度涵蓋 ±W%；0=沒涵蓋到（值偏低） |
| src | 固定為 `gh`（區分 box 資料） |

腳本：`scripts/snapshot.py`（抓快照）、`scripts/commit_rows.sh`（接檔、commit、推送；失敗先 `pull --rebase` 重試，不 force push）。
