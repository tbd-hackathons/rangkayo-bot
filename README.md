# Rangkayo bot

Strategy: steady beta with a brake. An entry for
[builderr Trading, Round 2](https://builderr.ai/trading-v0), forked from the
[builderr starter template](https://github.com/builderr-ai/builderr-trading-template) (MIT).

The bot is [`agent.py`](agent.py). It is about 140 lines of standard-library Python, with no
network calls, no LLM and no data files.

## What it does

| State | When (decided on the prior close) | Book | Beta-adjusted gross |
|---|---|---|---|
| **INVESTED** | Default | QQQ 25%, SMH 25%, SPY 25%, TQQQ 20% | 1.35x |
| **CASH** | QQQ down 5% in 5 days, or QQQ 20-day volatility above 40%, or QQQ more than 3% below its 50-day average | nothing | 0x |

Why this shape for a window of about 14 sessions:

- Over two or three weeks, most of a book's return comes from how much market exposure it holds.
  Switching names and states costs slippage and causes whipsaw.
- Two states, rarely changed. The Round 1 winner lost money in Round 2 mostly by going to cash on
  dips and missing the rebounds.
- ETFs only. Single-stock pickers back-tested on today's mega-cap list look strong because that
  list is made of past winners. See the evidence below.

## Limits, by construction

- Long-only, no borrowing. Buys never spend the last 1.5% of equity.
- The largest target weight is 25%. Any name that drifts above 27% is trimmed (the cap is 30%).
- Beta-adjusted gross targets 1.35x. The book is rebalanced if it drifts above 1.42x (the cap is 1.5x).
- Stateless. Every call recomputes from the bars and positions it is given, and uses only past bars.
- It trades only tickers in the live scorer's fetch list (`ROUND2_FETCH_UNIVERSE` in `live_runner.py`).

## Evidence, reported as measured

All simulations use the template's fill model: decisions are made on the prior close, orders
fill at the next open with 5 bps of slippage (10 bps on leveraged ETFs), and the 30% and 1.5x caps
are enforced. `research/fastsim.py` reimplements `live_runner.run_bot`. On the Round 2 data it
matches `run_bot` to four decimals for three different bots, and the replay reproduces the
benchmark's published Round 2 return (−2.99%).

### 1. `python preview.py` (the three public sample windows)

| Window | Return | Max drawdown | Trades |
|---|---|---|---|
| calm_uptrend (Jun–Aug 2021) | +16.87% | 3.70% | 5 |
| moderate_selloff (Sep–Oct 2021) | −8.83% | 10.52% | 28 |
| vol_spike_snapback (Feb–Apr 2020) | −14.25% | 14.25% | 24 |

Safety bar: all PASS. Peak gross 1.42x, peak single name 26%, worst drawdown 14.2%.

### 2. Long-history study: 791 windows of 14 sessions, 2011–2026

A fresh $100k account starts every 5 sessions, from January 2011 to September 2026, using Yahoo
daily bars for the 42 live tickers. I fixed the candidates and the selection rule before
running the study. "Beat bar" means the bot's 14-session return exceeds the benchmark's Round 2
return (−2.99% on 9 Oct) after compounding the benchmark's own return in the same 14 sessions.

| Design | Mean | 5th pct | Worst | Beat bar | ≥ +6% | ≥ +9% |
|---|---|---|---|---|---|---|
| A: core + TQQQ only in calm uptrends | +0.77% | −6.33% | −14.63% | 80.9% | 9.5% | 2.3% |
| **B: core + TQQQ unless CASH (this bot)** | +0.94% | −8.41% | −19.57% | 78.8% | 13.7% | 3.8% |
| C: momentum picker, stocks + ETFs | +1.29% | −6.93% | −13.16% | 91.5% | 15.4% | 7.6% |
| C, ETFs only | +0.47% | −5.02% | −11.72% | 81.8% | 3.9% | 1.0% |
| Round 1 winner (benchmark) | +0.96% | −6.62% | −10.74% | — | 14.3% | 7.2% |

**Why not C, when it scores highest?** All of its edge comes from single stocks. With the
stocks removed it falls below A. The stocks are today's 20 largest names (NVDA, PLTR, AVGO and
the rest), so a back-test that picks among them already knows who won. The benchmark has the same
pattern: strong history, weak live. The one test free of survivorship bias is the live Round 2
period, and there C lost 4.88% while B made 3.14%. B is the best design among those whose
history is not biased.

### 3. Round 2 replay (7 Jul – 9 Oct 2026, the template's `run_bot`)

| Bot | Full window | Mean of 11 rolling 14-session windows | Worst / best window |
|---|---|---|---|
| **This bot (B)** | +3.14% | +1.11% | −5.93% / +10.37% |
| A | +0.00% | +0.44% | −5.86% / +9.33% |
| C, momentum picker | −4.88% | −0.64% | −5.21% / +3.48% |
| Round 1 winner (benchmark) | −2.99% | +1.04% | −5.99% / +7.61% |
| QQQ benchmark file (capped at 30% by the engine) | +1.57% | +0.42% | −1.36% / +2.42% |

### Honest limits

- Order of work: first C (lost in the replay), then A, then the long study. The study chose B
  over A by a rule fixed in advance. Even so, the Round 2 replay was seen before the study, so
  it does not count as independent evidence.
- B accepts deeper drawdowns than A (worst 14-session window −19.6% against −14.6%) in exchange
  for a higher chance of a large gain. That matches a contest ranked on raw return over a short
  window. It is not a recommendation for real money.
- Overlapping windows are not independent samples, and Yahoo data gets revised.

## Run it

```bash
python preview.py            # admission safety preview, standard library only
```

`strategy_selftest.py` was removed because it tested the template's sample agent, not this one.
`research/` holds the replay and study scripts. They need `yfinance` and network access, and they
are not used by the bot.

## License

MIT. See [LICENSE](LICENSE). Template code is © builderr; the agent and the research scripts are
© Fury Oktria Putra.
