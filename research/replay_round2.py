"""Replay agents through Builderr's own live_runner.run_bot on cached Round 2 bars."""
import importlib.util, json, sys
lr_path, bars_path = sys.argv[1], sys.argv[2]
agents = dict(a.split("=", 1) for a in sys.argv[3:])
spec = importlib.util.spec_from_file_location("live_runner", lr_path)
lr = importlib.util.module_from_spec(spec); spec.loader.exec_module(lr)
bars = json.load(open(bars_path))
print("GOOGL bars:", len(bars.get("GOOGL", [])), "tickers:", len(bars))
dates = sorted({b["ts"] for r in bars.values() for b in r if b["ts"] >= "2026-07-07"})
def mdd(c):
    pk, m = 0, 0
    for x in c: pk = max(pk, x); m = min(m, x / pk - 1)
    return m
print("== full Round 2 window from 2026-07-07 to", dates[-1])
for name, path in agents.items():
    r = lr.run_bot(lr.load_decide_from(__import__("pathlib").Path(path)), bars, "2026-07-07")
    print(f"  {name:8s} ret={r['ret']*100:+6.2f}%  maxDD={mdd(r['curve'])*100:6.2f}%  trades={r['trades']}  days={r['days']}")
# Rolling 14-session windows (a fresh $100k start every 5 sessions), like a mid-October entry.
print("== rolling 14-session windows (start every 5 sessions)")
res = {n: [] for n in agents}
for i in range(0, len(dates) - 13, 5):
    start, end = dates[i], dates[i + 13]
    cut = {t: [b for b in rows if b["ts"] <= end] for t, rows in bars.items()}
    row = [start]
    for name, path in agents.items():
        r = lr.run_bot(lr.load_decide_from(__import__("pathlib").Path(path)), cut, start)
        res[name].append(r["ret"]); row.append(f"{name}={r['ret']*100:+5.2f}%")
    print("  ", "  ".join(row))
for n, v in res.items():
    v2 = sorted(v)
    print(f"  {n:8s} windows={len(v)} mean={sum(v)/len(v)*100:+.2f}% median={v2[len(v)//2]*100:+.2f}% worst={v2[0]*100:+.2f}% best={v2[-1]*100:+.2f}%")
