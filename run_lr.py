"""Learning-rate sweep (Fig. 5): for each LR in {0.75, ..., 0.95} the payoff matrix and
the compromise are re-solved. The learning rate is a model assumption rather than a
scenario, and with fast learning the employment attainable falls below the baseline
lower bound, so each rate is normalised on its own payoff bounds (as is the no-learning
case in run_core.py). Writes lr_sweep.json."""
import json, math
import model as M

out = []
orig = M.B_LEARN
for lr in (0.75, 0.80, 0.85, 0.90, 0.95):
    M.B_LEARN = -math.log2(lr)
    pm = M.payoff()
    r = M.maxmin(M.bounds_of(pm))
    out.append(dict(LR=lr, Z1=r["Z1"], Z2=r["Z2"], Z3=r["Z3"], lam=r["lam"],
                    maxjobs=pm["Z3"]["Z3"]))
    print(f"LR={lr:.2f}  {r['Z1']/1e6:.4f} M SAR  {r['Z2']:.2f}%  {r['Z3']:.0f} jobs", flush=True)
M.B_LEARN = orig
json.dump(out, open("lr_sweep.json", "w"), indent=1)
json.dump(M.SOLVE_LOG, open("lr_solve_log.json", "w"), indent=1, default=float)
