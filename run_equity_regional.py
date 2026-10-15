"""Where the jobs go: regional distribution of employment with and without the equity
rule (Section 5.4), and what an employment-based equity rule would buy.

Employment is attributed to the region of the facility that creates it, following
Eq. (17): the tonnage term (collected tonnage / WC_t) to the collection centre that
receives the tonnage, and the staffing floor e_min to every operating facility.
"Lower-income" means outside the two highest-income regions (Riyadh, Eastern; GASTAT
HIES 2018), the definition of the equity rule as written; "outside the corridor" also
excludes Makkah (the wide variant).

Part A re-solves the Stage 2 compromise (baseline payoff bounds, two phases) for the
segregation siting chosen with and without the equity rule and for the best siting under
each stricter variant (from equity_enum.json), and reports facility locations and the
employment split.
Part B adds an employment-share floor to Stage 2, sum(lower-income worker-periods) >=
s * Z3, and raises s until the compromise has no solution, to see how far any rule could
move employment towards lower-income regions within this network.
Writes equity_regional.json."""
import json
import pulp
import model as M
import stage1 as S1

R = json.load(open("results.json")); BND = {k: tuple(v) for k, v in R["bounds"].items()}
E = json.load(open("equity_enum.json"))
S1J = json.load(open("stage1.json"))
POP = json.load(open("population.json"))
DELTA = 0.10
REGION = dict(S1.REGION)
# Downstream sites that are not among the 24 cities (anchored to a city for distances)
RC_REGION = {"Turbarjal": "Al-Jouf", "Ad Dilam": "Riyadh", "Umm Lajj": "Tabuk"}
HIGH, WIDE = S1.H, S1.H_WIDE


def facility_regions():
    reg = {}
    for j, c in enumerate(M.CC): reg[("cc", j)] = REGION[M.CITIES[c]]
    for k, c in enumerate(M.SC): reg[("sc", k)] = REGION[M.CITIES[c]]
    for l, n in enumerate(M.RC_ANCHOR): reg[("rc", l)] = RC_REGION[n]
    for f, n in enumerate(M.RF_NAMES): reg[("rf", f)] = REGION[n]
    return reg


ATTR = "collection"      # where the tonnage-related labour of Eq. (17) is placed


def employment_terms(m, attr=None):
    """Linear expressions: worker-periods by region (dict region -> expr).
    Eq. (17) fixes how many worker-periods a design needs, not where they work: every
    collected tonne also passes through a segregation centre, so the tonnage term can be
    placed at the collection centre that receives the tonnage (attr="collection") or at
    the segregation centre that sorts it (attr="segregation"); totals are identical."""
    attr = attr or ATTR
    V = m.variablesDict(); reg = facility_regions(); out = {}
    for t in range(M.T):
        w = 1.0 / M.wc(t)
        for j in range(len(M.CC)):
            e = M.E_MIN * V[f"aJ_{j}_{t}"]
            if attr == "collection":
                e = e + pulp.lpSum(w * V[f"x_{i}_{j}_{t}"] for i in M.I)
            out.setdefault(reg[("cc", j)], []).append(e)
        for k in range(len(M.SC)):
            e = M.E_MIN * V[f"aK_{k}_{t}"]
            if attr == "segregation":
                e = e + pulp.lpSum(w * V[f"q_{j}_{k}_{t}"] for j in range(len(M.CC)))
            out.setdefault(reg[("sc", k)], []).append(e)
        for l in range(3):
            out.setdefault(reg[("rc", l)], []).append(M.E_MIN * V[f"aL_{l}_{t}"])
        for f in range(3):
            out.setdefault(reg[("rf", f)], []).append(M.E_MIN * V[f"aM_{f}_{t}"])
    return {r: pulp.lpSum(v) for r, v in out.items()}


def T_expr(Z, k):
    lo, hi = BND[k]
    return (Z[k] - lo) * (1.0 / (hi - lo))


def compromise(extra=None):
    """Two-phase compromise with optional extra constraints built from (m, Z)."""
    m, Z = M.build()
    lam = pulp.LpVariable("lam", lowBound=0, upBound=1)
    cons = [T_expr(Z, k) >= lam * (1.0 / (1 - DELTA)) for k in ("Z1", "Z2", "Z3")]
    cons += (extra(m, Z) if extra else [])
    M.solve(m, lam, extra=cons)
    v1 = M.val(Z)
    lam1 = (1 - DELTA) * min((v1[k] - BND[k][0]) / (BND[k][1] - BND[k][0]) for k in v1)
    m, Z = M.build()
    floor = lam1 / (1 - DELTA) - 1e-7
    cons = [T_expr(Z, k) >= floor for k in ("Z1", "Z2", "Z3")] + (extra(m, Z) if extra else [])
    M.solve(m, pulp.lpSum(T_expr(Z, k) for k in ("Z1", "Z2", "Z3")), extra=cons)
    reg = {r: pulp.value(e) for r, e in employment_terms(m, "collection").items()}
    reg_sc = {r: pulp.value(e) for r, e in employment_terms(m, "segregation").items()}
    V = m.variablesDict()
    open_ = {"cc": [M.CITIES[M.CC[j]] for j in range(len(M.CC)) if any(V[f"aJ_{j}_{t}"].value() > .5 for t in range(M.T))],
             "sc": [M.CITIES[M.SC[k]] for k in range(len(M.SC)) if any(V[f"aK_{k}_{t}"].value() > .5 for t in range(M.T))]}
    sc_slots = {M.CITIES[M.SC[k]]: sum(V[f"aK_{k}_{t}"].value() > .5 for t in range(M.T)) for k in range(len(M.SC))}
    return dict(lam=lam1, regions=reg, regions_seg=reg_sc, open=open_, sc_slots=sc_slots, **M.val(Z))


def summarise(r):
    tot = sum(r["regions"].values())
    low = sum(v for g, v in r["regions"].items() if g not in HIGH)
    wide = sum(v for g, v in r["regions"].items() if g not in WIDE)
    sc_low = sum(M.E_MIN * n for c, n in r["sc_slots"].items() if REGION[c] not in HIGH)
    low_s = sum(v for g, v in r["regions_seg"].items() if g not in HIGH)
    wide_s = sum(v for g, v in r["regions_seg"].items() if g not in WIDE)
    return dict(total=tot, low=low, low_share=100 * low / tot, wide=wide, wide_share=100 * wide / tot,
                sc_low=sc_low, low_share_seg=100 * low_s / tot, wide_share_seg=100 * wide_s / tot)


if __name__ == "__main__":
    out = {}
    base_sc = list(M.SC)
    # population shares (covered population) for reference
    pn = POP["nodes"]; ptot = sum(v["pop"] for v in pn.values())
    out["pop_share_low"] = 100 * sum(v["pop"] for c, v in pn.items() if REGION[c] not in HIGH) / ptot
    out["pop_share_wide"] = 100 * sum(v["pop"] for c, v in pn.items() if REGION[c] not in WIDE) / ptot

    okrows = [r for r in E["rows"] if r["feasible"]]
    def best(n, HS):
        adm = [r for r in okrows if sum(g not in HS for g in r["regions"]) >= n]
        return max(adm, key=lambda r: r["Z1"])["sites"] if adm else None
    variants = [("as_written", base_sc, "at least one outside Riyadh and Eastern (Stage 1 choice)"),
                ("none", [M.CITIES.index(c) for c in S1J["segregation_without_equity"]], "no equity rule (Stage 1 choice)"),
                ("narrow_all", best(3, HIGH), "all three outside Riyadh and Eastern"),
                ("wide_two", best(2, WIDE), "two of three outside Riyadh, Eastern and Makkah"),
                ("wide_all", best(3, WIDE), "all three outside Riyadh, Eastern and Makkah")]
    out["variants"] = {}
    for key, sc, label in variants:
        M.SC[:] = list(sc)
        r = compromise()
        r.update(summarise(r)); r["label"] = label; r["sc_sites"] = [M.CITIES[k] for k in sc]
        out["variants"][key] = r
        print(f"{key:11s} SC={r['sc_sites']}  profit {r['Z1']/1e6:.3f}  Z3 {r['Z3']:.0f}  "
              f"low-income {r['low_share']:.1f}%  outside corridor {r['wide_share']:.1f}%", flush=True)
    M.SC[:] = base_sc

    # Part B: employment-share floor for lower-income regions, under each attribution
    for attr, key in (("collection", "low_share"), ("segregation", "low_share_seg")):
        s0 = out["variants"]["as_written"][key]
        sweep = []
        s = float(int(s0) + 1)
        while s <= 100:
            def extra(m, Z, s=s, attr=attr):
                reg = employment_terms(m, attr)
                low = pulp.lpSum(e for g, e in reg.items() if g not in HIGH)
                return [low >= (s / 100.0) * Z["Z3"]]
            try:
                r = compromise(extra)
                r.update(summarise(r)); r["floor"] = s
                sweep.append(r)
                print(f"[{attr}] floor {s:.0f}%: profit {r['Z1']/1e6:.3f}  lam {r['lam']:.4f}  "
                      f"SC {r['open']['sc']}", flush=True)
                s += 1.0 if attr == "collection" else 5.0
            except M.NotSolved as e:
                print(f"[{attr}] floor {s:.0f}%: {e}", flush=True)
                out[f"share_floor_infeasible_at_{attr}"] = s
                break
        out[f"share_floor_sweep_{attr}"] = sweep
    out["solve_log"] = M.SOLVE_LOG
    json.dump(out, open("equity_regional.json", "w"), indent=1, default=float)
