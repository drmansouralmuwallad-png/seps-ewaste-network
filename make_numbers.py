"""Write numbers.tex: every number quoted in the manuscript prose, as a LaTeX macro,
computed from the result files. Nothing in the paper's text is typed by hand."""
import json, math
import numpy as np
import model as M

R = json.load(open("results.json")); X = json.load(open("extra.json"))
LR = json.load(open("lr_sweep.json")); E = json.load(open("equity_enum.json"))
S1 = json.load(open("stage1.json"))
B = {k: tuple(v) for k, v in R["bounds"].items()}
mm = R["maxmin"]; pm = R["payoff"]; ideal = R["ideal"]
out = {}

def put(name, val):
    out[name] = val

def ms(x, d=2):   # million SAR
    return f"{x/1e6:.{d}f}"

def num(x, d=0):
    s = f"{x:,.{d}f}"
    return s.replace(",", "{,}")

def pct(x, d=1, sign=False):
    return (f"{x:+.{d}f}" if sign else f"{x:.{d}f}").replace("-", "$-$").replace("+", "$+$")

T = {k: (mm[k] - B[k][0]) / (B[k][1] - B[k][0]) for k in ("Z1", "Z2", "Z3")}
# payoff
W = {"Z1": "One", "Z2": "Two", "Z3": "Three"}
for o in ("Z1", "Z2", "Z3"):
    put(f"Pay{W[o]}Profit", ms(pm[o]["Z1"])); put(f"Pay{W[o]}Util", f"{pm[o]['Z2']:.2f}")
    put(f"Pay{W[o]}Jobs", num(pm[o]["Z3"]))
put("CmpProfit", ms(mm["Z1"])); put("CmpProfitThree", ms(mm["Z1"], 3))
put("CmpUtil", f"{mm['Z2']:.2f}"); put("CmpJobs", num(mm["Z3"]))
put("Lam", f"{mm['lam']:.4f}")
put("TOne", f"{T['Z1']:.3f}"); put("TTwo", f"{T['Z2']:.3f}"); put("TThree", f"{T['Z3']:.3f}")
_nm = {"Z1": "profit", "Z2": "utilisation", "Z3": "employment"}
_b = [k for k in ("Z1", "Z2", "Z3") if T[k] - min(T.values()) < 1e-6]
put("BindingSentence", (f"{_nm[_b[0]].capitalize()} is the binding objective." if len(_b) == 1 else
    " and ".join(_nm[k] for k in _b).capitalize() + " are the binding objectives; the second phase raises profit above that level." if "Z1" not in _b else
    " and ".join(_nm[k] for k in _b).capitalize() + " are the binding objectives."))
put("Tmin", f"{min(T.values()):.3f}"); put("DeltaT", f"{max(T.values())-min(T.values()):.3f}")
put("PctMaxProfit", f"{100*mm['Z1']/ideal['Z1']:.1f}"); put("PctMaxUtil", f"{100*mm['Z2']/ideal['Z2']:.1f}")
put("PctMaxJobs", f"{100*mm['Z3']/ideal['Z3']:.1f}")
nos_c = M.nos(mm, ideal); put("NOSc", f"{nos_c:.4f}")
alts = [r for r in R["ws"]] + [r for r in R["ec"] if "Z1" in r]
put("NOSbest", f"{max(r['NOS'] for r in alts):.4f}"); put("NOSworst", f"{min(r['NOS'] for r in alts):.4f}")
vert = [r for r in R["ws"] if abs(r["Z1"] - ideal["Z1"]) / ideal["Z1"] < 1e-3]
put("WSvertex", str(len(vert))); put("WSn", str(len(R["ws"])))
odd = [r for r in R["ws"] if r not in vert]
put("WSoddW", ", ".join(f"{odd[0]['w'][k]:.2f}" for k in ("Z1", "Z2", "Z3")) if odd else "")
put("WSoddSentence", "" if not odd else (" Only $w = (" + ", ".join(f"{odd[0]['w'][k]:.2f}" for k in ("Z1", "Z2", "Z3")) +
    f")$ moved away from it, to {ms(odd[0]['Z1'])}~M~SAR and {odd[0]['Z2']:.2f}\\% utilisation."))
put("WSoddProfit", ms(odd[0]["Z1"]) if odd else ""); put("WSoddUtil", f"{odd[0]['Z2']:.2f}" if odd else "")
put("ProfitGivenUp", ms(ideal["Z1"] - mm["Z1"]))
put("EcInfeasible", str(sum(1 for r in R["ec"] if "Z1" not in r)))
# sensitivity
for r in R["sens"]:
    key = {"E-waste collection volume": "Vol", "Market demand": "Dem", "Fuel price": "Fuel",
           "Selling prices": "Price", "Collection capacity": "Cap"}[r["parameter"]]
    tag = key + ("Up" if r["change"] > 0 else "Down")
    if "dZ1" in r:
        put(tag + "Profit", pct(r["dZ1"], 2, True)); put(tag + "Jobs", pct(r["dZ3"], 2, True))
        put(tag + "Util", pct(r["dZ2"], 2, True))
    else:
        put(tag + "Profit", "infeasible")
# learning
off = R["learning"]["off"]
put("NoLearnJobs", num(off["Z3"])); put("NoLearnProfit", ms(off["Z1"]))
put("LearnCut", f"{100*(off['Z3']-mm['Z3'])/off['Z3']:.1f}")
put("LRlowJobs", num(LR[0]["Z3"])); put("LRhighJobs", num(LR[-1]["Z3"]))
put("LRspread", f"{100*(LR[-1]['Z3']-LR[0]['Z3'])/LR[0]['Z3']:.1f}")
put("LRprofitMin", ms(min(o["Z1"] for o in LR))); put("LRprofitMax", ms(max(o["Z1"] for o in LR)))
put("LRprofitRange", f"{100*(max(o['Z1'] for o in LR)-min(o['Z1'] for o in LR))/mm['Z1']:.2f}")
# recovery
rec = {r["name"][:4]: r for r in R["recovery"]}
for k, nm in (("Cons", "Seventy"), ("Base", "Eighty"), ("Ambi", "Ninety")):
    put(f"Rec{nm}Profit", ms(rec[k]["Z1"])); put(f"Rec{nm}Jobs", num(rec[k]["Z3"]))
put("RecGainPct", f"{100*(rec['Ambi']['Z1']-rec['Cons']['Z1'])/rec['Cons']['Z1']:.1f}")
put("RecGainAbs", ms(rec["Ambi"]["Z1"] - rec["Cons"]["Z1"]))
put("RecJobsAdd", num(rec["Ambi"]["Z3"] - rec["Cons"]["Z3"]))
en = X["endog"]
put("EndogAlpha", f"{en['alpha']:.2f}"); put("EndogBeta", f"{en['beta']:.2f}"); put("EndogGamma", f"{en['gamma']:.2f}")
put("EndogProfit", ms(en["Z1"]))
put("EndogShortfall", f"{100*(en['Z1']-mm['Z1'])/en['Z1']:.1f}")      # baseline below max, % of max
put("EndogGain", f"{100*(en['Z1']-mm['Z1'])/mm['Z1']:.1f}")           # max above baseline, % of baseline
# disruption
D = R["disruption"]
for tier, tag in (("Collection", "CC"), ("Segregation", "SC"), ("Recycling", "RC"), ("Refurbishing", "RF")):
    rows = [d for d in D if d["tier"] == tier]
    feas = [d for d in rows if d["feasible"]]
    put(f"Dis{tag}N", str(len(rows))); put(f"Dis{tag}Feas", str(len(feas)))
    if feas:
        put(f"Dis{tag}Min", pct(min(d["dZ1"] for d in feas), 2)); put(f"Dis{tag}Max", pct(max(d["dZ1"] for d in feas), 2))
        put(f"Dis{tag}PhysMin", pct(min(d["dZ1max"] for d in feas), 2)); put(f"Dis{tag}PhysMax", pct(max(d["dZ1max"] for d in feas), 2))
        put(f"Dis{tag}Util", f"{min(d['Z2'] for d in feas):.2f}")
        put(f"Dis{tag}JobsMin", pct(min(d["dZ3"] for d in feas), 2))
for tier, tag in (("Collection", "CC"), ("Segregation", "SC")):
    v = [abs(d["dZ1"]) for d in D if d["tier"] == tier and d["feasible"]]
    put(f"Dis{tag}AbsLo", f"{min(v):.2f}"); put(f"Dis{tag}AbsHi", f"{max(v):.2f}")
put("DisOtherAbs", f"{max(abs(d['dZ1']) for d in D if d['tier'] in ('Recycling', 'Refurbishing') and d['feasible']):.2f}")
put("DisRCAbs", f"{max(abs(d['dZ1']) for d in D if d['tier'] == 'Recycling'):.2f}")
_rf = [abs(d["dZ1"]) for d in D if d["tier"] == "Refurbishing"]
put("DisRFAbsLo", f"{min(_rf):.2f}"); put("DisRFAbsHi", f"{max(_rf):.2f}")
put("DisOtherPhys", f"{max(abs(d['dZ1max']) for d in D if d['tier'] in ('Recycling', 'Refurbishing')):.2f}")
put("DisAllFeasible", "yes" if all(d["feasible"] for d in D) else "no")
# resilience: strict single-failure tests (radii, capacities and flow kept as in the plan)
put("DisN", str(len(D))); put("DisStrictOK", str(sum(d["strict_feasible"] for d in D)))
put("DisStrictFail", str(sum(not d["strict_feasible"] for d in D)))
for tier, tag in (("Collection", "CC"), ("Segregation", "SC")):
    rows = [d for d in D if d["tier"] == tier]
    put(f"Dis{tag}Strict", str(sum(d["strict_feasible"] for d in rows)))
    put(f"Dis{tag}CovLost", str(sum(bool(d["uncovered"]) for d in rows)))
    put(f"Dis{tag}CapLost", str(sum((not d["uncovered"]) and not d["strict_feasible"] for d in rows)))
    put(f"Dis{tag}CapSite", ", ".join(d["site"] for d in rows if not d["uncovered"] and not d["strict_feasible"]))
    u = [len(d["uncovered"]) for d in rows if d["uncovered"]]
    put(f"Dis{tag}UncovLo", str(min(u))); put(f"Dis{tag}UncovHi", str(max(u)))
    h = [d["longest_haul"] for d in rows if d["uncovered"]]
    put(f"Dis{tag}HaulLo", num(min(h))); put(f"Dis{tag}HaulHi", num(max(h)))
    put(f"Dis{tag}ContFeas", str(sum(d["feasible"] for d in rows)))
cap_only = [d for d in D if d["tier"] == "Segregation" and not d["uncovered"] and not d["strict_feasible"]]
put("DisSCCapSite", ", ".join(d["site"] for d in cap_only))
oth = [d for d in D if d["tier"] in ("Recycling", "Refurbishing")]
put("DisOtherN", str(len(oth))); put("DisOtherStrict", str(sum(d["strict_feasible"] for d in oth)))
cc = [d for d in D if d["tier"] == "Collection"]
put("DisCCPhysAbs", f"{max(abs(d['dZ1max']) for d in cc):.2f}")
sc = [d for d in D if d["tier"] == "Segregation"]
put("DisSCMaxLo", ms(min(d["Z1max"] for d in sc))); put("DisSCMaxHi", ms(max(d["Z1max"] for d in sc)))
RD = json.load(open("radius.json"))
put("RadFreeProfit", ms(RD["no_R2"]["Z1"])); put("RadCostPct", f"{100*(RD['no_R2']['Z1']-pm['Z1']['Z1'])/pm['Z1']['Z1']:.1f}")
put("RadCostAbs", ms(RD["no_R2"]["Z1"] - pm["Z1"]["Z1"]))
put("DisSCvsFree", f"{100*max(abs(d['Z1max']-RD['no_R2']['Z1']) for d in sc)/RD['no_R2']['Z1']:.1f}")
LV = json.load(open("lowvol.json"))
cp = LV["captive_peak"]; tight = max(cp, key=cp.get)
put("CaptiveSite", tight); put("CaptivePeak", num(cp[tight])); put("CapCC", num(LV["cap_cc"]))
put("CaptiveHead", f"{100*(LV['cap_cc']-cp[tight])/LV['cap_cc']:.0f}")
put("CaptiveCut", num(0.75 * LV["cap_cc"]))
ph = LV["physical"]
put("VolUpPhys", "feasible" if ph["vol+10"]["radii"] == "Optimal" else "infeasible")
put("VolUpNoROne", "feasible" if ph["vol+10"]["no_R1"] == "Optimal" else "infeasible")
put("CapDownNoROne", "feasible" if ph["cap-25"]["no_R1"] == "Optimal" else "infeasible")
put("FuelAbs", f"{max(abs(r['dZ1']) for r in R['sens'] if r['parameter'] in ('Fuel price', 'Market demand') and 'dZ1' in r):.2f}")
# Monte Carlo
mc = X["mc"]
put("MCn", str(mc["n"])); put("MCmean", ms(mc["mean"])); put("MCgap", f"{100*abs(mm['Z1']-mc['mean'])/mm['Z1']:.1f}")
put("MCcv", f"{mc['cv']:.3f}"); put("MCpLo", ms(mc["p05"])); put("MCpHi", ms(mc["p95"]))
DG = json.load(open("diag_mc.json")); assert len(DG) == mc["infeasible"]
assert mc["infeasible"] == 0, "text says every Monte Carlo scenario is feasible"
_nc = sum(1 for r in DG if r["overflow"] and r["overflow"][1] == [tight]); _nr = sum(r["phys_relaxed"] == "Optimal" for r in DG)
put("MCcaptiveSentence", (f"In each of them the same {tight}" if _nc == len(DG) else f"In {_nc} of them the {tight}"))
put("MCrelaxSentence", ("all of them become" if _nr == len(DG) else f"{_nr} of them become"))
put("MCcaptiveN", str(sum(1 for r in DG if r["overflow"] and r["overflow"][1] == [tight])))
put("MCrelaxOK", str(sum(r["phys_relaxed"] == "Optimal" for r in DG)))
put("MCinfeas", str(mc["infeasible"])); put("MCinfeasPct", f"{100*mc['infeasible']/mc['n']:.0f}"); put("MCfeasN", str(mc["n"]-mc["infeasible"])); put("MCjobs", num(mc["emp_mean"])); put("MCutil", f"{mc['util_mean']:.2f}")
# transport surrogate
cb = X["carbon"]
put("TransProfit", ms(cb["Z1"])); put("TransPct", pct(cb["dZ1"], 2, True))
put("TransJobs", num(cb["Z3"])); put("TransUtil", f"{cb['Z2']:.2f}")
# tonnage
G = M.EWASTE
put("GenTotal", num(G.sum())); put("GenPeriodMin", num(G.sum(0).min())); put("GenPeriodMax", num(G.sum(0).max()))
put("Diverted", num(0.8 * G.sum())); put("Refurb", num(0.5 * G.sum()))
# Stage 1
put("SOneCC", ", ".join(S1["collection"])); put("SOneSC", ", ".join(S1["segregation"]))
put("SOneInvest", f"{S1['investment_kusd']/1000:.2f}"); put("SOneMaxDist", num(S1["max_distance_city_to_cc"]))
put("SOnePeak", num(S1["peak_tonnes"]))
FRx = {tuple(k.split("->")): v for k, v in S1["assignment_fractions"].items()}
_C = json.load(open("realdata.json")); _ci = _C["cities"]
put("SOneMaxAssign", num(max(_C["dist"][_ci.index(i)][_ci.index(j)] for (i, j) in FRx)))
_spl = {}
for (i, j), f in FRx.items():
    if f < 0.999: _spl.setdefault(i, []).append(j)
_ss = [f"{i}, between the {' and '.join(js)} centres" for i, js in _spl.items()]
put("SOneSplitSentence", ("The assignment splits one city's tonnage: " + _ss[0] + "." if len(_ss) == 1 else
     ("The assignment splits the tonnage of " + "; ".join(_ss) + "." if _ss else "No city's tonnage is split.")))
put("SOneNCC", str(S1["n_collection"])); put("SOneNCCuncap", str(S1["n_collection_uncapacitated"]))
put("SOneOneOutCC", str(S1["one_out_minimum"][0])); put("SOneOneOutSC", str(S1["one_out_minimum"][1]))
pl = S1["collection_peak_load"]; full = [k for k, v in pl.items() if v >= M.CAP_CC - 1e-3]
put("SOneFull", ", ".join(full)); put("SOneNSC", str(S1["n_segregation"]))
s = E["summary"]
put("EqNconfig", num(E["n_configs"])); put("EqNinfeas", num(E["n_configs"] - sum(r["feasible"] for r in E["rows"])));
put("EqNfeas", num(sum(r["feasible"] for r in E["rows"])))
put("EqNequity", num(s["n_equity"])); put("EqNequityWide", num(s["n_equity_wide"]))
put("EqBest", ", ".join(s["best"]["names"])); put("EqBestProfit", ms(s["best"]["Z1"], 3))
put("EqSOneProfit", ms(s["stage1"]["Z1"], 3))
put("EqBestEq", ", ".join(s["best_equity"]["names"])); put("EqBestEqWide", ", ".join(s["best_equity_wide"]["names"]))
put("EqBestEqWideProfit", ms(s["best_equity_wide"]["Z1"], 3))
put("EqCost", f"{s['equity_cost_pct']:.2f}"); put("EqCostWide", f"{s['equity_wide_cost_pct']:.2f}")
put("EqCostWideSAR", num((s["best"]["Z1"] - s["best_equity_wide"]["Z1"]) / 1e3))
okrows = [r for r in E["rows"] if r["feasible"]]
bestz = max(r["Z1"] for r in okrows)
import stage1 as S1m
for nm, HS in (("Narrow", S1m.H), ("Wide", S1m.H_WIDE)):
    for n, word in ((2, "Two"), (3, "All")):
        adm = [r for r in okrows if sum(g not in HS for g in r["regions"]) >= n]
        b = max(adm, key=lambda r: r["Z1"])
        put(f"Eq{nm}{word}N", num(len(adm))); put(f"Eq{nm}{word}Sites", ", ".join(b["names"]))
        put(f"Eq{nm}{word}Cost", f"{100*(bestz-b['Z1'])/bestz:.2f}")
        put(f"Eq{nm}{word}SAR", num((bestz - b["Z1"]) / 1e3))
put("DecompGap", f"{s['decomposition_gap_pct']:.2f}"); put("SpreadPct", f"{s['spread_pct']:.2f}")
put("DecompGapSAR", num((s["best"]["Z1"] - s["stage1"]["Z1"]) / 1e3))
# employment by period (run_employment.py)
EM = json.load(open("employment.json")); per = EM["baseline"]["periods"]
tot = sum(r["total"] for r in per)
put("EmpAvg", num(tot / len(per))); put("EmpPeak", num(max(r["total"] for r in per)))
put("EmpLast", num(per[-1]["total"])); put("EmpFirst", num(per[0]["total"]))
put("EmpFloorShare", f"{100*sum(r['floor_workers'] for r in per)/tot:.1f}")
put("EmpOpenFirst", str(per[0]["open"])); put("EmpOpenLast", str(per[-1]["open"]))
put("EmpFloorFirst", num(per[0]["floor_workers"])); put("EmpTonFirst", num(per[0]["tonnage_workers"]))
put("EmpTonLast", num(per[-1]["tonnage_workers"]))
put("EmpSlots", str(sum(r["open"] for r in per)))
sw = {int(r["e_min"]): r for r in EM["e_min_sweep"]}
for e, w in ((10, "Lo"), (40, "Hi")):
    put(f"Emin{w}Z", num(sw[e]["Z"]["Z3"])); put(f"Emin{w}Avg", num(sw[e]["Z"]["Z3"] / 6))
    put(f"Emin{w}Profit", ms(sw[e]["Z"]["Z1"])); put(f"Emin{w}Util", "%.2f" % sw[e]["Z"]["Z2"])
put("EminHiPct", pct(100 * (sw[40]["Z"]["Z1"] - mm["Z1"]) / mm["Z1"], 1, True))
assert all(abs(sw[e]["Z"]["Z1"] - mm["Z1"]) / mm["Z1"] < 1e-3 and abs(sw[e]["Z"]["Z2"] - mm["Z2"]) < 1e-6 for e in (10, 40)), "text says e_min leaves the design unchanged"
put("EminSameDesign", "yes" if all(abs(sw[e]["Z"]["Z1"] - mm["Z1"]) / mm["Z1"] < 1e-3 and abs(sw[e]["Z"]["Z2"] - mm["Z2"]) < 1e-6 for e in (10, 40)) else "no")
put("NoLearnAvg", num(off["Z3"] / 6)); put("CmpAvgShort", num(mm["Z3"] / 6))
put("PayOneAvg", num(pm["Z1"]["Z3"] / 6))
# computation
logs = R["solve_log"] + X.get("solve_log", [])
put("NSolves", num(len(logs)))
put("MaxSolveSec", f"{max(l['seconds'] for l in logs):.0f}")
put("NUncert", num(sum(1 for l in logs if l["sol_status"] == 2 and not l.get("superseded"))))
_nu = sum(1 for l in logs if l["sol_status"] == 2 and not l.get("superseded"))
_ns = sum(1 for l in logs if l.get("superseded"))
_mcu = X["mc"].get("uncertified", 0)
put("SolveSentence", (f"All {num(len(logs) - _ns)} logged subproblems of the main experiments reached the gap" + (f" ({_ns} of them only on a second attempt with a 3{{,}}600~s limit)" if _ns else "") + (", as did every Monte Carlo scenario" if _mcu == 0 else f"; {_mcu} Monte Carlo scenarios stopped at the limit and use the best design found") if _nu == 0 else
    f"Of the {num(len(logs))} logged subproblems, {_nu} stopped at the limit before reaching the gap, and the best design found is used"))
put("MCuncert", str(X["mc"].get("uncertified", 0)))
put("AllCertified", "yes" if all(l["sol_status"] in (1, -1) for l in logs) else "no")
m, _ = M.build()
nb = sum(1 for v in m.variables() if v.cat == "Integer")
put("NVars", num(len(m.variables()))); put("NBin", num(nb)); put("NCont", num(len(m.variables()) - nb))
put("NCons", num(len(m.constraints)))

with open("numbers.tex", "w") as f:
    f.write("% generated by make_numbers.py -- do not edit\n")
    for k, v in out.items():
        assert k.isalpha(), k
        f.write(f"\\newcommand{{\\n{k}}}{{{v}}}\n")
json.dump(out, open("numbers.json", "w"), indent=1)
print(len(out), "macros")

# ---- data provenance and comparison with published Saudi statistics (Section 5.1)
POPJ = json.load(open("population.json")); PNod = POPJ["nodes"]; RT = POPJ["region_totals_census_2022"]
ptot = sum(v["pop"] for v in PNod.values())
put("PopCovered", f"{ptot/1e6:.2f}"); put("PopKingdom", f"{RT['Kingdom']/1e6:.2f}")
put("PopCoveredPct", f"{100*ptot/RT['Kingdom']:.1f}")
put("PopCensusLabelled", str(sum(v["census_label"] for v in PNod.values())))
Vt = M.EWASTE.sum(axis=0)
put("CollRate", f"{1e6*Vt.mean()/ptot:.1f}")                       # kg per 1,000 residents per period
NE = POPJ["national_ewaste"]; put("NatEwasteKt", num(NE["generated_kt"])); put("NatEwasteYear", str(NE["year"]))
cov_kt = NE["generated_kt"] * ptot / RT["Kingdom"]                 # generation of the covered population, kt/yr
put("CovEwasteKt", num(cov_kt))
for tag, per in (("Annual", 1), ("Monthly", 12)):
    put(f"ImpliedShare{tag}", f"{100*Vt.mean()*per/1000/cov_kt:.1f}")
put("RiyadhShare", f"{100*PNod['Riyadh']['pop']/ptot:.1f}")
# transport cost per tonne-km: model vs benchmark (diesel 0.44 USD/l, 0.235 l/km)
put("TkmModel", f"{M.FP*M.FCR/M.VC:.4f}"); put("TkmBench", f"{0.44*0.235/M.VC:.4f}")
put("TkmRatio", f"{(0.44*0.235)/(M.FP*M.FCR):.1f}")
import os
if os.path.exists("bench/logs/BENCH_DONE"):
    BR = json.load(open("bench/results.json")); BE = json.load(open("bench/equity_enum.json"))["summary"]
    BRD = json.load(open("bench/radius.json"))
    bmm = BR["maxmin"]; bpm = BR["payoff"]
    put("BenchCmpProfit", ms(bmm["Z1"])); put("BenchCmpUtil", f"{bmm['Z2']:.2f}"); put("BenchCmpJobs", num(bmm["Z3"]))
    put("BenchMaxProfit", ms(bpm["Z1"]["Z1"])); put("BenchMaxDrop", f"{100*(pm['Z1']['Z1']-bpm['Z1']['Z1'])/pm['Z1']['Z1']:.1f}")
    put("BenchLam", f"{bmm['lam']:.4f}")
    put("BenchCmpDrop", f"{100*(mm['Z1']-bmm['Z1'])/mm['Z1']:.1f}")
    put("BenchSCPhysMax", f"{max(d['dZ1max'] for d in BR['disruption'] if d['tier']=='Segregation'):.1f}")
    put("BenchDecomp", f"{BE['decomposition_gap_pct']:.2f}"); put("BenchSpread", f"{BE['spread_pct']:.2f}")
    put("BenchEqCost", f"{BE['equity_cost_pct']:.2f}"); put("BenchEqCostWide", f"{BE['equity_wide_cost_pct']:.2f}")
    put("BenchRadCostPct", f"{100*(BRD['no_R2']['Z1']-BRD['radii']['Z1'])/BRD['radii']['Z1']:.1f}")
    bD = BR["disruption"]
    put("BenchDisCCPhysAbs", f"{max(abs(d['dZ1max']) for d in bD if d['tier']=='Collection'):.2f}")
    put("BenchStrictOK", str(sum(d["strict_feasible"] for d in bD)))
    # equity strict variants under benchmark
    import stage1 as S1b
    okb = [r for r in json.load(open("bench/equity_enum.json"))["rows"] if r["feasible"]]
    bz = max(r["Z1"] for r in okb)
    adm = [r for r in okb if sum(g not in S1b.H_WIDE for g in r["regions"]) >= 3]
    put("BenchEqWideAllCost", f"{100*(bz-max(r['Z1'] for r in adm))/bz:.2f}" if adm else "n/a")

# ---- regional distribution of employment (Section 5.4; run_equity_regional.py)
ER = json.load(open("equity_regional.json")); EV = ER["variants"]
import stage1 as S1r
aw, nw, ww = EV["as_written"], EV["none"], EV["wide_all"]
assert aw["sc_sites"] == nw["sc_sites"] and abs(aw["Z1"] - nw["Z1"]) < 1, "text says siting identical with and without the rule"
put("ERPopLow", f"{ER['pop_share_low']:.1f}"); put("ERPopWide", f"{ER['pop_share_wide']:.1f}")
put("ERLow", f"{aw['low_share']:.1f}"); put("ERWide", f"{aw['wide_share']:.1f}")
put("ERLowSeg", f"{aw['low_share_seg']:.1f}"); put("ERWideSeg", f"{aw['wide_share_seg']:.1f}")
na = EV["narrow_all"]
put("ERNarrowSites", ", ".join(na["sc_sites"])); put("ERWideAllSites", ", ".join(ww["sc_sites"]))
put("ERNarrowLow", f"{na['low_share']:.1f}"); put("ERNarrowLowSeg", f"{na['low_share_seg']:.1f}")
put("ERWideAllLow", f"{ww['low_share']:.1f}"); put("ERWideAllWide", f"{ww['wide_share']:.1f}")
put("ERWideAllLowSeg", f"{ww['low_share_seg']:.1f}"); put("ERWideAllWideSeg", f"{ww['wide_share_seg']:.1f}")
put("ERNarrowCost", f"{100*(aw['Z1']-na['Z1'])/aw['Z1']:.2f}"); put("ERWideAllCost", f"{100*(aw['Z1']-ww['Z1'])/aw['Z1']:.2f}")
put("ERSCFloorWP", num(M.E_MIN * M.T)); put("ERSCFloorPct", f"{100*M.E_MIN*M.T/aw['Z3']:.1f}")
# regions with covered nodes but no facility in any variant
fac_regions = set()
for v in EV.values():
    fac_regions |= {g for g, x in v["regions"].items() if x > 1e-6}
node_regions = {S1r.REGION[c] for c in M.CITIES}
put("ERNoFacility", ", ".join(sorted(node_regions - fac_regions)))
_per = json.load(open("employment.json"))["baseline"]["periods"]
put("EmpTonShare", f"{100*sum(r['tonnage_workers'] for r in _per)/sum(r['total'] for r in _per):.1f}")
put("ERNoFacilityN", str(len(node_regions - fac_regions)))
# employment-share floor sweeps
sc_ = ER["share_floor_sweep_collection"]
ok45 = [r for r in sc_ if abs(r["lam"] - aw["lam"]) < 1e-6]
put("ERFloorCollMax", f"{max(r['floor'] for r in ok45):.0f}")
put("ERFloorCollLast", f"{max(r['floor'] for r in sc_):.0f}")
put("ERFloorCollLastLam", f"{[r for r in sc_ if r['floor']==max(x['floor'] for x in sc_)][0]['lam']:.3f}")
put("ERFloorCollInf", f"{ER['share_floor_infeasible_at_collection']:.0f}")
ss_ = ER["share_floor_sweep_segregation"]
top = max(ss_, key=lambda r: r["floor"])
put("ERFloorSegMax", f"{top['floor']:.0f}"); put("ERFloorSegInf", f"{ER['share_floor_infeasible_at_segregation']:.0f}")
put("ERFloorSegCost", f"{100*(aw['Z1']-top['Z1'])/aw['Z1']:.2f}")

# ---- joint siting and operation at the Stage 1 capital cost (run_joint.py)
JJ = json.load(open("joint.json")); jm = JJ["maxprofit"]; seqmax = pm["Z1"]["Z1"]
def andjoin(xs):
    xs = list(xs)
    return xs[0] if len(xs) == 1 else ", ".join(xs[:-1]) + " and " + xs[-1]
put("JointMaxProfit", ms(jm["Z1"])); put("SeqMaxProfit", ms(seqmax))
put("JointMaxForgone", f"{100*(jm['Z1']-seqmax)/jm['Z1']:.1f}")          # % of the joint maximum
put("JointMaxForgoneAbs", ms(jm["Z1"] - seqmax))
put("JointMaxCC", ", ".join(jm["cc"])); put("JointMaxSC", andjoin(jm["sc"]))
put("JointMaxDropped", andjoin(c for c in S1["collection"] if c not in jm["cc"]))
put("JointMaxAdded", andjoin(c for c in jm["cc"] if c not in S1["collection"]))
put("JointMaxCert", "yes" if jm["sol_status"] == 1 else "no")
JS = json.load(open("joint_sites.json")); put("JointSitesCmpProfit", ms(JS["compromise"]["Z1"]))
TM = json.load(open("tied_maxprofit.json")); tb = TM["best"]
put("TiedBestProfit", ms(tb["Z1"])); put("TiedBestSites", andjoin(tb["sites"])); put("TiedBestUsed", andjoin(tb["used"]))
put("TiedVsJoint", f"{100*(jm['Z1']-tb['Z1'])/jm['Z1']:.2f}"); put("TiedNear", str(TM["n_within_01pct"]))
put("TiedN", str(TM["n_feasible"])); put("TiedMin", ms(TM["min"]))
put("TiedForgone", f"{100*(tb['Z1']-TM['stage1']['Z1'])/tb['Z1']:.1f}")
put("JointIdleSC", andjoin(c for c in jm["sc"] if c not in JS["sc_used_maxprofit"]))
put("JointUsedSC", andjoin(JS["sc_used_maxprofit"]))
put("JointVsRadFree", f"{100*(RD['no_R2']['Z1']-jm['Z1'])/RD['no_R2']['Z1']:.1f}")
if "compromise" in JJ:
    jc = JJ["compromise"]
    put("JointCmpProfit", ms(jc["Z1"])); put("JointCmpUtil", f"{jc['Z2']:.2f}"); put("JointCmpJobs", num(jc["Z3"]))
    put("JointCmpLam", f"{jc['lam']:.4f}")
    put("JointCmpForgone", f"{100*(jc['Z1']-mm['Z1'])/jc['Z1']:.2f}")
    put("JointCmpCC", ", ".join(jc["cc"])); put("JointCmpSC", ", ".join(jc["sc"]))
    put("JointCmpCert", "yes" if jc["phase1"]["sol_status"] == 1 and jc["phase2"]["sol_status"] == 1 else "no")

# ---- recovery mandates explained (Section 5.5; run_recovery.py)
RC_ = json.load(open("recovery.json")); A_ = RC_["A"]
sar = M.SAR_USD
mp = {k: A_[k]["maxprofit"] for k in A_}; cp_ = {k: A_[k]["compromise"] for k in A_}
put("RecMaxSeventy", ms(mp["70"]["Z1"])); put("RecMaxEighty", ms(mp["80"]["Z1"])); put("RecMaxNinety", ms(mp["90"]["Z1"]))
put("RecMaxGain", f"{100*(mp['90']['Z1']-mp['70']['Z1'])/mp['70']['Z1']:.1f}")
put("RecMaxDrop", f"{100*(mp['80']['Z1']-mp['90']['Z1'])/mp['80']['Z1']:.1f}")
drev = (mp["90"]["rev_r"] + mp["90"]["rev_f"] - mp["70"]["rev_r"] - mp["70"]["rev_f"]) * sar
put("RecRevGain", ms(drev))
put("RecRevGainRec", ms((mp["90"]["rev_r"] - mp["70"]["rev_r"]) * sar)); put("RecRevGainRef", ms((mp["90"]["rev_f"] - mp["70"]["rev_f"]) * sar))
put("RecOCMax", ms((mp["90"]["oc"] - mp["70"]["oc"]) * sar)); put("RecOCCmp", ms((cp_["90"]["oc"] - cp_["70"]["oc"]) * sar))
assert mp['90']['tc'] < mp['70']['tc'], "text says transport falls"
put("RecTCFall", f"{(mp['70']['tc'] - mp['90']['tc'])*sar/1e3:.0f}")
put("RecShiftT", num(mp["70"]["t_disp"] - mp["90"]["t_disp"]))
put("RecSlotsSeventyMax", str(mp["70"]["slots"])); put("RecSlotsEightyMax", str(mp["80"]["slots"])); put("RecSlotsNinetyMax", str(mp["90"]["slots"]))
put("RecSlotsSeventyCmp", str(cp_["70"]["slots"])); put("RecSlotsNinetyCmp", str(cp_["90"]["slots"]))
put("RecLamSeventy", f"{cp_['70']['lam']:.3f}"); put("RecLamNinety", f"{cp_['90']['lam']:.3f}")
put("RecCmpShortSeventy", ms(mp["70"]["Z1"] - cp_["70"]["Z1"])); put("RecCmpShortNinety", ms(mp["90"]["Z1"] - cp_["90"]["Z1"]))
put("RecUtilSeventy", f"{cp_['70']['Z2']:.1f}"); put("RecUtilNinety", f"{cp_['90']['Z2']:.1f}")
pref = RC_["prices"]["pref"]; put("RecPref", num(pref)); put("RecPrice", num(RC_["prices"]["pr"]))
put("RecAvgPrice", num((M.PR + pref) / 2))
extra_t = mp["70"]["t_disp"] - mp["90"]["t_disp"]
put("RecFixedPerT", num((mp["90"]["oc"] - mp["70"]["oc"]) / extra_t))
be = RC_["breakeven"]
put("RecBEOne", num(be["1.0"])); put("RecBEEight", num(be["0.8"]))
assert be["0.6"] is None or be["0.6"] < 1, "text says no positive break-even at yield 0.6"
_pk = float(M.EWASTE.sum(axis=0).max())
put("RecCapRC", num(M.CAP_RC)); put("RecCapRF", num(M.CAP_RF))
put("RecNeedRC", num(0.35 * _pk)); put("RecNeedRF", num(0.55 * _pk))
put("RecNeedRCEighty", num(0.30 * _pk)); put("RecNeedRFEighty", num(0.50 * _pk))

# ---- workforce learning interpretation (Sections 3.3, 5.6)
_per = json.load(open("employment.json"))["baseline"]["periods"]
_off = R["learning"]["off"]
saved = _off["Z3"] - mm["Z3"]
put("LearnSaved", num(saved))
put("LearnSavedPerK", ms(saved * 1000))                     # M SAR per 1,000 SAR per worker-period
put("LearnSavedPerKPct", f"{100*saved*1000/mm['Z1']:.1f}")
nl6 = _per[-1]["tonnes"] / M.WC1 + _per[-1]["floor_workers"]
put("LearnCutLast", f"{100*(nl6 - _per[-1]['total'])/nl6:.1f}")
put("NoLearnLast", num(nl6))
put("WCLast", f"{M.wc(M.T-1):.2f}"); put("WCGain", f"{100*(M.wc(M.T-1)/M.WC1-1):.0f}")
put("LearnTonCut", f"{100*(_per[0]['tonnage_workers']-_per[-1]['tonnage_workers'])/_per[0]['tonnage_workers']:.0f}")
assert abs(R["learning"]["off"]["Z1"] - mm["Z1"]) < 1 and abs(R["learning"]["off"]["Z2"] - mm["Z2"]) < 1e-6, "text says same design with and without learning"
assert all(abs(o["Z1"] - mm["Z1"]) < 1 for o in LR), "text says profit identical across learning rates"

# ---- equity rules at maximum profit (tied sitings, schedule free)
import stage1 as _S1q
_ok = [r for r in TM["rows"] if "Z1" in r]
_best = max(r["Z1"] for r in _ok)
def _bestadm(n, HS):
    a = [r for r in _ok if sum(_S1q.REGION[c] not in HS for c in r["sites"]) >= n]
    return max(a, key=lambda r: r["Z1"])
_na = _bestadm(3, _S1q.H); _wa = _bestadm(3, _S1q.H_WIDE)
put("EqMaxNarrowCost", f"{100*(_best-_na['Z1'])/_best:.1f}"); put("EqMaxWideCost", f"{100*(_best-_wa['Z1'])/_best:.1f}")
put("EqMaxNarrowSites", andjoin(_na["sites"])); put("EqMaxWideSites", andjoin(_wa["sites"]))
_aw = _bestadm(1, _S1q.H)
assert abs(_aw["Z1"] - _best) < 1, "rule as written free at max profit"
_two = [r for r in _ok if len(r["used"]) == 2]
assert _two and all("Riyadh" in r["used"] for r in _two), "text says two-centre sitings all use Riyadh"
put("TwoCentreN", str(len(_two)))

# ---- parameter values for the main-text parameter table (Table 2), read from the code
put("ParCapCC", num(M.CAP_CC)); put("ParCapSC", num(M.CAP_SC)); put("ParCapRC", num(M.CAP_RC)); put("ParCapRF", num(M.CAP_RF))
put("ParFOCcc", num(M.FOC_CC)); put("ParFOCsc", num(M.FOC_SEG)); put("ParFOCrc", num(M.FOC_REC)); put("ParFOCrf", num(M.FOC_REF))
put("ParPR", num(M.PR)); put("ParPL", num(M.PL)); put("ParPI", num(M.PI)); put("ParSigma", f"{M.SHARE_LOCAL:.2f}")
put("ParFP", f"{M.FP:.2f}"); put("ParFCR", f"{M.FCR:.2f}"); put("ParVC", f"{M.VC:.0f}")
put("ParAlpha", f"{M.ALPHA:.2f}"); put("ParBeta", f"{M.BETA:.2f}"); put("ParGamma", f"{1-M.ALPHA-M.BETA:.2f}")
put("ParLR", f"{M.LR:.2f}"); put("ParWCone", f"{M.WC1:.1f}"); put("ParEmin", num(M.E_MIN)); put("ParMu", f"{M.MIN_UTIL:.2f}")
put("ParRone", num(S1["radius_km"][0])); put("ParRtwo", num(S1["radius_km"][1])); put("ParSAR", f"{M.SAR_USD:.2f}")
put("ParDL", f"{num(min(M.DL))}--{num(max(M.DL))}"); put("ParDI", f"{num(min(M.DI))}--{num(max(M.DI))}"); put("ParDR", f"{num(min(M.DR))}--{num(max(M.DR))}")
put("ParT", str(M.T)); put("ParGap", "10^{-4}"); put("ParTlim", num(M.SOLVE_TLIM))
import stage1 as _S1p
put("ParFC", num(_S1p.FC)); put("ParFS", num(_S1p.FS))
assert _S1p.CAP_CC == M.CAP_CC and _S1p.CAP_SC == M.CAP_SC and tuple(S1["radius_km"]) == (_S1p.R1, _S1p.R2)

# ---- computation report (Section 5.1, Tables S17 and S22)
import compstats as _CS
_ex = _CS.experiments(); _sm = [(_n, _CS.summary(_l)) for _n, _s, _l in _ex]
_all = [l for _n, _s, _l in _ex for l in _l]
_hi = [l for _n, _s, _l in _ex if _s == "HiGHS" and not _n.startswith("Joint siting") for l in _l]
put("CompN", num(len(_all))); put("CompHours", f"{sum(l['seconds'] for l in _all)/3600:.1f}")
put("CompHighsN", num(len(_hi)))
import statistics as _st
put("CompMedian", f"{_st.median(l['seconds'] for l in _hi):.2f}")
put("CompMax", num(max(l['seconds'] for l in _hi)))
_nsup = sum(1 for l in _all if l.get("superseded"))
put("CompSuperseded", str(_nsup)); put("CompRetryPhrase", f"{_nsup} subproblem{'s' if _nsup != 1 else ''} needed")
put("CompLimited", str(sum(1 for l in _all if l.get("sol_status") == 2 and not l.get("superseded"))))
_MS = json.load(open("model_sizes.json"))
put("SwPython", _MS["software"]["python"]); put("SwPulp", _MS["software"]["pulp"]); put("SwHighs", _MS["software"]["highs"])
put("SwCbc", "2.10.3"); put("HwCpu", _MS["hardware"]["cpu"].replace("(R)", "")); put("HwCores", str(_MS["hardware"]["logical_cpus"]))
put("HwMem", f"{_MS['hardware']['mem_gib']:.1f}")
put("JointVars", num(_MS["joint"]["n_vars"])); put("JointBin", num(_MS["joint"]["n_int"])); put("JointCons", num(_MS["joint"]["n_cons"]))
put("JointMaxSec", num(JJ["maxprofit"]["seconds"]))
# ---- capacity utilisation vs operational utilisation (Eq. 16; run_caputil.py)
CU = json.load(open("caputil.json")); cuc = CU["compromise"]; cum = CU["maxprofit"]
assert abs(cuc["Z2"] - R["maxmin"]["Z2"]) < 1e-6 and abs(cuc["Z1"] - R["maxmin"]["Z1"]) < 1
put("CapUtilOpen", f"{cuc['all']['load_open']:.1f}"); put("CapUtilInst", f"{cuc['all']['load_installed']:.1f}")
put("CapUtilCC", f"{cuc['cc']['load_open']:.1f}"); put("CapUtilSC", f"{cuc['sc']['load_open']:.1f}")
put("CapUtilMaxOpen", f"{cum['all']['load_open']:.1f}")
json.dump(out, open("numbers.json", "w"), indent=1)
with open("numbers.tex", "w") as f:
    for k, v in sorted(out.items()):
        f.write(f"\\newcommand{{\\n{k}}}{{{v}}}\n")
print(len(out), "macros (with provenance block)")
