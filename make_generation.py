"""City-level e-waste quantities for the case study (Section 5.1, Table S1).

Each node stands for the governorate it serves. The tonnage the network handles in
period t is an assumed formal collection volume V_t (kept from the study data,
realdata_original.json), and it is allocated to nodes in proportion to their Saudi
Census 2022 population (population.json):

    EW_it = V_t * pop_i / sum_j pop_j,

rounded to whole tonnes by largest remainder so that every period total is exactly V_t.
A single per-capita collection rate therefore applies to every node.
Writes the generation matrix into realdata.json; distances are unchanged."""
import json
import numpy as np

orig = json.load(open("realdata_original.json"))
P = json.load(open("population.json"))["nodes"]
C = orig["cities"]
pop = np.array([P[c]["pop"] for c in C], dtype=float)
V = np.array(orig["ewaste"], dtype=float).sum(axis=0)          # tonnes per period
share = pop / pop.sum()
G = np.zeros((len(C), len(V)), dtype=int)
for t, v in enumerate(V):
    raw = v * share
    base = np.floor(raw).astype(int)
    rest = int(round(v)) - base.sum()
    order = np.argsort(-(raw - base), kind="stable")
    base[order[:rest]] += 1
    G[:, t] = base
assert (G.sum(axis=0) == V.round().astype(int)).all()
out = dict(orig); out["ewaste"] = G.tolist()
json.dump(out, open("realdata.json", "w"))
kg = 1000 * V / pop.sum() * 1000                 # kg per 1,000 residents per period
print("period totals", V.tolist())
print(f"collection rate {kg.mean():.2f} kg per 1,000 residents per period (all nodes)")
for c, g in zip(C, G):
    print(f"{c:15s} {g.tolist()}")
