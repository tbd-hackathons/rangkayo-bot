"""Fetch the Round 2 universe bars once using Builderr's own live_runner.fetch_bars, cache to JSON."""
import importlib.util, json, sys
lr_path, out = sys.argv[1], sys.argv[2]
spec = importlib.util.spec_from_file_location("live_runner", lr_path)
lr = importlib.util.module_from_spec(spec); spec.loader.exec_module(lr)
bars = lr.fetch_bars()
json.dump(bars, open(out, "w"))
print("tickers", len(bars), "last", max(b[-1]["ts"] for b in bars.values()))
