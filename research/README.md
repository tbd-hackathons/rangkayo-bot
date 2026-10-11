# Replay scripts (not used by the bot)

```bash
pip install yfinance
python research/fetch_round2_bars.py live_runner.py /tmp/bars.json
python research/replay_round2.py live_runner.py /tmp/bars.json mine=agent.py qqq=qqq_benchmark.py
```

`fetch_round2_bars.py` calls the template's own `live_runner.fetch_bars()`. `replay_round2.py` scores
each agent with `live_runner.run_bot()` from 7 Jul 2026, and then over rolling 14-session windows.
Yahoo data is revised over time, so later runs can differ slightly.

## Long-history study

```bash
python research/fetch_long_history.py /tmp/long.json QQQ,SPY,SMH,TQQQ,...   # the 42 live tickers
python research/study_windows.py /tmp/long.json agent.py A=a.py B=b.py ...  # writes /tmp/study_rows.json
python research/score_study.py /tmp/study_rows.json A,B,...,E              # E must be the benchmark
python research/validate_fastsim.py live_runner.py /tmp/bars.json research agent.py
```

`fastsim.py` follows the rules of `live_runner.run_bot`, but trims history to the last 320 bars so
it runs fast. `validate_fastsim.py` checks that it matches `run_bot`.
