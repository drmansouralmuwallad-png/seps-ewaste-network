"""Run every reported experiment from the recovered data. Checkpoints to results.json
after each block so partial progress survives."""
import json, os, time, random, statistics, sys
import model as M

OUT = "results.json"
R = json.load(open(OUT)) if os.path.exists(OUT) else {}


def save():
    json.dump(R, open(OUT, "w"), indent=1, default=float)


def log(s):
    print(f"[{time.strftime('%H:%M:%S')}] {s}", flush=True)


t0 = time.time()

# ---------------------------------------------------------------- payoff
if "payoff" not in R:
    log("payoff matrix ...")
    R["payoff"] = M.payoff(); save()
pm = R["payoff"]
ideal = {k: pm[k][k] for k in ("Z1", "Z2", "Z3")}
bnd = M.bounds_of(pm)
R["ideal"], R["bounds"] = ideal, {k: list(v) for k, v in bnd.items()}
for k, v in pm.items():
    log(f"   max {k}: {v['Z1']/1e6:9.2f} M SAR  {v['Z2']:6.2f}%  {v['Z3']:8.0f} jobs")

# ---------------------------------------------------------------- compromise
if "maxmin" not in R:
    log("fuzzy max-min compromise ...")
    R["maxmin"] = M.maxmin(bnd); save()
mm = R["maxmin"]; mm["NOS"] = M.nos(mm, ideal)
log(f"   {mm['Z1']/1e6:.2f} M SAR  {mm['Z2']:.2f}%  {mm['Z3']:.0f} jobs  "
    f"lam*={mm['lam']:.4f} (check {mm['lam_check']:.4f})  NOS={mm['NOS']:.4f}")

# ---------------------------------------------------------------- weighted sum
if "ws" not in R:
    log("weighted sum, 10 configurations ...")
    grid = [(0.50, .25, .25), (0.33, .33, .34), (0.25, .25, .50), (0.60, .20, .20),
            (0.20, .50, .30), (0.40, .40, .20), (0.70, .15, .15), (0.20, .20, .60),
            (0.15, .70, .15), (0.45, .30, .25)]
    ws = []
    for w1, w2, w3 in grid:
        r = M.weighted({"Z1": w1, "Z2": w2, "Z3": w3}, ideal)
        r["NOS"] = M.nos(r, ideal); ws.append(r)
        log(f"   w=({w1:.2f},{w2:.2f},{w3:.2f}) {r['Z1']/1e6:8.2f} {r['Z2']:6.2f} "
            f"{r['Z3']:8.0f} NOS={r['NOS']:.4f}")
    R["ws"] = ws; save()

# ---------------------------------------------------------------- epsilon
if "ec" not in R:
    log("epsilon-constraint, 10 configurations ...")
    ul, uh = bnd["Z2"]; el, eh = bnd["Z3"]
    ec = []
    for i in range(10):
        eu = ul + (uh - ul) * i / 12.0
        ee = el + (eh - el) * i / 12.0
        try:
            r = M.epsilon(eu, ee)
            r["NOS"] = M.nos(r, ideal)
        except M.NotSolved as e:
            r = dict(eps=(eu, ee), status=str(e))
        ec.append(r)
        if "Z1" in r:
            log(f"   eps=({eu:6.2f},{ee:8.0f}) {r['Z1']/1e6:8.2f} {r['Z2']:6.2f} "
                f"{r['Z3']:8.0f} NOS={r['NOS']:.4f}")
    R["ec"] = ec; save()

# ---------------------------------------------------------------- learning
if "learning" not in R:
    log("learning on/off ...")
    off_pm = M.payoff(learning=False)
    off = M.maxmin(M.bounds_of(off_pm), learning=False)
    R["learning"] = dict(on=mm, off=off); save()
    log(f"   no learning: {off['Z1']/1e6:.2f} M SAR  {off['Z3']:.0f} jobs")

# ---------------------------------------------------------------- sensitivity
if "sens" not in R:
    log("sensitivity ...")
    rows = []
    import numpy as np
    for label, kw, deltas in [
            ("E-waste collection volume", "gen", (-0.10, 0.10)),
            ("Market demand", "dem", (-0.10, 0.10)),
            ("Fuel price", "fuel", (-0.10, 0.10)),
            ("Selling prices", "price", (-0.15, 0.15)),
            ("Collection capacity", "cap", (-0.25,))]:
        for dd in deltas:
          for attempt in (0, 1):
            # a case stopped by the time limit is re-solved once with a 3,600 s limit
            M.SOLVE_TLIM = 300 if attempt == 0 else 3600
            try:
                if kw == "gen":
                    r = M.maxmin(bnd, gen=M.EWASTE * (1 + dd))
                elif kw == "fuel":
                    r = M.maxmin(bnd, p={"fuel": M.FP * (1 + dd)})
                elif kw == "price":
                    r = M.maxmin(bnd, p={"pr": M.PR*(1+dd), "pl": M.PL*(1+dd),
                                         "pi": M.PI*(1+dd)})
                elif kw == "cap":
                    r = M.maxmin(bnd, cap_scale={"cc": 1 + dd})
                else:
                    old = (M.DL[:], M.DI[:], M.DR[:])
                    M.DL[:] = [v*(1+dd) for v in old[0]]
                    M.DI[:] = [v*(1+dd) for v in old[1]]
                    M.DR[:] = [v*(1+dd) for v in old[2]]
                    r = M.maxmin(bnd)
                    M.DL[:], M.DI[:], M.DR[:] = old
                rows.append(dict(parameter=label, change=dd,
                                 dZ1=100*(r["Z1"]-mm["Z1"])/abs(mm["Z1"]),
                                 dZ3=100*(r["Z3"]-mm["Z3"])/abs(mm["Z3"]),
                                 dZ2=r["Z2"]-mm["Z2"]))
                log(f"   {label:26s} {dd:+.0%}  profit {rows[-1]['dZ1']:+6.2f}%  "
                    f"jobs {rows[-1]['dZ3']:+6.2f}%  util {rows[-1]['dZ2']:+5.2f}pp")
                break
            except M.NotSolved as e:
                if "sol_status 2" in str(e) and attempt == 0:
                    log(f"   {label:26s} {dd:+.0%}  time limit; retrying with 3,600 s")
                    M.SOLVE_LOG[-1]["superseded"] = True
                    continue
                rows.append(dict(parameter=label, change=dd, status=str(e)))
                log(f"   {label:26s} {dd:+.0%}  {e}")
                break
    M.SOLVE_TLIM = 300
    R["sens"] = rows; save()

# ---------------------------------------------------------------- recovery targets
if "recovery" not in R:
    log("recovery targets ...")
    rec = []
    for name, a, b in [("Conservative (70%)", 0.25, 0.45), ("Baseline (80%)", 0.30, 0.50),
                       ("Ambitious (90%)", 0.35, 0.55)]:
        r = M.maxmin(bnd, p={"alpha": a, "beta": b})
        rec.append(dict(name=name, alpha=a, beta=b, gamma=round(1-a-b, 2), **r))
        log(f"   {name:20s} {r['Z1']/1e6:8.2f} M SAR  {r['Z3']:8.0f} jobs")
    R["recovery"] = rec; save()

# ---------------------------------------------------------------- disruption
# Every single-facility loss, tier by tier, for all six periods. For each loss:
#   uncovered   cities (collection loss) or collection centres (segregation loss) left with
#               no surviving facility within the coverage radius;
#   strict      Stage 2 re-solved with the radii enforced for everyone; infeasible by
#               construction if anything is uncovered;
#   contingency Stage 2 re-solved with the radius lifted for the lost facility's service
#               area (the cities Stage 1 assigned to a lost collection centre, or every
#               collection centre if a segregation centre is lost), i.e. emergency long
#               hauls; reports compromise and profit-maximum, and the longest haul needed
#               by an uncovered node.
if "disruption" not in R:
    log("disruption ...")
    dis = []
    tiers = [("cc", "Collection", M.CC_NAMES), ("sc", "Segregation", M.SC_NAMES),
             ("rc", "Recycling", list(M.RC_ANCHOR)), ("rf", "Refurbishing", M.RF_NAMES)]
    for tier, tname, names in tiers:
        for i, nm in enumerate(names):
            relax, haul = {}, 0.0
            if tier == "cc":
                rest = [M.CC[j] for j in range(len(M.CC)) if j != i]
                unc = [c for c in M.I if not any(M.DIST[c][k] <= M.R1 for k in rest)]
                lost = M.CC_NAMES[i]
                served = [M.CITIES.index(a.split("->")[0]) for a, f in M.S1_FRAC.items()
                          if a.split("->")[1] == lost and f > 1e-9]
                relax = {"city": sorted(set(unc) | set(served))}
                haul = max((min(M.DIST[c][k] for k in rest) for c in unc), default=0.0)
                unc_names = [M.CITIES[c] for c in unc]
            elif tier == "sc":
                rest = [M.SC[k] for k in range(len(M.SC)) if k != i]
                unc = [j for j in range(len(M.CC)) if not any(M.DIST[M.CC[j]][k] <= M.R2 for k in rest)]
                relax = {"cc": list(range(len(M.CC)))}
                haul = max((min(M.DIST[M.CC[j]][k] for k in rest) for j in unc), default=0.0)
                unc_names = [M.CC_NAMES[j] for j in unc]
            else:
                unc_names = []
            rec = dict(tier=tname, site=nm, uncovered=unc_names, longest_haul=haul)
            if not unc_names:
                try:
                    M.maxmin(bnd, closed=((tier, i),)); rec["strict_feasible"] = True
                except M.NotSolved as e:
                    rec["strict_feasible"] = False; rec["strict_status"] = str(e)
            else:
                rec["strict_feasible"] = False; rec["strict_status"] = "coverage lost"
            try:
                r = M.maxmin(bnd, closed=((tier, i),), relax=relax)
                mp, Zp = M.build(closed=((tier, i),), relax=relax); M.solve(mp, Zp["Z1"])
                pmax = M.val(Zp)["Z1"]
                rec.update(feasible=True, Z2=r["Z2"], lam=r["lam"], Z1max=pmax,
                           dZ1=100*(r["Z1"]-mm["Z1"])/abs(mm["Z1"]),
                           dZ3=100*(r["Z3"]-mm["Z3"])/abs(mm["Z3"]),
                           dZ1max=100*(pmax-ideal["Z1"])/abs(ideal["Z1"]))
                log(f"   {tname+': '+nm:32s} uncovered {len(unc_names)}  strict "
                    f"{'ok' if rec['strict_feasible'] else 'no'}  compromise {rec['dZ1']:+6.2f}%  "
                    f"max-profit {rec['dZ1max']:+6.2f}%  haul {haul:.0f} km")
            except M.NotSolved as e:
                rec.update(feasible=False, status=str(e))
                log(f"   {tname+': '+nm:32s} {e}")
            dis.append(rec)
    R["disruption"] = dis; save()

R["solve_log"] = M.SOLVE_LOG
log(f"core complete in {time.time()-t0:.0f}s")
save()
