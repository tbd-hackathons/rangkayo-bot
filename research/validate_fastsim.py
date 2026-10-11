import importlib.util, json, sys, pathlib
sys.path.insert(0, sys.argv[3]); import fastsim
spec = importlib.util.spec_from_file_location("lr", sys.argv[1]); lr = importlib.util.module_from_spec(spec); spec.loader.exec_module(lr)
bars = json.load(open(sys.argv[2])); data = fastsim.Data(bars)
for a in sys.argv[4:]:
    d = lr.load_decide_from(pathlib.Path(a)); r1 = lr.run_bot(d, bars, "2026-07-07")
    d = lr.load_decide_from(pathlib.Path(a)); r2 = fastsim.run(d, data, "2026-07-07", "2099")
    print(pathlib.Path(a).name, "run_bot=%+.4f%% fastsim=%+.4f%%" % (r1["ret"]*100, r2["ret"]*100))
