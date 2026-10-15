"""Write supp_tables.tex: every table of the Supplementary Material, generated from the
input data and the result files. Nothing in these tables is typed by hand."""
import json, math
import model as M

R = json.load(open("results.json")); X = json.load(open("extra.json"))
LR = json.load(open("lr_sweep.json")); E = json.load(open("equity_enum.json"))
S1 = json.load(open("stage1.json")); LV = json.load(open("lowvol.json"))
B = {k: tuple(v) for k, v in R["bounds"].items()}
mm = R["maxmin"]; ideal = R["ideal"]
C = M.CITIES; D = M.DIST; G = M.EWASTE
out = []
w = out.append


def n0(x):
    return f"{x:,.0f}".replace(",", "{,}")


def sg(x, d=2):
    s = f"{x:+.{d}f}"
    return s.replace("-", "$-$").replace("+", "$+$")


def table(label, caption, colspec, header, rows, size="\\footnotesize", note=None):
    w("\\begin{table}[!htb]\n\\centering")
    w(f"\\caption{{{caption}}}\n\\label{{{label}}}\n{size}")
    w(f"\\begin{{tabular}}{{{colspec}}}\n\\toprule")
    w(header + " \\\\\n\\midrule")
    for r in rows:
        w(r if r.startswith("\\") else r + " \\\\")
    w("\\bottomrule\n\\end{tabular}")
    if note:
        w(f"\\par\\smallskip\\noindent\\parbox{{0.92\\textwidth}}{{\\footnotesize {note}}}")
    w("\\end{table}\n")


# S1 population basis and generation
POP = json.load(open("population.json")); PN = POP["nodes"]
ptot = sum(PN[c]["pop"] for c in C)
w("\\section{Input data}\n\\label{sec:s-data}\n")
rows = [f"{C[i]} & {n0(PN[C[i]]['pop'])}{'' if PN[C[i]]['census_label'] else '$^{a}$'} & "
        f"{100*PN[C[i]]['pop']/ptot:.1f} & " + " & ".join(n0(v) for v in G[i]) + f" & {n0(G[i].sum())}"
        for i in range(24)]
rows.append("\\midrule")
rows.append(f"Total & {n0(ptot)} & 100.0 & " + " & ".join(n0(v) for v in G.sum(0)) + f" & {n0(G.sum())}")
table("tab:s-gen", "Population basis and e-waste collected (tonnes per period) by node. Each node "
      "stands for the governorate it serves; populations are Saudi Census 2022 figures as compiled by "
      "Saudipedia and Wikipedia governorate tables (URLs in \\texttt{population.json}), and every regional "
      "sum is below the GASTAT census total of its region. The tonnage handled in each period is an "
      "assumed formal collection volume, allocated to nodes in proportion to population and rounded to "
      "whole tonnes with period totals preserved.",
      "lrr*{6}{r}r", "Node & Population & Share (\\%) & $t=1$ & $t=2$ & $t=3$ & $t=4$ & $t=5$ & $t=6$ & Total",
      rows, size="\\scriptsize",
      note="$^{a}$ The compiling page gives the 2022 figure without stating that it is the census figure. "
           "Several compiling pages describe their figure as a city population. For Riyadh, Medina, Ha'il, "
           "Abha, Sakakah, Buraidah, Najran and Arar the figure equals the region's census total minus its "
           "other governorates, which identifies it as a governorate total; Tabuk agrees to within one person. "
           "For the other nodes this check was not possible. Al Mubarraz stands for Al-Ahsa Governorate, "
           "which also contains Al Hofuf.")

# S2 distances
ab = {c: c.replace("Khamis Mushait", "K. Mushait").replace("Hafar Al-Batin", "Hafar")
      .replace("Al Qunfudhah", "Qunfudhah").replace("Al Mubarraz", "Mubarraz") for c in C}
for part, cols in ((1, range(0, 12)), (2, range(12, 24))):
    hdr = "& " + " & ".join(f"\\rotatebox{{90}}{{{ab[C[j]]}}}" for j in cols)
    rows = [f"{ab[C[i]]} & " + " & ".join(str(D[i][j]) for j in cols) for i in range(24)]
    table(f"tab:s-dist{part}", f"Road distance (km) between the 24 cities, part {part} of 2 "
          "(Google Maps Distance Matrix API).", "l*{12}{r}", hdr, rows, size="\\scriptsize")

# S3 parameters, with the class of each value: O = official data, L = literature,
# A = modelling assumption (including calibration values without a traceable source).
P = [("Coverage radius, collection", "$R_1$", "300", "km", "A", "service standard"),
     ("Coverage radius, segregation", "$R_2$", "1{,}000", "km", "A", "service standard"),
     ("Installation cost, collection centre", "$FC_j$", "2{,}000", "kUSD", "A", "no traceable source"),
     ("Installation cost, segregation centre", "$FS_k$", "4{,}250", "kUSD", "A", "no traceable source"),
     ("Capacity, collection centre", "$Cap_j$", n0(M.CAP_CC), "t/period", "A", ""),
     ("Capacity, segregation centre", "$Cap_k$", n0(M.CAP_SC), "t/period", "A", ""),
     ("Capacity, recycling centre", "", n0(M.CAP_RC), "t/period", "A", ""),
     ("Capacity, refurbishing centre", "", n0(M.CAP_RF), "t/period", "A", ""),
     ("Minimum throughput when operating", "$\\mu$", f"{M.MIN_UTIL:.2f}", "of capacity", "A", ""),
     ("Operating cost, collection centre", "$FOC_j$", n0(M.FOC_CC), "kUSD/period", "A", ""),
     ("Operating cost, segregation centre", "$FOS_k$", n0(M.FOC_SEG), "kUSD/period", "A", "no traceable source"),
     ("Operating cost, recycling centre", "$FOR_r$", n0(M.FOC_REC), "kUSD/period", "A", "no traceable source"),
     ("Operating cost, refurbishing centre", "$FOF_f$", n0(M.FOC_REF), "kUSD/period", "A", "no traceable source"),
     ("Price, recycled material", "$P_r$", n0(M.PR), "USD/t", "A", "$\\pm$15\\% tested"),
     ("Price, refurbished products (local)", "$P_l$", n0(M.PL), "USD/t", "A", "$\\pm$15\\% tested"),
     ("Price, refurbished products (international)", "$P_i$", n0(M.PI), "USD/t", "A", "$\\pm$15\\% tested"),
     ("Refurbished output sold locally", "$\\sigma$", f"{M.SHARE_LOCAL:.2f}", "", "A", ""),
     ("Fuel price", "$FP$", f"{M.FP:.2f}", "USD/l", "A", "benchmark 0.44 (O)"),
     ("Fuel consumption", "$FCR$", f"{M.FCR:.2f}", "l/km", "A", "benchmark 0.235 (L)"),
     ("Vehicle capacity", "$VC$", f"{M.VC:.0f}", "t", "A", ""),
     ("Recovery fractions", "$\\alpha,\\beta,\\gamma$", f"{M.ALPHA:.2f}, {M.BETA:.2f}, {1-M.ALPHA-M.BETA:.2f}", "", "A", "policy; varied"),
     ("Learning rate", "$LR$", f"{M.LR:.2f}", "", "L", "swept 0.75--0.95"),
     ("Learning exponent", "$b$", f"{M.B_LEARN:.3f}", "$-\\log_2 LR$", "L", ""),
     ("Worker capacity, period 1", "$WC_1$", f"{M.WC1:.1f}", "t/worker/period", "A", ""),
     ("Minimum staffing per operating facility", "$e_{\\min}$", n0(M.E_MIN), "workers/period", "A", "10 and 40 tested"),
     ("Tolerance parameter", "$\\delta$", "0.10", "", "A", "method parameter"),
     ("Exchange rate", "", f"{M.SAR_USD:.2f}", "SAR/USD", "O", "official peg"),
     ("Population of each node", "", "Table~S1", "", "O", "Census 2022"),
     ("Formal collection volume", "$\\sum_i EW_{it}$", f"{n0(G.sum(0).min())}--{n0(G.sum(0).max())}", "t/period", "A", "allocated by population"),
     ("Road distances", "$d_{ij}$", "Tables~S2--S3", "km", "M", "Google Maps"),
     ("High-income regions", "", "Riyadh, Eastern", "", "O", "GASTAT HIES 2018")]
P += [(f"Demand, {lab}", "", f"{n0(min(arr))}--{n0(max(arr))}", "t/period", "A", "by period")
      for lab, arr in (("local refurbished", M.DL), ("international refurbished", M.DI),
                       ("raw material", M.DR))]
_C = ("Coverage radius", "Capacity,", "Minimum throughput", "Operating cost, collection", "Minimum staffing", "Tolerance")
P = [(a, b, c, d, ("A (C)" if a.startswith(_C) else "A (S)") if e == "A" else e, f) for a, b, c, d, e, f in P]
w("\\section{Parameters}\n\\label{sec:s-param}\n")
table("tab:s-param", "Model parameters and the class of each value: O, official data; M, measured "
      "data from a commercial service; L, literature; A, assumption (S, calibration value carried over from the "
      "study data; C, the author's modelling choice). Sources are given in the parameter table of Section~5.1 of the main text, including calibration values carried over from the study "
      "data that could not be traced to a published source (Section~5.1).", "@{}llllll@{}",
      "Parameter & Symbol & Value & Unit & Class & Note",
      [f"{a} & {b} & {c} & {d} & {e} & {f}" for a, b, c, d, e, f in P], size="\\scriptsize")

# S4 Stage 1
w("\\section{Stage 1 siting}\n\\label{sec:s-stage1}\n")
rows = []
FR = {tuple(k.split("->")): v for k, v in S1["assignment_fractions"].items()}
for j in S1["collection"]:
    served = [(c, f) for (c, jj), f in FR.items() if jj == j]
    lab = ", ".join(c if f > 0.999 else f"{c} ({100*f:.0f}\\%)" for c, f in served)
    far = max(D[C.index(c)][C.index(j)] for c, _ in served)
    rows.append(f"{j} & {lab} & {far} & {n0(S1['collection_peak_load'][j])}")
table("tab:s-cc", f"Collection centres and the tonnage assigned to them in Phase~1. A city "
      f"whose tonnage is split between centres is shown with the share sent to each. Every "
      f"city is within {int(S1['radius_km'][0])}~km of the centres it is assigned to, and no "
      f"centre's assigned load exceeds its capacity of {n0(M.CAP_CC)}~t in any period.",
      "lp{0.5\\textwidth}rr", "Centre & Cities served & Max.\\ distance (km) & Peak load (t)", rows,
      size="\\scriptsize")
rows = []
for k in S1["segregation"]:
    cov = [j for j in S1["collection"] if D[C.index(j)][C.index(k)] <= S1["radius_km"][1]]
    rows.append(f"{k} & {S1['regions'][k]} & {', '.join(cov)}")
table("tab:s-sc", "Segregation centres, their administrative regions, and the collection "
      f"centres within {n0(S1['radius_km'][1])}~km.", "llp{0.55\\textwidth}",
      "Centre & Region & Collection centres covered", rows)

# S5 payoff and memberships
w("\\section{Payoff matrix and memberships}\n\\label{sec:s-payoff}\n")
pm = R["payoff"]
rows = [f"{lab} & {pm[k]['Z1']/1e6:.3f} & {pm[k]['Z2']:.2f} & {n0(pm[k]['Z3'])}"
        for lab, k in (("Profit only", "Z1"), ("Op.\\ utilisation only", "Z2"), ("Employment only", "Z3"))]
rows += ["\\midrule", f"Upper bound $U_k$ & {B['Z1'][1]/1e6:.3f} & {B['Z2'][1]:.2f} & {n0(B['Z3'][1])}",
         f"Lower bound $L_k$ & {B['Z1'][0]/1e6:.3f} & {B['Z2'][0]:.2f} & {n0(B['Z3'][0])}",
         "\\midrule", f"Compromise & {mm['Z1']/1e6:.3f} & {mm['Z2']:.2f} & {n0(mm['Z3'])}"]
table("tab:s-payoff", "Payoff matrix and bounds. Profit in million SAR.", "lrrr",
      "Optimised objective & Profit & Op.\\ utilisation (\\%) & Employment (w-p)", rows)
T = mm["T"]
rows = [f"{lab} & {T[k]:.3f} & {1-T[k]:.3f} & {0.9*T[k]:.3f} & {min(T[k],1-T[k]):.3f}"
        for lab, k in (("Profit $Z_1$", "Z1"), ("Op.\\ utilisation $Z_2$", "Z2"), ("Employment $Z_3$", "Z3"))]
rows += ["\\midrule", f"$\\lambda^{{*}} = (1-\\delta)\\min_k T_k$ & \\multicolumn{{4}}{{c}}{{{mm['lam']:.4f}}}"]
table("tab:s-memb", "Memberships at the compromise ($\\delta = 0.10$).", "lcccc",
      "Objective & $T_k$ & $F_k$ & $U_k$ & $C_k$", rows)

# S6 scalarisation runs
rows = []
for r in R["ws"]:
    wv = ", ".join(f"{r['w'][k]:.2f}" for k in ("Z1", "Z2", "Z3"))
    rows.append(f"Weighted sum & $({wv})$ & {r['Z1']/1e6:.2f} & {r['Z2']:.2f} & {n0(r['Z3'])} & {r['NOS']:.4f}")
rows.append("\\midrule")
for r in R["ec"]:
    eu, ee = r["eps"]
    if "Z1" in r:
        rows.append(f"$\\varepsilon$-constraint & $Z_2 \\ge {eu:.2f}$, $Z_3 \\ge {n0(ee)}$ & {r['Z1']/1e6:.2f} & {r['Z2']:.2f} & {n0(r['Z3'])} & {r['NOS']:.4f}")
    else:
        rows.append(f"$\\varepsilon$-constraint & $Z_2 \\ge {eu:.2f}$, $Z_3 \\ge {n0(ee)}$ & \\multicolumn{{4}}{{c}}{{no solution}}")
rows += ["\\midrule", f"Compromise & two-phase max--min & {mm['Z1']/1e6:.2f} & {mm['Z2']:.2f} & {n0(mm['Z3'])} & {M.nos(mm, ideal):.4f}"]
w("\\section{Scalarisation benchmark}\n\\label{sec:s-bench}\n")
table("tab:s-bench", "All twenty scalarisation runs. Profit in million SAR; NOS as defined in Section~4.4 "
      "of the main text.", "llrrrr", "Method & Setting & Profit & Util.\\ (\\%) & Empl.\\ (w-p) & NOS",
      rows, size="\\scriptsize")

# S7 operating schedule
sch = E["schedule"]
tiers = [("aJ", "Collection", M.CC_NAMES), ("aK", "Segregation", M.SC_NAMES),
         ("aL", "Recycling", list(M.RC_ANCHOR)), ("aM", "Refurbishing", M.RF_NAMES)]
rows = []
for pre, tname, names in tiers:
    for i, nm in enumerate(names):
        cells = ["\\checkmark" if sch.get(f"{pre}_{i}_{t}", 0) else "--" for t in range(M.T)]
        rows.append(f"{tname} & {nm} & " + " & ".join(cells))
    rows.append("\\midrule")
EM = json.load(open("employment.json"))["baseline"]["periods"]
rows += ["\\midrule",
         "Tonnes handled & & " + " & ".join(n0(r["tonnes"]) for r in EM),
         "Workers for tonnage & $\\sum X/WC_t$ & " + " & ".join(n0(r["tonnage_workers"]) for r in EM),
         "Staffing floor & $e_{\\min} N_t$ & " + " & ".join(n0(r["floor_workers"]) for r in EM),
         "Workforce in period & $E_t$ & " + " & ".join(n0(r["total"]) for r in EM)]
w("\\section{Operating schedule}\n\\label{sec:s-sched}\n")
table("tab:s-sched", "Facilities operating in each period at the compromise, and the workforce each period "
      "requires. $Z_3$ is the sum of the last row over the six periods (worker-periods).", "ll*{6}{c}",
      "Tier & Site & 1 & 2 & 3 & 4 & 5 & 6", rows)

# S8 sensitivity
rows = []
for r in R["sens"]:
    ch = sg(100 * r["change"], 0) + "\\%"
    if "dZ1" in r:
        rows.append(f"{r['parameter']} & {ch} & {sg(r['dZ1'])} & {sg(r['dZ3'])} & {sg(r['dZ2'])}")
    else:
        rows.append(f"{r['parameter']} & {ch} & \\multicolumn{{3}}{{l}}{{no solution (see note)}}")
note = (f"Change relative to the baseline compromise; operational utilisation in percentage points. With "
        f"10\\% less tonnage the network remains feasible, but the most employment it can "
        f"support is {n0(LV['maxjobs'])} worker-periods, below the baseline lower bound $L_3 = "
        f"{n0(LV['baseline_L3'])}$, so the compromise has no solution on the baseline scale. "
        f"Re-solved on its own payoff bounds it gives {LV['compromise']['Z1']/1e6:.2f}~M~SAR "
        f"({sg(LV['dZ1'])}\\%), {n0(LV['compromise']['Z3'])} worker-periods and "
        f"{LV['compromise']['Z2']:.2f}\\% operational utilisation. With 10\\% more tonnage, or with collection "
        f"capacity cut by 25\\%, the network itself has no feasible flow within the coverage radii: "
        f"the cities whose only collection centre within {n0(S1['radius_km'][0])}~km is "
        f"{max(LV['captive_peak'], key=LV['captive_peak'].get)} generate up to "
        f"{n0(max(LV['captive_peak'].values()))}~t in a period, against a capacity of {n0(LV['cap_cc'])}~t. "
        f"Both cases become feasible when cities may ship beyond {n0(S1['radius_km'][0])}~km.")
w("\\section{Sensitivity, recovery mandates and learning}\n\\label{sec:s-sens}\n")
table("tab:s-sens", "Sensitivity of the compromise (\\% change).", "llrrr",
      "Parameter & Change & Profit & Employment & Op.\\ utilisation (pp)", rows, note=note)
rows = [f"{r['name'].replace('%', chr(92) + '%')} & {r['alpha']:.2f} & {r['beta']:.2f} & {r['gamma']:.2f} & {r['Z1']/1e6:.2f} & {r['Z2']:.2f} & {n0(r['Z3'])}"
        for r in R["recovery"]]
en = X["endog"]
rows += ["\\midrule", f"Profit-maximising split (5$\\times$5 grid) & {en['alpha']:.2f} & {en['beta']:.2f} & {en['gamma']:.2f} & {en['Z1']/1e6:.2f} & -- & --"]
table("tab:s-rec", "Recovery mandates. Profit in million SAR. The last row is the best split "
      "on a grid of $\\alpha \\in \\{0.20,\\ldots,0.40\\}$, $\\beta \\in \\{0.40,\\ldots,0.60\\}$ "
      "with $\\gamma \\geq 0.10$.", "lrrrrrr",
      "Scenario & $\\alpha$ & $\\beta$ & $\\gamma$ & Profit & Util.\\ (\\%) & Empl.\\ (w-p)", rows)
rows = [f"{o['LR']:.2f} & {-math.log2(o['LR']):.3f} & {o['Z1']/1e6:.3f} & {n0(o['Z3'])}" for o in LR]
table("tab:s-lr", "Learning-rate sweep. Profit in million SAR.", "cccr",
      "$LR$ & $b$ & Profit & Employment (w-p)", rows)

# S9 disruption
RD = json.load(open("radius.json"))
rows = []
for d in R["disruption"]:
    st = "yes" if d["strict_feasible"] else ("no: capacity" if not d["uncovered"] else "no: coverage")
    unc = ", ".join(d["uncovered"]) if d["uncovered"] else "--"
    haul = n0(d["longest_haul"]) if d["uncovered"] else "--"
    if d["feasible"]:
        rows.append(f"{d['tier']} & {d['site']} & {unc} & {st} & {haul} & {sg(d['dZ1max'])} & {sg(d['dZ1'])} & {sg(d['dZ3'])}")
    else:
        rows.append(f"{d['tier']} & {d['site']} & {unc} & {st} & {haul} & \\multicolumn{{3}}{{c}}{{no solution}}")
w("\\section{Single-facility loss}\n\\label{sec:s-dis}\n")
table("tab:s-dis", "Loss of each facility for all six periods. \\emph{Stranded}: cities (collection loss) "
      f"or collection centres (segregation loss) with no surviving facility within "
      f"{n0(S1['radius_km'][0])}~km or {n0(S1['radius_km'][1])}~km. \\emph{{Plan holds}}: whether Stage~2 is "
      "feasible with every radius, capacity and flow constraint kept. \\emph{Haul}: longest road distance "
      "a stranded node must ship in the contingency plan, in which the stranded nodes, and for a "
      "collection-centre loss the other cities it served, may ship beyond the radius. "
      "\\emph{Max.\\ profit}: profit-maximising contingency plan against the intact network's "
      "profit-maximising plan. Last two columns: contingency compromise against the baseline compromise.",
      "@{}llp{0.17\\textwidth}lrrrr@{}",
      "Tier & Site & Stranded & Plan holds & Haul (km) & Max.\\ profit (\\%) & Profit (\\%) & Empl.\\ (\\%)",
      rows, size="\\scriptsize",
      note=(f"For a segregation-centre loss every collection centre may ship beyond {n0(S1['radius_km'][1])}~km, "
            f"because narrower relaxations have no feasible flow. The intact network's maximum profit is "
            f"{RD['radii']['Z1']/1e6:.2f}~M~SAR with the radii and {RD['no_R2']['Z1']/1e6:.2f}~M~SAR when the "
            f"{n0(S1['radius_km'][1])}~km radius is lifted, which lets it close "
            f"{', '.join(sorted(set(RD['radii']['open_sc']) - set(RD['no_R2']['open_sc'])))}; the gain in the "
            f"\\emph{{Max.\\ profit}} column for segregation losses comes from that relaxation, not from the loss."))

# S10 Monte Carlo
DG = json.load(open("diag_mc.json"))
_sites = {tuple(r["overflow"][1]) for r in DG if r["overflow"]}
DG_site = ", ".join(_sites.pop()) if len(_sites) == 1 else "a single"
DG_n = sum(1 for r in DG if r["overflow"]); DG_relax = sum(r["phys_relaxed"] == "Optimal" for r in DG)
assert len(DG) == X["mc"]["infeasible"]
mc = X["mc"]
rows = [f"Profit (M SAR) & {mc['mean']/1e6:.2f} & {mc['median']/1e6:.2f} & {mc['p05']/1e6:.2f} & {mc['p95']/1e6:.2f}",
        f"Employment (w-p) & {n0(mc['emp_mean'])} & -- & -- & --",
        f"Op.\\ utilisation (\\%) & {mc['util_mean']:.2f} & -- & -- & --"]
w("\\section{Generation variability}\n\\label{sec:s-mc}\n")
table("tab:s-mc", f"Monte Carlo: {mc['n']} scenarios, each city-period generation drawn "
      f"independently from $\\pm$10\\% of its estimate. "
      + ("Every scenario has a feasible flow within the coverage radii. " if mc['infeasible'] == 0 else
         f"{mc['infeasible']} scenarios have no feasible flow within the coverage radii; in {DG_n} of them the "
         f"cities that can reach only the {DG_site} collection centre exceed its capacity in some period, and "
         f"{DG_relax} become feasible when cities may ship beyond the radius. Statistics are over the other "
         f"{mc['n'] - mc['infeasible']}. ")
      + (f"In {mc.get('uncertified', 0)} scenarios the solver stopped at the 300~s limit before "
         f"proving the gap; the best design found is used. " if mc.get('uncertified', 0) else
         "Every scenario was solved to the $10^{-4}$ gap. ")
      + f"Coefficient of variation of profit {mc['cv']:.3f}.",
      "lrrrr", "Metric & Mean & Median & 5th pct. & 95th pct.", rows)

# S11 equity enumeration
s = E["summary"]
ok = sorted([r for r in E["rows"] if r["feasible"]], key=lambda r: -r["Z1"])
rank = {tuple(r["sites"]): i + 1 for i, r in enumerate(ok)}
rows = []
for i, r in enumerate(ok[:10]):
    rows.append(f"{i+1} & {', '.join(r['names'])} & {', '.join(r['regions'])} & {r['Z1']/1e6:.3f} & "
                f"{'yes' if r['equity'] else 'no'} & {'yes' if r['equity_wide'] else 'no'}")
st = s["stage1"]; bw = s["best_equity_wide"]
rows += ["\\midrule",
         f"{rank[tuple(st['sites'])]} & {', '.join(st['names'])} (Stage~1) & {', '.join(st['regions'])} & {st['Z1']/1e6:.3f} & "
         f"{'yes' if st['equity'] else 'no'} & {'yes' if st['equity_wide'] else 'no'}",
         f"{rank[tuple(bw['sites'])]} & {', '.join(bw['names'])} (best, wide rule) & {', '.join(bw['regions'])} & {bw['Z1']/1e6:.3f} & yes & yes"]
w("\\section{Alternative Stage 1 sitings}\n\\label{sec:s-equity}\n")
table("tab:s-equity", f"Stage~2 profit (million SAR) for the {n0(E['n_configs'])} three-site "
      f"segregation configurations that meet the coverage rule, all evaluated under the "
      f"baseline operating schedule; top ten, the Stage~1 choice and the best configuration "
      f"meeting the wide equity rule. Operational utilisation and employment are identical across "
      f"configurations under a common schedule. Equity: at least one site outside "
      f"{{Riyadh, Eastern}}; wide: outside {{Riyadh, Eastern, Makkah}}.",
      "rp{0.3\\textwidth}p{0.22\\textwidth}rcc",
      "Rank & Sites & Regions & Profit & Equity & Wide", rows, size="\\scriptsize")

# S12 computation: software, hardware, model sizes and effort by experiment
import compstats as CS
MS = json.load(open("model_sizes.json")); sw = MS["software"]; hw = MS["hardware"]
s1p1 = next(l for l in MS["stage1"] if l["phase"] == 1); s1p2 = next(l for l in MS["stage1"] if l["phase"] == 2)
rows = [f"Software & Python {sw['python']}; PuLP {sw['pulp']}; HiGHS {sw['highs']} (Stage~2 and all later models); CBC {sw['cbc']} (Stage~1)",
        f"Hardware & {hw['cpu']}, {hw['logical_cpus']} logical CPUs, {hw['mem_gib']}~GiB RAM; {sw['os']}",
        "Solver settings & HiGHS: relative MIP gap $10^{-4}$ (equity LPs $10^{-9}$), 300~s limit per subproblem, one thread; "
        "a subproblem stopped by the limit is re-solved once with 3{,}600~s; joint model 3{,}600~s per solve. CBC: default settings (proven optimal)",
        f"Stage~1 models & Phase~1: {n0(s1p1['n_vars'])} variables ({n0(s1p1['n_int'])} binary), up to {n0(max(l['n_cons'] for l in MS['stage1'] if l['phase']==1))} constraints; "
        f"Phase~2: {n0(s1p2['n_vars'])} variables ({n0(s1p2['n_int'])} binary), up to {n0(max(l['n_cons'] for l in MS['stage1'] if l['phase']==2))} constraints",
        f"Stage~2 model & {n0(MS['stage2']['n_vars'])} variables ({n0(MS['stage2']['n_int'])} binary), {n0(MS['stage2']['n_cons'])} constraints",
        f"Joint model & {n0(MS['joint']['n_vars'])} variables ({n0(MS['joint']['n_int'])} binary), {n0(MS['joint']['n_cons'])} constraints"]
w("\\section{Computation}\n\\label{sec:s-comp}\n")
table("tab:s-comp", "Software, hardware, solver settings and model sizes. Compromise constraints are excluded from the "
      "model sizes. Computational effort by experiment is in Table~S22.", "@{}lp{0.72\\textwidth}@{}", "Item & Value", rows,
      size="\\scriptsize")
# S18 regional employment with and without the equity rule
import stage1 as S1r
ER = json.load(open("equity_regional.json")); EV = ER["variants"]
PNr = json.load(open("population.json"))["nodes"]; ptr = sum(v["pop"] for v in PNr.values())
popreg = {}
for c, v in PNr.items():
    popreg[S1r.REGION[c]] = popreg.get(S1r.REGION[c], 0) + v["pop"]
cls = lambda g: "H" if g in S1r.H else ("C" if g in S1r.H_WIDE else "L")
regs = sorted(popreg, key=lambda g: -popreg[g])
rows = []
for g in regs:
    cells = [f"{100*popreg[g]/ptr:.1f}"]
    for key in ("as_written", "narrow_all", "wide_all"):
        v = EV[key]
        cells += [n0(v["regions"].get(g, 0.0)), n0(v["regions_seg"].get(g, 0.0))]
    rows.append(f"{g} & {cls(g)} & " + " & ".join(cells))
rows.append("\\midrule")
def sh(v, k): return f"{v[k]:.1f}\\%"
rows.append("Lower-income share & & " + f"{ER['pop_share_low']:.1f} & " + " & ".join(
    f"{sh(EV[k], 'low_share')} & {sh(EV[k], 'low_share_seg')}" for k in ("as_written", "narrow_all", "wide_all")))
rows.append("Outside the corridor & & " + f"{ER['pop_share_wide']:.1f} & " + " & ".join(
    f"{sh(EV[k], 'wide_share')} & {sh(EV[k], 'wide_share_seg')}" for k in ("as_written", "narrow_all", "wide_all")))
rows.append("Profit (M SAR) & & & " + " & ".join(
    f"\\multicolumn{{2}}{{c}}{{{EV[k]['Z1']/1e6:.3f}}}" for k in ("as_written", "narrow_all", "wide_all")))
w("\\section{Regional distribution of employment}\n\\label{sec:s-regional}\n")
table("tab:s-regional", "Worker-periods by region at the compromise (baseline payoff bounds), for the "
      f"segregation siting chosen with or without the equity rule ({', '.join(EV['as_written']['sc_sites'])}; "
      f"identical in both cases), the best siting with all three centres outside Riyadh and Eastern "
      f"({', '.join(EV['narrow_all']['sc_sites'])}) and the best with all three outside the Riyadh--Jeddah--Dammam "
      f"corridor ({', '.join(EV['wide_all']['sc_sites'])}). Col.: the tonnage-related labour of Eq.~(17) is placed "
      "at the collection centre receiving the tonnage; Seg.: at the segregation centre sorting it. Totals are "
      "identical. Class: H, high-income region; C, Makkah (corridor); L, other. Pop.: share of the covered "
      "population (\\%). Regions with no facility in any variant show zero.",
      "llr*{6}{r}", "Region & Class & Pop. & \\multicolumn{2}{c}{With/without rule} & "
      "\\multicolumn{2}{c}{All 3 outside H} & \\multicolumn{2}{c}{All 3 outside H, C} \\\\\n"
      " & & & Col. & Seg. & Col. & Seg. & Col. & Seg.", rows, size="\\scriptsize")

# S19 sequential versus joint siting
JJ = json.load(open("joint.json")); JS = json.load(open("joint_sites.json"))
st = lambda r: "optimal ($10^{-4}$)" if r["sol_status"] == 1 else "best found in 1~h"
seq = JJ["sequential"]; jm = JJ["maxprofit"]; jc = JJ["compromise"]
rows = [f"Sequential (Stage~1, then Stage~2) & {', '.join(seq['cc'])} & {', '.join(seq['sc'])} & "
        f"{seq['maxprofit']/1e6:.2f} & {seq['compromise']['Z1']/1e6:.3f} & optimal ($10^{{-4}}$)",
        f"Joint, maximum profit & {', '.join(jm['cc'])} & {', '.join(jm['sc'])} & {jm['Z1']/1e6:.2f} & "
        f"{JS['compromise']['Z1']/1e6:.3f} & {st(jm)}",
        f"Joint, compromise & {', '.join(jc['cc'])} & {', '.join(jc['sc'])} & -- & {jc['Z1']/1e6:.3f} & "
        f"{'optimal ($10^{-4}$)' if jc['phase1']['sol_status'] == 1 and jc['phase2']['sol_status'] == 1 else 'best found in 1~h per phase'}"]
w("\\section{Sequential versus joint siting}\n\\label{sec:s-joint}\n")
table("tab:s-joint", f"Sequential and joint designs at the Stage~1 counts ({JJ['n_cc']} collection, {JJ['n_sc']} "
      "segregation centres; equal capital cost), with the equity rule, the coverage radii and every Stage~2 "
      "constraint. Max.\\ profit: Stage~2 profit maximum for the sites. Compromise: profit of the two-phase "
      "compromise on the baseline payoff bounds ($\\lambda^{*}$ = 0.45 in every row; for the joint maximum-profit "
      "row, the compromise is re-solved on its sites). Profit in million SAR.",
      "@{}p{0.17\\textwidth}p{0.30\\textwidth}p{0.13\\textwidth}rrp{0.12\\textwidth}@{}",
      "Design & Collection centres & Segregation centres & Max.\\ profit & Comp. & Status", rows,
      size="\\scriptsize")

# S20 recovery mandate decomposition, S21 processing cost and yield
RCs = json.load(open("recovery.json")); A_ = RCs["A"]; sar = M.SAR_USD
rows = []
for kind, lab in (("maxprofit", "Maximum profit"), ("compromise", "Compromise")):
    rows.append(f"\\multicolumn{{8}}{{l}}{{\\textit{{{lab}}}}} \\\\")
    for k in ("70", "80", "90"):
        v = A_[k][kind]
        rows.append(f"{k}\\% & {v['rev_r']*sar/1e6:.2f} & {v['rev_f']*sar/1e6:.2f} & {v['tc']*sar/1e6:.3f} & "
                    f"{v['oc']*sar/1e6:.2f} & {v['Z1']/1e6:.2f} & {v['slots']} & {v['t_rec']:,.1f}/{v['t_ref']:,.1f}/{v['t_disp']:,.1f}".replace(",", "{,}"))
w("\\section{Recovery mandates: what drives profit}\n\\label{sec:s-recovery}\n")
table("tab:s-recdec", "Profit at each recovery mandate, decomposed (million SAR over six periods). Rec./Ref.: "
      "revenue from recycled and refurbished output; Transport; Operating: fixed facility operating cost; Slots: "
      "facility-periods in operation; tonnes recycled/refurbished/disposed. No per-tonne processing cost, "
      "unit yields. The compromise uses the baseline payoff bounds.",
      "@{}lrrrrrrr@{}", "Mandate & Rec. & Ref. & Transport & Operating & Profit & Slots & Tonnes", rows,
      size="\\scriptsize")
rows = []
for r in RCs["B"]:
    d = r.get("delta")
    rows.append(f"{r['yield_']:.1f} & {n0(r['cost'])} & {r['70']/1e6:.2f} & {r['90']/1e6:.2f} & "
                f"{(d/1e6 if d is not None else float('nan')):+.2f}".replace("+", "$+$").replace("-", "$-$"))
be = RCs["breakeven"]
note = ("Break-even processing cost (90\\% and 70\\% equally profitable): "
        + "; ".join(f"yield {y}: " + (f"{be[y]:.0f}~USD/t" if be[y] is not None and be[y] >= 1 else "none ($\\le 0$)")
                    for y in ("1.0", "0.8", "0.6")) + ".")
table("tab:s-recgen", "Maximum profit (million SAR) at the 70\\% and 90\\% mandates with a per-tonne processing "
      "cost $c$ (USD/t, both recovery routes) and sold yield $y$; yields scale revenue only.",
      "@{}rrrrr@{}", "$y$ & $c$ & 70\\% & 90\\% & 90\\% $-$ 70\\%", rows, size="\\scriptsize", note=note)

# S22 computational effort by experiment
rows = []; tot = dict(n=0, total=0.0)
for name, solver, logs in CS.experiments():
    v = CS.summary(logs); tot["n"] += v["n"]; tot["total"] += v["total"]
    stopped = f"{v['superseded']} / {v['limited']}"
    rows.append(f"{name} & {solver} & {n0(v['n'])} & {v['total']:,.1f}".replace(",", "{,}") +
                f" & {v['median']:,.2f} & {v['max']:,.1f}".replace(",", "{,}") + f" & {v['infeasible']} & {stopped}")
rows.append("\\midrule")
rows.append(f"Total & & {n0(tot['n'])} & {tot['total']:,.1f}".replace(",", "{,}") + " & & & &")
table("tab:s-effort", "Computational effort by experiment: subproblems solved, total, median and longest solve time (s), "
      "subproblems proven infeasible, and subproblems stopped by the time limit that were re-solved to the gap / that "
      "remained stopped (best solution used and reported as such). Times are wall-clock solver times on the hardware of "
      "Table~S17, from the solve logs stored in each result file.",
      "@{}>{\\raggedright\\arraybackslash}p{0.38\\textwidth}lrrrrrr@{}",
      "Experiment & Solver & Solves & Total & Median & Max & Infeas. & Stopped", rows, size="\\scriptsize")

open("supp_tables.tex", "w").write("\n".join(out))
print("supp_tables.tex written")
