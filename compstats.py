"""Computational statistics by experiment, read from the solve logs stored with every
result file (Section 5.1, Table S17)."""
import json, statistics


def _load(f, key="solve_log"):
    d = json.load(open(f))
    return d if isinstance(d, list) else d.get(key, [])


def experiments():
    mc_rows = [json.loads(l) for l in open("mc_rows.jsonl")]
    mc = [l for r in mc_rows for l in r["log"]]
    ex = _load("extra.json"); ex_own = ex[:len(ex) - len(mc)]
    J = json.load(open("joint.json"))
    joint = [dict(seconds=J["maxprofit"]["seconds"], sol_status=J["maxprofit"]["sol_status"]),
             dict(seconds=J["compromise"]["phase1"]["seconds"], sol_status=J["compromise"]["phase1"]["sol_status"]),
             dict(seconds=J["compromise"]["phase2"]["seconds"], sol_status=J["compromise"]["phase2"]["sol_status"])]
    s1 = [dict(seconds=l["seconds"], sol_status=1 if l["status"] == "Optimal" else -1)
          for l in json.load(open("stage1_solve_log.json"))]
    return [
        ("Stage~1 siting (both phases, all variants)", "CBC", s1),
        ("Payoff, compromise, scalarisations, learning, sensitivity, mandates, facility loss", "HiGHS", _load("results.json")),
        ("Allocation grid and transport probe", "HiGHS", ex_own),
        ("Monte Carlo (120 draws)", "HiGHS", mc),
        ("Equal-cost sitings, fixed schedule", "HiGHS", _load("equity_enum.json")),
        ("Equal-cost sitings, maximum profit", "HiGHS", _load("tied_maxprofit.json")),
        ("Joint siting model", "HiGHS", joint),
        ("Compromise on joint sites", "HiGHS", _load("joint_sites.json")),
        ("Regional employment and share floors", "HiGHS", _load("equity_regional.json")),
        ("Learning-rate sweep", "HiGHS", _load("lr_solve_log.json")),
        ("Staffing-floor sweep", "HiGHS", _load("employment.json")),
        ("Coverage-radius check", "HiGHS", _load("radius.json")),
        ("Lower volume and physical feasibility", "HiGHS", _load("lowvol.json")),
        ("Recovery mandates and processing-cost grid", "HiGHS", _load("recovery.json")),
        ("Capacity utilisation at the compromise", "HiGHS", _load("caputil.json")),
        ("Benchmark transport cost (core, equity enumeration, radius)", "HiGHS",
         _load("bench/results.json") + _load("bench/equity_enum.json") + _load("bench/radius.json")),
    ]


def summary(logs):
    t = [l["seconds"] for l in logs]
    return dict(n=len(logs), total=sum(t), median=statistics.median(t) if t else 0.0, max=max(t) if t else 0.0,
                superseded=sum(1 for l in logs if l.get("superseded")),
                limited=sum(1 for l in logs if l.get("sol_status") == 2 and not l.get("superseded")),
                infeasible=sum(1 for l in logs if l.get("sol_status") == -1))


if __name__ == "__main__":
    for name, solver, logs in experiments():
        print(name, solver, summary(logs))
