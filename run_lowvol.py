"""A 10% fall in collected volume. Against the baseline payoff bounds the compromise has
no solution, because employment cannot reach the baseline floor L_3 with less tonnage
to handle. The network itself remains feasible; this script reports the profit and
employment maxima at the lower volume and the compromise under that scenario's own
payoff bounds. Writes lowvol.json."""
import json
import pulp
import model as M

R = json.load(open("results.json")); mm = R["maxmin"]
g = M.EWASTE * 0.9
pm = M.payoff(gen=g)
b = M.bounds_of(pm)
r = M.maxmin(b, gen=g)
out = dict(payoff=pm, bounds=b, compromise=r,
           maxjobs=pm["Z3"]["Z3"], baseline_L3=R["bounds"]["Z3"][0],
           maxprofit=pm["Z1"]["Z1"],
           dZ1=100 * (r["Z1"] - mm["Z1"]) / mm["Z1"], dZ3=100 * (r["Z3"] - mm["Z3"]) / mm["Z3"],
           dZ2=r["Z2"] - mm["Z2"], solve_log=M.SOLVE_LOG)
json.dump(out, open("lowvol.json", "w"), indent=1, default=float)
print(f"max jobs {out['maxjobs']:.0f} vs baseline L3 {out['baseline_L3']:.0f}; "
      f"own-bounds compromise {r['Z1']/1e6:.2f} M SAR ({out['dZ1']:+.2f}%), {r['Z3']:.0f} jobs, {r['Z2']:.2f}%")

# Physical feasibility of the infeasible sensitivity cases (profit maximisation, no
# compromise): with the coverage radii as in Stage 1, and with the collection radius
# lifted. The binding catchment is the set of cities whose only centre within R1 is one
# given centre ("captive" load).
reach = {i: [j for j in range(len(M.CC)) if M.DIST[i][M.CC[j]] <= M.R1] for i in M.I}
captive = {}
for j in range(len(M.CC)):
    cs = [c for c in M.I if reach[c] == [j]]
    captive[M.CC_NAMES[j]] = max(float(sum(M.EWASTE[c, t] for c in cs)) for t in range(M.T))
phys = {}
for name, kw in (("vol+10", dict(gen=M.EWASTE * 1.1)), ("vol-10", dict(gen=M.EWASTE * 0.9)),
                 ("cap-25", dict(cap_scale={"cc": 0.75}))):
    row = {}
    for tag, rl in (("radii", None), ("no_R1", {"city": list(M.I)})):
        m, Z = M.build(relax=rl, **kw)
        row[tag] = M.solve(m, Z["Z1"], strict=False)
        if row[tag] == "Optimal":
            row[tag + "_Z1"] = pulp.value(Z["Z1"])
    phys[name] = row
out["physical"] = phys; out["captive_peak"] = captive; out["cap_cc"] = M.CAP_CC
json.dump(out, open("lowvol.json", "w"), indent=1, default=float)
print(phys); print(captive)
