"""Rangkayo bot — builderr Trading Round 2 entry (strategy: steady beta with a brake).

One sentence: hold a fixed, diversified book of big US index and chip ETFs at
about 1.35x market exposure, and go to cash only when the market really breaks.

Why this shape, for a short forward window (about 14 sessions, mid to late
October 2026):
  * Over two to three weeks, most of a book's return comes from how much market
    exposure it holds, not from which names it picked. Picking and switching
    also cost slippage and whipsaw.
  * The Round 1 winner lost money in Round 2 mainly by stepping to cash on dips
    and missing the rebounds. This bot has two states and changes them rarely.
  * ETFs only. Back-tests of single-stock pickers on today's mega-cap list look
    great because that list is made of past winners (survivorship bias).

The book (fractions of equity):
  INVESTED  QQQ 25%, SMH 25%, SPY 25%, TQQQ 20%  -> beta-adjusted gross 1.35x
  CASH      nothing  (QQQ down 5% in 5 days, QQQ 20-day vol above 40%,
                      or QQQ more than 3% below its 50-day average)

Design limits (by construction):
  * Long-only, no borrowing; buys never exceed cash minus a 1.5% buffer.
  * Max target per name 25% (cap 30%); a name above 27% is trimmed.
  * Beta gross target 1.35x (cap 1.5x); the book is rebalanced if it drifts above 1.42x.
  * Stateless: every call recomputes from the bars and positions it is given.
  * Standard-library Python, no network, no LLM, no files, only past bars.
"""
from __future__ import annotations

import math

CORE = {"QQQ": 0.25, "SMH": 0.25, "SPY": 0.25}
SLEEVE = {"TQQQ": 0.20}
SLEEVE_FALLBACK = {"QLD": 0.30}          # same 0.60 beta budget if TQQQ is missing

BETA = {
    "TQQQ": 3.0, "SOXL": 3.0, "UPRO": 3.0, "SPXL": 3.0, "TNA": 3.0, "FAS": 3.0,
    "TECL": 3.0, "LABU": 3.0, "CURE": 3.0, "DRN": 3.0, "UDOW": 3.0, "NAIL": 3.0,
    "QLD": 2.0, "SSO": 2.0, "DDM": 2.0, "ROM": 2.0, "UWM": 2.0, "AGQ": 2.0,
}

TREND_SMA = 50        # QQQ trend line
VOL_BRAKE = 0.40      # above this -> cash
DROP_BRAKE = -0.05    # QQQ 5-day return at or below -5% -> cash
BREAK_BRAKE = 0.97    # QQQ more than 3% below its 50-day average -> cash
BAND = 0.03           # skip resizes smaller than 3% of equity
DRIFT_NAME = 0.27     # always trim a name above this
DRIFT_GROSS = 1.42    # always rebalance if beta gross drifts above this
CASH_BUFFER = 0.985   # never spend the last 1.5%
MIN_BARS = 60


def _closes(market_state, t):
    out = []
    for b in market_state.get(t) or []:
        try:
            c = float(b["close"])
        except (KeyError, TypeError, ValueError):
            continue
        if c > 0 and math.isfinite(c):
            out.append(c)
    return out


def _sma(c, n):
    return sum(c[-n:]) / n


def _vol(c, n):
    r = [c[i] / c[i - 1] - 1 for i in range(len(c) - n, len(c))]
    m = sum(r) / n
    return math.sqrt(sum((x - m) ** 2 for x in r) / n) * math.sqrt(252)


def regime(market_state):
    """INVESTED or CASH, from QQQ daily closes (SPY must also have history)."""
    q, s = _closes(market_state, "QQQ"), _closes(market_state, "SPY")
    if len(q) < MIN_BARS or len(s) < MIN_BARS:
        return "CASH"
    q_sma, vol20 = _sma(q, TREND_SMA), _vol(q, 20)
    if vol20 > VOL_BRAKE or q[-1] / q[-6] - 1 <= DROP_BRAKE or q[-1] < BREAK_BRAKE * q_sma:
        return "CASH"
    return "INVESTED"


def targets(market_state):
    state = regime(market_state)
    if state == "CASH":
        return state, {}
    out = {t: w for t, w in CORE.items() if len(_closes(market_state, t)) >= MIN_BARS}
    for sleeve in (SLEEVE, SLEEVE_FALLBACK):
        t, w = next(iter(sleeve.items()))
        if len(_closes(market_state, t)) >= MIN_BARS:
            out[t] = w
            break
    return state, out


def decide(market_state, portfolio_state, cash):
    try:
        cash = float(portfolio_state.get("cash", cash))
    except (TypeError, ValueError, AttributeError):
        cash = float(cash or 0.0)

    held = {}
    for p in portfolio_state.get("positions") or []:
        try:
            t, q = str(p["ticker"]), float(p["quantity"])
        except (KeyError, TypeError, ValueError):
            continue
        if q > 0:
            held[t] = held.get(t, 0.0) + q

    last_prices = portfolio_state.get("last_prices") or {}

    def px(t):
        c = _closes(market_state, t)
        if c:
            return c[-1]
        try:
            return float(last_prices.get(t) or 0.0)
        except (TypeError, ValueError):
            return 0.0

    equity = cash + sum(q * px(t) for t, q in held.items())
    if equity <= 0:
        return []

    _, tgt = targets(market_state)
    weights = {t: q * px(t) / equity for t, q in held.items()}
    force = sum(w * BETA.get(t, 1.0) for t, w in weights.items()) > DRIFT_GROSS

    sells, buys = [], []
    for t in sorted(set(held) | set(tgt)):
        p = px(t)
        if p <= 0:
            continue
        cur, want = weights.get(t, 0.0), tgt.get(t, 0.0)
        diff = want - cur
        if want == 0.0 and cur > 0:
            sells.append({"ticker": t, "side": "sell", "quantity": held[t]})
        elif diff < 0 and (-diff >= BAND or cur > DRIFT_NAME or force):
            sells.append({"ticker": t, "side": "sell", "quantity": round(-diff * equity / p, 6)})
        elif diff > 0 and (cur == 0.0 or diff >= BAND):
            buys.append((t, diff * equity))

    # Buys are funded by cash plus what the sells release, keeping a small buffer.
    budget = cash + sum(o["quantity"] * px(o["ticker"]) for o in sells) - (1 - CASH_BUFFER) * equity
    orders = list(sells)
    for t, notional in buys:
        spend = min(notional, budget)
        if spend <= 0:
            break
        orders.append({"ticker": t, "side": "buy", "quantity": round(spend / px(t), 6)})
        budget -= spend
    return orders
