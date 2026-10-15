"""Monte Carlo on generation (Section 5.8): N scenarios, each city-period generation drawn
independently within +/-10% of its estimate; Stage 2 compromise re-solved against the
baseline payoff bounds. Scenarios are independent, so they can be split across workers:
    python3 run_mc.py WORKER NWORKERS     (appends to mc_rows.jsonl)
    python3 run_mc.py retry WORKER NWORKERS  (re-solves time-limited scenarios, keeping the incumbent)
    python3 run_mc.py collect             (merges retries, writes the summary into extra.json)"""
import json, os, random, statistics, sys, time
import numpy as np
import model as M

N = int(os.environ.get("MC_N", "120"))
OUT = "mc_rows.jsonl"


def draws():
    rng = random.Random(20260919)
    return [M.EWASTE * np.array([[rng.uniform(0.9, 1.1) for _ in range(M.T)] for _ in range(24)])
            for _ in range(N)]


def work(w, nw):
    R = json.load(open("results.json")); bnd = {k: tuple(v) for k, v in R["bounds"].items()}
    done = set()
    if os.path.exists(OUT):
        done = {json.loads(l)["i"] for l in open(OUT)}
    G = draws()
    for i in range(w, N, nw):
        if i in done:
            continue
        t0 = time.time(); n0 = len(M.SOLVE_LOG)
        try:
            r = M.maxmin(bnd, gen=G[i])
            rec = dict(i=i, ok=True, Z1=r["Z1"], Z2=r["Z2"], Z3=r["Z3"])
        except M.NotSolved as e:
            rec = dict(i=i, ok=False, status=str(e))
        rec["seconds"] = time.time() - t0; rec["log"] = M.SOLVE_LOG[n0:]
        with open(OUT, "a") as f:
            f.write(json.dumps(rec, default=float) + "\n")
        print(i, rec.get("Z1"), round(rec["seconds"], 1), flush=True)


def retry(w=0, nw=1, tlim=300):
    """Re-solve scenarios stopped by the time limit, keeping the best design found; the
    row is marked uncertified if the 1% gap was still not reached."""
    M.SOLVE_TLIM = tlim; M.STRICT = False
    R = json.load(open("results.json")); bnd = {k: tuple(v) for k, v in R["bounds"].items()}
    rows = [json.loads(l) for l in open(OUT)]
    G = draws()
    todo = [r["i"] for r in rows if not r["ok"] and "sol_status 2" in r.get("status", "")]
    for i in todo[w::nw]:
        t0 = time.time(); n0 = len(M.SOLVE_LOG)
        try:
            r = M.maxmin(bnd, gen=G[i]); rec = dict(i=i, ok=True, Z1=r["Z1"], Z2=r["Z2"], Z3=r["Z3"])
            rec["certified"] = all(l["sol_status"] == 1 for l in M.SOLVE_LOG[n0:])
        except M.NotSolved as e:
            rec = dict(i=i, ok=False, status=str(e))
        rec["seconds"] = time.time() - t0; rec["log"] = M.SOLVE_LOG[n0:]; rec["retried"] = tlim
        with open(f"mc_retry_{w}.jsonl", "a") as f:
            f.write(json.dumps(rec, default=float) + "\n")
        print(i, rec.get("Z1"), round(rec["seconds"], 1), flush=True)


def merge_retries():
    rows = {json.loads(l)["i"]: json.loads(l) for l in open(OUT)}
    for fn in [f for f in os.listdir(".") if f.startswith("mc_retry_")]:
        for l in open(fn):
            r = json.loads(l); rows[r["i"]] = r
    with open(OUT, "w") as f:
        for i in sorted(rows):
            f.write(json.dumps(rows[i], default=float) + "\n")


def collect():
    rows = [json.loads(l) for l in open(OUT)]
    assert sorted(r["i"] for r in rows) == list(range(N)), "missing scenarios"
    ok = [r for r in rows if r["ok"]]
    prof = sorted(r["Z1"] for r in ok)
    X = json.load(open("extra.json"))
    X["mc"] = dict(n=N, infeasible=len(rows) - len(ok), mean=statistics.fmean(prof),
                   median=statistics.median(prof),
                   cv=statistics.pstdev(prof) / abs(statistics.fmean(prof)),
                   p05=prof[int(0.05 * len(prof))], p95=prof[int(0.95 * len(prof))],
                   emp_mean=statistics.fmean(r["Z3"] for r in ok),
                   util_mean=statistics.fmean(r["Z2"] for r in ok),
                   statuses=sorted({r.get("status", "ok") for r in rows}),
                   uncertified=sum(1 for r in ok if r.get("certified") is False))
    X["solve_log"] = X.get("solve_log", []) + [l for r in rows for l in r["log"]]
    json.dump(X, open("extra.json", "w"), indent=1, default=float)
    print(X["mc"])


if __name__ == "__main__":
    if sys.argv[1] == "collect":
        merge_retries(); collect()
    elif sys.argv[1] == "retry":
        retry(int(sys.argv[2]), int(sys.argv[3]))
    else:
        work(int(sys.argv[1]), int(sys.argv[2]))
