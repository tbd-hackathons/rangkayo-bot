# Replay scripts (not used by the bot)

```bash
pip install yfinance
python research/fetch_round2_bars.py live_runner.py /tmp/bars.json
python research/replay_round2.py live_runner.py /tmp/bars.json mine=agent.py qqq=qqq_benchmark.py
```

`fetch_round2_bars.py` calls the template's own `live_runner.fetch_bars()`. `replay_round2.py` scores
each agent with `live_runner.run_bot()` from 7 Jul 2026, and then over rolling 14-session windows.
Yahoo data is revised over time, so later runs can differ slightly.
