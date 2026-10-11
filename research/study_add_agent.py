import json, sys, pathlib, importlib.util
sys.path.insert(0, pathlib.Path(__file__).parent.as_posix()); import fastsim
long = json.load(open(sys.argv[1])); bars = {t: [b for b in r if b["ts"] >= "2009-06-01"] for t, r in long.items()}
data = fastsim.Data(bars); rows = json.load(open(sys.argv[2]))
def load(p):
    spec = importlib.util.spec_from_file_location(pathlib.Path(p).stem, p); m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m
dates = [d for d in data.dates if d >= "2011-01-03"]; idx = {d: i for i, d in enumerate(dates)}
for name, p in (a.split("=", 1) for a in sys.argv[3:]):
    for r in rows:
        i = idx[r["start"]]; r[name] = fastsim.run(load(p).decide, data, r["start"], dates[i + 13])["ret"]
json.dump(rows, open(sys.argv[2], "w")); print("ok")
