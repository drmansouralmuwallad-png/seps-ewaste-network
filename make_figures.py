"""Generate main-text Figures 3 and 4 (learning-rate effect, price/volume sensitivity) from the solver output.

Every value plotted is read from results.json / lr_sweep.json; nothing is typed in.
Run:  python3 make_figures.py
"""
import json, math
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

plt.rcParams.update({
    "font.family": "DejaVu Sans", "font.size": 9,
    "axes.edgecolor": "#444444", "axes.labelcolor": "#222222",
    "xtick.color": "#444444", "ytick.color": "#444444",
    "axes.spines.top": False, "axes.spines.right": False,
    "savefig.bbox": "tight", "savefig.dpi": 300, "figure.dpi": 150,
    "pdf.fonttype": 42, "ps.fonttype": 42,
})
BLUE, GREEN, ORANGE, GREY = "#2b6cb0", "#2f855a", "#c05621", "#718096"

R = json.load(open("results.json"))
bnd = {k: tuple(v) for k, v in R["bounds"].items()}
ideal = R["ideal"]


def norm(sol):
    v = [(sol[k] - bnd[k][0]) / (bnd[k][1] - bnd[k][0]) for k in ("Z1", "Z2", "Z3")]
    return [0.0 if abs(x) < 5e-4 else x for x in v]


ws = max(R["ws"], key=lambda r: r["NOS"])
ec = max([e for e in R["ec"] if "Z1" in e], key=lambda r: r["NOS"])
mm = R["maxmin"]
METHODS = [("Weighted sum", ws, GREY), ("$\\varepsilon$-constraint", ec, ORANGE),
           ("Fuzzy max-min", mm, BLUE)]
OBJ = ["Profit\n$Z_1$", "Utilisation\n$Z_2$", "Employment\n$Z_3$"]


# ---------------------------------------------------- Figure 3: trade-off radar
def fig3():
    ang = np.linspace(0, 2 * np.pi, 3, endpoint=False).tolist()
    ang += ang[:1]
    fig, ax = plt.subplots(figsize=(5.0, 4.6), subplot_kw=dict(polar=True))
    for name, sol, c in METHODS:
        v = norm(sol); v += v[:1]
        ls = "-" if "Fuzzy" in name else "--"
        lw = 2.4 if "Fuzzy" in name else 1.6
        ax.plot(ang, v, ls, lw=lw, color=c, label=name.replace("-", "\u2013") if "max" in name else name)
        ax.fill(ang, v, color=c, alpha=0.12 if "Fuzzy" in name else 0.05)
    ax.set_xticks(ang[:-1])
    ax.set_xticklabels([o.replace("\n", " ") for o in OBJ], fontsize=9)
    ax.set_ylim(0, 1.05); ax.set_yticks([0.25, 0.5, 0.75, 1.0])
    ax.set_yticklabels(["0.25", "0.50", "0.75", "1.00"], fontsize=7, color="#888")
    ax.grid(color="#dddddd", lw=0.7)
    ax.set_title("Normalised objective attainment by method", pad=18, fontsize=10)
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.06), ncol=3,
              frameon=False, fontsize=8)
    fig.savefig("figures/fig3_tradeoff.pdf"); plt.close(fig)
    print("fig3_tradeoff.pdf")


# ------------------------------------- Figure 4: membership attainment (centrepiece)
def fig4():
    fig, ax = plt.subplots(figsize=(6.6, 3.5))
    x = np.arange(3); w = 0.26
    for i, (name, sol, c) in enumerate(METHODS):
        v = norm(sol)
        b = ax.bar(x + (i - 1) * w, v, w, color=c, edgecolor="white", lw=0.6,
                   label=name.replace("-", "\u2013") if "max" in name else name)
        for rect, val in zip(b, v):
            ax.text(rect.get_x() + rect.get_width() / 2, val + 0.025, f"{val:.3f}",
                    ha="center", va="bottom", fontsize=7.5, color=c)
    ax.set_xticks(x); ax.set_xticklabels(OBJ)
    ax.set_ylabel("Normalised attainment $T_k$")
    ax.set_ylim(0, 1.30)
    ax.axhline(0, color="#444", lw=0.8)
    ax.legend(loc="upper right", frameon=False, fontsize=8, ncol=1)

    # annotate the floor and dispersion, which is the paper's argument
    tm = [min(norm(s)) for _, s, _ in METHODS]
    dt = [max(norm(s)) - min(norm(s)) for _, s, _ in METHODS]
    txt = (f"Attainment floor $T_{{\\min}}$:  {tm[0]:.3f} / {tm[1]:.3f} / "
           f"$\\bf{{{tm[2]:.3f}}}$\n"
           f"Dispersion $\\Delta_T$:  {dt[0]:.3f} / {dt[1]:.3f} / $\\bf{{{round(dt[2],3):.3f}}}$")
    ax.text(0.015, 0.97, txt, transform=ax.transAxes, va="top", ha="left", fontsize=8,
            bbox=dict(boxstyle="round,pad=0.45", fc="#f7fafc", ec="#cbd5e0", lw=0.8))
    fig.savefig("figures/fig3_membership.pdf"); plt.close(fig)
    print("fig3_membership.pdf")


# ---------------------------------------------------- Figure 5: sensitivity tornado
def fig5():
    rows = []
    for r in R["sens"]:
        if "dZ1" in r:
            rows.append((r["parameter"], r["change"], r["dZ1"]))
    agg = {}
    for name, ch, d in rows:
        agg.setdefault(name, []).append((ch, d))
    order = sorted(agg, key=lambda k: -max(abs(d) for _, d in agg[k]))
    fig, ax = plt.subplots(figsize=(6.4, 3.1))
    for i, name in enumerate(order):
        for ch, d in agg[name]:
            c = GREEN if d >= 0 else "#a0392c"
            ax.barh(i, d, height=0.5, color=c, alpha=0.85 if ch > 0 else 0.55,
                    edgecolor="white", lw=0.5)
            ax.text(d + (0.8 if d >= 0 else -0.8), i, f"{d:+.2f}%",
                    va="center", ha="left" if d >= 0 else "right", fontsize=7.5,
                    color="#333")
    ax.set_yticks(range(len(order)))
    ax.set_yticklabels([n.replace("E-waste collection", "Collection") for n in order], fontsize=8.5)
    ax.invert_yaxis()
    ax.axvline(0, color="#444", lw=0.9)
    ax.set_xlabel("Change in compromise profit (%)")
    lim = max(abs(d) for _, _, d in rows) * 1.25
    ax.set_xlim(-lim, lim)
    ax.text(0.99, 0.04, "darker = upward perturbation", transform=ax.transAxes,
            ha="right", fontsize=7, color="#888")
    fig.savefig("figures/fig4_tornado.pdf"); plt.close(fig)
    print("fig4_tornado.pdf")


# ---------------------------------------------------- Figure 6: workforce learning
def fig6():
    sw = json.load(open("lr_sweep.json"))
    lr = [o["LR"] for o in sw]; emp = [o["Z3"] for o in sw]
    pr = [o["Z1"] / 1e6 for o in sw]
    fig, ax = plt.subplots(figsize=(6.0, 3.3))
    ax.plot(lr, emp, "o-", color=BLUE, lw=2.0, ms=5, label="Employment")
    for a, b in zip(lr, emp):
        ax.annotate(f"{b:,.0f}", (a, b), textcoords="offset points", xytext=(0, 8),
                    ha="center", fontsize=7.5, color=BLUE)
    ax.set_xlabel("Learning rate $LR$   (lower = faster learning)")
    ax.set_ylabel("Employment (worker-periods)", color=BLUE)
    ax.tick_params(axis="y", colors=BLUE)
    ax.set_ylim(min(emp) * 0.93, max(emp) * 1.10)
    ax.axvline(0.85, color=GREY, ls=":", lw=1.2)
    ax.text(0.852, min(emp) * 0.955, "baseline", fontsize=7.5, color=GREY)

    ax2 = ax.twinx()
    ax2.plot(lr, pr, "s--", color=ORANGE, lw=1.6, ms=4, label="Profit")
    ax2.set_ylabel("Compromise profit (M SAR)", color=ORANGE)
    ax2.tick_params(axis="y", colors=ORANGE)
    ax2.set_ylim(min(pr) - 2, max(pr) + 2)
    ax2.spines["right"].set_visible(True); ax2.spines["top"].set_visible(False)
    
    h1, l1 = ax.get_legend_handles_labels(); h2, l2 = ax2.get_legend_handles_labels()
    ax.legend(h1 + h2, l1 + l2, loc="upper left", frameon=False, fontsize=8)
    fig.savefig("figures/fig3_learning.pdf"); plt.close(fig)
    print("fig3_learning.pdf")


if __name__ == "__main__":
    import os
    os.makedirs("figures", exist_ok=True)
    fig5(); fig6()   # fig4() (attainment chart) dropped: it repeated Table 4
