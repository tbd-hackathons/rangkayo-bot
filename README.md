# Steady Beta with a Brake

An entry for [builderr Trading, Round 2](https://builderr.ai/trading-v0). Forked from the
[builderr starter template](https://github.com/builderr-ai/builderr-trading-template) (MIT).

The bot is [`agent.py`](agent.py). It is about 150 lines of standard-library Python, with no
network calls, no LLM and no data files.

## What it does

It holds a fixed book of big US index and chip ETFs and changes how much it holds based on the
Nasdaq's trend.

| State | When (decided on the prior close) | Book | Beta-adjusted gross |
|---|---|---|---|
| **ON** | QQQ and SPY above their 50-day averages, QQQ 20-day volatility below 30% | QQQ 25%, SMH 25%, SPY 25%, TQQQ 20% | 1.35x |
| **STEADY** | Trend wobbling, but no break | QQQ 25%, SMH 25%, SPY 25% | 0.75x |
| **CASH** | QQQ down 5% in 5 days, or QQQ volatility above 40%, or QQQ more than 3% under its 50-day average | nothing | 0x |

Why this shape for a window of about 14 sessions:

- Over two or three weeks, most of a book's return comes from how much market exposure it holds.
  Switching names and states costs slippage and causes whipsaw.
- The 1x core stays in place through small dips. Only the leveraged slice switches off, so the bot
  does not sit in cash while the market rebounds.
- The brake exits only on a real break, which keeps a crash from ending the entry.

## Limits, by construction

- Long-only, no borrowing. Buys never spend the last 1.5% of equity.
- The largest target weight is 25%. Any name that drifts above 27% is trimmed (the cap is 30%).
- Beta-adjusted gross targets 1.35x. The book is rebalanced if it drifts above 1.42x (the cap is 1.5x).
- Stateless. Every call recomputes from the bars and positions it is given, and uses only past bars.
- It trades only tickers in the live scorer's fetch list (`ROUND2_FETCH_UNIVERSE` in `live_runner.py`).

## Local results, reported as measured

**`python preview.py`** (the three public sample windows from the template):

| Window | Return | Max drawdown | Trades |
|---|---|---|---|
| calm_uptrend (Jun–Aug 2021) | +15.81% | 3.83% | 8 |
| moderate_selloff (Sep–Oct 2021) | −8.41% | 9.34% | 25 |
| vol_spike_snapback (Feb–Apr 2020) | −11.26% | 11.26% | 20 |

Safety bar: all PASS. Peak gross 1.42x, peak single name 26%, worst drawdown 11.3%.

**Round 2 replay.** I ran the bot through the template's own `live_runner.run_bot` on Yahoo daily
bars for the 42 live tickers, from 7 Jul to 9 Oct 2026. On the same data the replay reproduced the
benchmark's published Round 2 return exactly (−2.99%).

| Bot | 7 Jul – 9 Oct 2026 | Mean of 11 rolling 14-session windows | Worst / best window |
|---|---|---|---|
| This bot | +0.00% | +0.44% | −5.86% / +9.33% |
| Round 1 winner (benchmark) | −2.99% | +1.04% | −5.99% / +7.61% |
| QQQ buy-and-hold | +1.57% | +0.42% | −1.36% / +2.42% |

Read these numbers with care:

- **The replay is in-sample for this version.** My first design, a momentum stock picker with a
  TQQQ sleeve, used rules I fixed before any test. In the same replay it lost −4.88%, and its
  rolling-window mean was −0.64%. I chose this simpler design after seeing that result, so the
  replay is not independent evidence for it.
- The rolling windows overlap, and there are only 11 of them. They show the spread of outcomes,
  not a forecast.
- Moving each parameter ±20% left the full-window result between −1.1% and +3.2%, with no
  collapse. I kept the original parameters and did not pick the best variant.

## Run it

```bash
python preview.py            # admission safety preview, standard library only
```

`strategy_selftest.py` was removed because it tested the template's sample agent, not this one.
`research/` holds the replay scripts. They need `yfinance` and network access, and they are not
used by the bot.

## License

MIT. See [LICENSE](LICENSE). Template code is © builderr; the agent and the research scripts are
© Fury Oktria Putra.
