"""Fast re-implementation of live_runner.run_bot semantics (fill at open, slippage, 30%/1.5x caps,
sell-before-buy, mark at close) with market_state trimmed to the last HIST bars before each date."""
import bisect, math
SLIP_EQ, SLIP_LEV = 0.0005, 0.0010
B3 = {"TQQQ","SOXL","UPRO","SPXL","TNA","FAS","TECL","LABU","CURE","DRN","UDOW","NAIL"}
B2 = {"QLD","SSO","DDM","ROM","UWM","AGQ"}
def beta(t): return 3.0 if t in B3 else 2.0 if t in B2 else 1.0
class Data:
    def __init__(self, bars):
        self.bars = bars
        self.ts = {t: [b["ts"] for b in rows] for t, rows in bars.items()}
        self.by = {t: {b["ts"]: b for b in rows} for t, rows in bars.items()}
        self.dates = sorted({d for v in self.ts.values() for d in v})
def run(decide, data, start, end, hist=320):
    eval_dates = [d for d in data.dates if start <= d <= end]
    cash, pos, avg, curve, trades = 100000.0, {}, {}, [], 0
    for date in eval_dates:
        op = {t: data.by[t][date]["open"] for t in data.bars if date in data.by[t]}
        cl = {t: data.by[t][date]["close"] for t in data.bars if date in data.by[t]}
        ms = {}
        for t, rows in data.bars.items():
            k = bisect.bisect_left(data.ts[t], date)
            if k > 0: ms[t] = rows[max(0, k - hist):k]
        prior = {t: v[-1]["close"] for t, v in ms.items()}
        ps = {"cash": cash, "positions": [{"ticker": t, "quantity": q, "avg_cost": avg.get(t, 0.0)} for t, q in pos.items() if q > 0], "last_prices": prior}
        try: orders = decide(ms, ps, cash) or []
        except Exception: orders = []
        norm = []
        for o in orders[:100] if isinstance(orders, list) else []:
            try: tk, side, qty = str(o["ticker"]).strip().upper(), o["side"], float(o["quantity"])
            except (KeyError, TypeError, ValueError): continue
            if side not in ("buy","sell") or not math.isfinite(qty) or qty <= 0 or tk not in op: continue
            norm.append((tk, side, qty))
        for tk, side, qty in sorted(norm, key=lambda x: 0 if x[1] == "sell" else 1):
            px = op[tk]; slip = SLIP_LEV if beta(tk) > 1 else SLIP_EQ
            if side == "buy":
                fill = px * (1 + slip)
                eq = max(cash + sum(pos.get(t, 0) * op.get(t, 0) for t in pos), 1e-9)
                held = pos.get(tk, 0.0)
                conc = max(0.0, 0.30 * eq - held * fill)
                bu = sum(pos.get(t, 0) * op.get(t, 0) * beta(t) for t in pos)
                broom = max(0.0, 1.5 * eq - bu)
                qty = min(qty, min(cash, conc, broom / beta(tk)) / fill if fill > 0 else 0)
                if qty <= 0: continue
                avg[tk] = (avg.get(tk, 0) * held + fill * qty) / (held + qty)
                pos[tk] = held + qty; cash -= fill * qty; trades += 1
            else:
                held = pos.get(tk, 0.0); qty = min(qty, held)
                if qty <= 0: continue
                cash += px * (1 - slip) * qty; pos[tk] = held - qty; trades += 1
        curve.append(max(cash + sum(pos.get(t, 0) * cl.get(t, 0) for t in pos), 1e-9))
    return {"ret": curve[-1] / 100000 - 1 if curve else 0.0, "curve": curve, "trades": trades}
