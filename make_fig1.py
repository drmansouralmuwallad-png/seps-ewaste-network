"""Figure 1: overview of the two-stage planning model."""
import json
import matplotlib
_S1 = json.load(open("stage1.json"))
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mp

plt.rcParams.update({"font.family": "DejaVu Sans", "savefig.bbox": "tight",
                     "savefig.dpi": 300, "pdf.fonttype": 42, "ps.fonttype": 42})

AMBER, TEAL, BLUE = "#d08a1e", "#2e8b74", "#3a76c4"
RED, PURPLE, GREEN = "#c0392b", "#7d4fa8", "#2e8b57"

fig, ax = plt.subplots(figsize=(11.2, 8.8))
ax.set_xlim(0, 100); ax.set_ylim(0, 100); ax.axis("off")


def box(x, y, w, h, ec, fc="white", lw=1.4, r=0.8):
    ax.add_patch(mp.FancyBboxPatch((x, y), w, h, boxstyle=f"round,pad=0.3,rounding_size={r}",
                 linewidth=lw, edgecolor=ec, facecolor=fc))


def ttl(x, y, s, c, fs=9.5, w="bold"):
    ax.text(x, y, s, ha="center", va="center", fontsize=fs, weight=w, color=c)


def body(x, y, s, fs=7.2, c="#333"):
    ax.text(x, y, s, ha="center", va="center", fontsize=fs, color=c, linespacing=1.6)


# ---- input data -----------------------------------------------------------
box(3, 90.5, 94, 7.5, AMBER, "#fdf6e8")
ttl(50, 96.2, "INPUT DATA", "#7a4f00", 10.5)
body(50, 92.9, "24 cities  |  6 periods  |  e-waste generation  |  budget  |  road distances  |  regional income", 7.6)

# ---- stage 1 --------------------------------------------------------------
box(3, 66, 94, 21.5, TEAL, "#f1f9f6")
box(4.6, 82.5, 4.6, 3.6, TEAL, TEAL, r=0.5)
ax.text(6.9, 84.3, "S1", ha="center", va="center", fontsize=9, weight="bold", color="white")
ttl(52, 84.3, "STAGE 1 :  Strategic Facility Location  (Integer Linear Program)", "#1d3f36", 10)
for i, (t, lines, c) in enumerate([
    ("Objective", "Minimise the number of\ncollection, then segregation\ncentres (set covering)", TEAL),
    ("Constraints", "Coverage: 300 km / 1,000 km\nCapacitated assignment\nOne-out  |  Equity  |  Budget", TEAL),
    ("Output", f"{_S1['n_collection']} collection centres\n{_S1['n_segregation']} segregation centres\n(24 candidate sites each)", TEAL)]):
    x = 6 + i * 30.5
    box(x, 68.5, 27.5, 12.5, "#bcd9d0")
    ttl(x + 13.75, 78.4, t, c, 8.6)
    body(x + 13.75, 73.5, lines)
    if i < 2:
        ax.annotate("", xy=(x + 30, 74.8), xytext=(x + 27.9, 74.8),
                    arrowprops=dict(arrowstyle="->", color=TEAL, lw=1.8))
ax.text(50, 64.4, "Facility locations feed into Stage 2", ha="center", fontsize=7.4,
        style="italic", color="#555")
ax.annotate("", xy=(50, 61.2), xytext=(50, 63.6),
            arrowprops=dict(arrowstyle="->", color="#777", lw=1.6))

# ---- stage 2 --------------------------------------------------------------
box(3, 4, 94, 57, BLUE, "#f3f7fd")
box(4.6, 55.5, 4.6, 3.6, BLUE, BLUE, r=0.5)
ax.text(6.9, 57.3, "S2", ha="center", va="center", fontsize=9, weight="bold", color="white")
ttl(52, 57.3, "STAGE 2 :  Operational Supply Chain Optimisation  (Multi-Objective MILP)", "#1b3a63", 10)
box(20, 51.2, 60, 3.4, "#9dc0e8", "#e8f1fb", lw=1)
body(50, 52.9, "Flow Allocation:  $\\alpha$ = 30% Recycle  |  $\\beta$ = 50% Refurbish  |  "
     "$\\gamma$ = 20% Dump  $\\rightarrow$  80% Material Recovery", 7.2)

for i, (t, lines, c, fc) in enumerate([
    ("Obj 1: Maximise Profit", "Sales of recycled material\nand refurbished products\nminus transport and operating costs", RED, "#fdf0ef"),
    ("Obj 2: Maximise Network\nUtilisation", "Share of facility-period\nslots in operation\nacross all tiers", PURPLE, "#f6f1fb"),
    ("Obj 3: Maximise Employment", "Workers for the tonnage handled\n(learning-adjusted) plus a\nstaffing floor per open facility", GREEN, "#eff8f2")]):
    x = 6 + i * 30.5
    box(x, 34.5, 27.5, 14, c, fc)
    ttl(x + 13.75, 45.4, t, c, 8.2)
    body(x + 13.75, 39.6, lines)

box(56, 25.5, 38, 7, "#e08a2e", "#fdf4e9")
ttl(75, 30.4, "Workforce Learning Curve", "#a85f10", 8.6)
body(75, 27.6, "Workers per tonne fall with cumulative experience  (LR = 0.85)", 7.2)

# ---- solution method: the box that carried the superseded terminology ----
box(6, 7, 38, 15, GREEN, "#eff8f2")
ttl(25, 19.3, "Solution Method", GREEN, 9)
body(25, 14.4, "Two-phase fuzzy max-min compromise\n"
     "(max-min level, then efficiency)\n"
     "Per-objective attainment readout", 7.2)

box(56, 7, 38, 15, AMBER, "#fdf6e8")
ttl(75, 19.3, "Benchmarks and checks", "#a85f10", 9)
body(75, 14.4, "Weighted sum (10 weight vectors)\n"
     "$\\varepsilon$-constraint (10 bound settings)\n"
     "All tied Stage 1 sitings re-evaluated", 7.2)

ax.plot([44.5, 55.5], [14.5, 14.5], ls="--", color="#999", lw=1.2)

fig.savefig("figures/fig1_framework.pdf")
print("Figure 1 regenerated")
