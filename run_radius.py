"""Price of the coverage radii: maximum profit of the intact Stage 1 network with the
radii as planned, with the segregation radius R2 lifted, and with both lifted.
Writes radius.json."""
import json
import model as M
out = {}
for tag, rl in (("radii", None), ("no_R2", {"cc": list(range(len(M.CC)))}),
                ("no_R1_R2", {"city": list(M.I), "cc": list(range(len(M.CC)))})):
    m, Z = M.build(relax=rl); M.solve(m, Z["Z1"])
    v = M.val(Z)
    v["open_sc"] = [M.SC_NAMES[k] for k in range(len(M.SC))
                    if any((m.variablesDict().get(f"aK_{k}_{t}").varValue or 0) > 0.5 for t in range(M.T))]
    out[tag] = v; print(tag, v, flush=True)
out["solve_log"] = M.SOLVE_LOG
json.dump(out, open("radius.json", "w"), indent=1, default=float)
