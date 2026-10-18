#!/usr/bin/env python3
"""myliq 訂單簿公開備援：抓一次 24 幣現貨訂單簿快照。
算法與欄位跟 box 上 /workspace/myliq/collector_live.py 相同（來源順序、BANDS、四捨五入），另加 src=gh。
輸出：把本次各幣的列寫到 argv[1]（CSV，含表頭），供 workflow 接到 data/depth_YYYYMMDD.csv（UTC 日期）。
0 列時 exit 1（workflow 就不 commit）。"""
import json,time,csv,sys,urllib.request,datetime as dt,socket
socket.setdefaulttimeout(10)
UNIV="BTC ETH SOL XRP BNB DOGE ADA TRX LINK AVAX DOT LTC BCH SUI HYPE UNI AAVE NEAR TON ATOM APT ARB OP ZEC".split()
ORDER={'TRX':['bitstamp','gate','kucoin']}; DEF=['coinbase','bitstamp','gate','kucoin']
BANDS=(1,2,5,10); GAP=0.15
def get(u):return json.load(urllib.request.urlopen(urllib.request.Request(u,headers={'User-Agent':'myliq-depth-backup'}),timeout=10))
lv=lambda x:[(float(p),float(q)) for p,q,*_ in x]
SRC={'coinbase':(lambda c:get(f"https://api.exchange.coinbase.com/products/{c}-USD/book?level=2"),'-USD'),
'bitstamp':(lambda c:get(f"https://www.bitstamp.net/api/v2/order_book/{c.lower()}usd/"),'USD'),
'gate':(lambda c:get(f"https://api.gateio.ws/api/v4/spot/order_book?currency_pair={c}_USDT&limit=1000"),'_USDT'),
'kucoin':(lambda c:get(f"https://api.kucoin.com/api/v1/market/orderbook/level2_100?symbol={c}-USDT")['data'],'-USDT')}
F=['ts_utc','exchange','symbol','mid','bid_reach_pct','ask_reach_pct']+[f'{s}_{w}' for w in BANDS for s in ('bid','ask')]+[f'full_{w}' for w in BANDS]+['src']
def snap(c):
    for ex in ORDER.get(c,DEF):
        try:
            d=SRC[ex][0](c); b=sorted(lv(d['bids']),reverse=True); a=sorted(lv(d['asks']))
            if not(b and a): continue
            m=(b[0][0]+a[0][0])/2; br=(m-b[-1][0])/m*100; ar=(a[-1][0]-m)/m*100
            r={'ts_utc':dt.datetime.now(dt.timezone.utc).strftime('%Y-%m-%d %H:%M:00'),'exchange':ex,'symbol':c+SRC[ex][1],
               'mid':round(m,8),'bid_reach_pct':round(br,2),'ask_reach_pct':round(ar,2)}
            for w in BANDS:
                r[f'bid_{w}']=round(sum(p*q for p,q in b if p>=m*(1-w/100)),0)
                r[f'ask_{w}']=round(sum(p*q for p,q in a if p<=m*(1+w/100)),0)
                r[f'full_{w}']=int(min(br,ar)>=w)
            r['src']='gh'
            return r
        except Exception as e:
            print('ERR',c,ex,repr(e)[:120],flush=True)
        finally:
            time.sleep(GAP)
    return None
def main():
    out=sys.argv[1]; t0=time.time(); rows=[r for r in (snap(c) for c in UNIV) if r]
    with open(out,'w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=F); w.writeheader(); w.writerows(rows)
    print(f'rows {len(rows)}/{len(UNIV)} in {time.time()-t0:.1f}s',flush=True)
    sys.exit(0 if rows else 1)
if __name__=='__main__': main()
