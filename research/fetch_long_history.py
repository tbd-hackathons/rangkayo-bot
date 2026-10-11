"""Max daily history for the 42 live tickers (Yahoo, auto-adjusted), same row shape as live_runner."""
import json, sys, time
import yfinance as yf
tickers = sys.argv[2].split(",")
out = {}
for t in tickers:
    for attempt in range(3):
        try:
            df = yf.download(t, period="max", interval="1d", auto_adjust=True, progress=False, timeout=20)
            if df is not None and not df.empty:
                if hasattr(df.columns, "nlevels") and df.columns.nlevels > 1:
                    df.columns = df.columns.get_level_values(0)
                rows = []
                for ts, r in df.iterrows():
                    o, h, l, c = (float(r[k]) for k in ("Open", "High", "Low", "Close"))
                    if any(x != x for x in (o, h, l, c)) or o <= 0 or c <= 0:
                        continue
                    v = r["Volume"]; rows.append({"ts": ts.strftime("%Y-%m-%d"), "open": o, "high": h, "low": l, "close": c, "volume": int(v) if v == v else 0})
                out[t] = rows; break
        except Exception as e:
            print("retry", t, e, file=sys.stderr); time.sleep(3)
    time.sleep(0.4)
json.dump(out, open(sys.argv[1], "w"))
print("got", len(out), {t: out[t][0]["ts"] for t in out})
