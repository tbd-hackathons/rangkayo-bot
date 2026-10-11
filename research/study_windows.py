"""Pre-registered study: 14-session windows, start every 5 sessions, 2011-01 to latest."""
import importlib.util, json, sys, pathlib, statistics as st
sys.path.insert(0, pathlib.Path(__file__).parent.as_posix()); import fastsim
long = json.load(open(sys.argv[1]))
bars = {t: [b for b in rows if b["ts"] >= "2009-06-01"] for t, rows in long.items()}
data = fastsim.Data(bars)
agents = dict(a.split("=", 1) for a in sys.argv[3:])
def load(p):
    spec = importlib.util.spec_from_file_location(pathlib.Path(p).stem, p); m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m
regime_mod = load(sys.argv[2])
dates = [d for d in data.dates if d >= "2011-01-03"]
rows = []
for i in range(0, len(dates) - 13, 5):
    s, e = dates[i], dates[i + 13]
    ms = {t: v[max(0, k - 320):k] for t, v in bars.items() if (k := __import__("bisect").bisect_left(data.ts[t], s)) > 0}
    row = {"start": s, "regime": regime_mod.regime(ms)}
    for n, p in agents.items():
        row[n] = fastsim.run(load(p).decide, data, s, e)["ret"]   # fresh module = fresh state per window
    rows.append(row)
json.dump(rows, open(pathlib.Path(sys.argv[1]).with_name("study_rows.json"), "w"))
print("windows:", len(rows), rows[0]["start"], "->", rows[-1]["start"])
