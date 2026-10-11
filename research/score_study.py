import json, sys
rows = json.load(open(sys.argv[1])); names = sys.argv[2].split(",")
ARNAV_NOW = -0.0299
def table(sub, label):
    print(f"\n== {label}: {len(sub)} windows")
    print(f"  {'bot':4s} {'mean':>7s} {'median':>7s} {'p5':>7s} {'worst':>7s} {'beatArnav':>9s} {'>=+6%':>6s} {'>=+9%':>6s}")
    for n in names:
        v = sorted(r[n] for r in sub)
        q = sum(r[n] > (1 + ARNAV_NOW) * (1 + r["E"]) - 1 for r in sub) / len(sub)
        f = lambda x: f"{x*100:+6.2f}%"
        print(f"  {n:4s} {f(sum(v)/len(v))} {f(v[len(v)//2])} {f(v[int(len(v)*0.05)])} {f(v[0])} {q*100:8.1f}% {sum(x>=0.06 for x in v)/len(v)*100:5.1f}% {sum(x>=0.09 for x in v)/len(v)*100:5.1f}%")
table(rows, "ALL 2011-2026")
table([r for r in rows if r["regime"] == "ON"], "entry regime ON (today's state)")
table([r for r in rows if r["start"] < "2020-01-01"], "2011-2019")
table([r for r in rows if r["start"] >= "2020-01-01"], "2020-2026")
