"""Why do some Monte Carlo draws fail? Physical feasibility with and without radii,
and the catchment that overflows (cities whose only reachable collection centres are
a given set)."""
import json, itertools
import numpy as np, pulp
import model as M, run_mc
rows=[json.loads(l) for l in open("mc_rows.jsonl")]
bad=[r["i"] for r in rows if not r["ok"]]
G=run_mc.draws()
reach={i:[j for j in range(len(M.CC)) if M.DIST[i][M.CC[j]]<=M.R1] for i in M.I}
out=[]
for i in bad:
    g=G[i]; rec=dict(i=i)
    m,Z=M.build(gen=g); rec["phys"]=M.solve(m,Z["Z1"],strict=False)
    m,Z=M.build(gen=g,relax={"city":list(M.I)}); rec["phys_relaxed"]=M.solve(m,Z["Z1"],strict=False)
    # Hall-type check: for each set S of centres, cities reachable only to S must fit
    worst=None
    for n in (1,2):
        for S in itertools.combinations(range(len(M.CC)),n):
            cities=[c for c in M.I if reach[c] and set(reach[c])<=set(S)]
            for t in range(M.T):
                over=sum(g[c,t] for c in cities)-M.CAP_CC*n
                if over>1e-6 and (worst is None or over>worst[0]):
                    worst=(over,[M.CC_NAMES[j] for j in S],t+1)
    rec["overflow"]=worst; out.append(rec); print(rec,flush=True)
json.dump(out,open("diag_mc.json","w"),indent=1,default=str)
