"""Column-width figures for the Milestone 5 IEEE paper (3.45 in wide, 7 pt text).

The notebook figures (figures/fig_m05_*.png, fig_m04_*.png) are 15-18 in wide and unreadable at
IEEE column width. This script redraws the key panels from the same CSV tables in docs/tables/, so
every plotted value is a reported value. Output: figures/fig_m05_paper_*.png at 300 dpi.

Run from the repository root, after data_extension.ipynb:
    python docs/manuscript/make_figures_m5.py
"""
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from src import plotting as P  # noqa: E402

T = ROOT / "docs" / "tables"
OUT = ROOT / "figures"
W = 3.45
INIT_C, NEW_C = P.CAT_COLORS[0], P.CAT_COLORS[1]
MONTHS = ["J", "F", "M", "A", "M", "J", "J", "A", "S", "O", "N", "D"]
T1, T2, T3 = "Tier 1 metro (≥ 3 M)", "Tier 2 large (1–3 M)", "Tier 3 small (< 1 M)"

P.set_style()
plt.rcParams.update({"font.size": 7, "axes.titlesize": 7.5, "axes.labelsize": 7, "xtick.labelsize": 6.5,
                     "ytick.labelsize": 6.5, "legend.fontsize": 6.2, "axes.titleweight": "bold",
                     "figure.dpi": 300, "lines.linewidth": 1.2})


def save(fig, name):
    fig.tight_layout(pad=0.3)
    fig.savefig(OUT / f"fig_m05_paper_{name}.png", dpi=300, bbox_inches="tight", facecolor="white")
    plt.close(fig)


tab = lambda n: pd.read_csv(T / f"{n}.csv")

# 1. Label shift: next-day spike rate by calendar month
ts = tab("m5_target_shift")
mm = ts[ts.grouping == "month"].sort_values("group")
fig, ax = plt.subplots(figsize=(W, 1.75))
x = np.arange(12)
ax.bar(x - 0.2, 100 * mm.rate_ref, width=0.38, color=INIT_C, label="Initial wave (Aug 2022–Dec 2023)")
ax.bar(x + 0.2, 100 * mm.rate_new, width=0.38, color=NEW_C, label="New wave (2024)")
ax.set_xticks(x)
ax.set_xticklabels(MONTHS)
ax.set(ylabel="Next-day spike rate (%)", xlabel="Calendar month")
ax.legend(loc="upper center", frameon=False, ncol=1)
save(fig, "1_label_shift")

# 2. PSI per feature, whole wave and season-matched
dr = tab("m5_drift_features")
short = {"composite_smog_index": "Smog index", "persist_margin": "Index margin", "pm2_5_mean_ugm3": "PM2.5",
         "pm10_mean_ugm3": "PM10", "no2_mean_ugm3": "NO2", "so2_mean_ugm3": "SO2", "o3_mean_ugm3": "O3",
         "co_mean_ugm3": "CO", "temp_mean_c": "Mean temp.", "temp_range_c": "Temp. range", "rh_mean_pct": "Humidity",
         "vec_len_kmh": "Wind speed", "precip_sum_mm": "Rain (mm)", "fire_cnt_up45_r300_all": "Upwind fires",
         "fire_cnt_r300_all": "Fires 300 km", "fire_cnt_up45_r300_in": "Upwind fires, IN",
         "fire_cnt_up45_r300_pk": "Upwind fires, PK", "stagnant": "Stagnant", "rain_day": "Rain day",
         "wind_sector": "Wind sector"}
sm = dr[dr.comparison == "season-matched (Sep-Dec)"].set_index("feature")
ww = dr[dr.comparison == "whole wave"].set_index("feature")
order = sm.psi.sort_values().index
fig, ax = plt.subplots(figsize=(W, 3.0))
y = np.arange(len(order))
ax.barh(y - 0.2, ww.loc[order, "psi"], height=0.38, color=P.GREY, label="Whole wave")
ax.barh(y + 0.2, sm.loc[order, "psi"], height=0.38, color=NEW_C, label="Season-matched (Sep–Dec)")
for v, ls in [(0.10, "--"), (0.25, "-")]:
    ax.axvline(v, color="#000000", lw=0.7, ls=ls)
ax.set_yticks(y)
ax.set_yticklabels([short[f] for f in order])
ax.set(xlabel="Population Stability Index (dashed 0.10, solid 0.25)")
ax.legend(loc="lower right", frameon=False)
save(fig, "2_psi")

# 3. Calibration-in-the-large of the frozen LR by month
ms = tab("m5_monthly_skill").sort_values("month")
fig, ax = plt.subplots(figsize=(W, 1.8))
xm = np.arange(len(ms))
ax.plot(xm, 100 * ms.observed_rate, color="#000000", marker="o", ms=2.5, label="Observed spike rate")
ax.plot(xm, 100 * ms.mean_predicted, color=INIT_C, marker="s", ms=2.5, label="Mean predicted probability (frozen LR)")
k24 = int(np.flatnonzero(ms.month.to_numpy() == "2024-01")[0])
ax.axvline(k24 - 0.5, color=P.GREY, ls="--", lw=0.8)
ax.text(k24 - 0.3, 47, "2024 →", fontsize=6.5, color=P.GREY)
ticks = [i for i, mo in enumerate(ms.month) if mo.endswith(("-01", "-07"))]
ax.set_xticks(ticks)
ax.set_xticklabels([ms.month.iloc[i] for i in ticks])
ax.set(ylabel="Share of city-days (%)")
ax.legend(loc="upper left", frameon=False)
save(fig, "3_calibration_time")

# 4. PR-AUC by setting
th = tab("m5_three_way")
SET = {"(1) initial model, initial data (Sep-Dec 2023)": "(1) Initial\nSep–Dec 23",
       "(2b) initial model, zero-shot, Sep-Dec 2024": "(2) Zero-shot\nSep–Dec 24",
       "(3a) re-trained model, Sep-Dec 2024 test": "(3a) Re-trained\nSep–Dec 24",
       "(3b) re-trained model, combined data, purged CV": "(3b) Re-trained\ncombined CV"}
MOD = [("Persistence", "#000000"), ("LR full", P.CAT_COLORS[0]), ("RF full", P.CAT_COLORS[2]), ("HGB full", P.CAT_COLORS[3])]
fig, ax = plt.subplots(figsize=(W, 1.95))
for k, (m, col) in enumerate(MOD):
    d = th[(th.metric == "pr_auc") & (th.model == m)].set_index("setting").loc[list(SET)]
    xv = np.arange(len(SET)) + (k - 1.5) * 0.16
    err_lo = np.where(d.ci_low.notna(), d.estimate - d.ci_low, d.sd.fillna(0))
    err_hi = np.where(d.ci_high.notna(), d.ci_high - d.estimate, d.sd.fillna(0))
    ax.errorbar(xv, d.estimate, yerr=[err_lo, err_hi], fmt="o", ms=3, color=col, capsize=1.5, lw=0.9, label=m)
ax.set_xticks(range(len(SET)))
ax.set_xticklabels(SET.values(), fontsize=6)
ax.set(ylabel="PR-AUC", ylim=(0.2, 1.0))
ax.legend(loc="lower center", ncol=4, frameon=False, columnspacing=0.8, handletextpad=0.2)
save(fig, "4_three_way")

# 5. False-alarm rate and recall by tier across settings
gc = tab("m5_fair_group_ci")
SETS = [("(1) initial, Sep-Dec 2023", "(1) Initial, Sep–Dec 23", P.CAT_COLORS[0]),
        ("(2b) zero-shot, Sep-Dec 2024", "(2) Zero-shot, Sep–Dec 24", P.CAT_COLORS[1]),
        ("(3a) re-trained, Sep-Dec 2024", "(3a) Re-trained", P.CAT_COLORS[2]),
        ("(3a) re-trained, per-tier thresholds", "(3a) Re-trained, per-tier thr.", P.CAT_COLORS[4])]
groups = [T1, T2, T3]
fig, axes = plt.subplots(1, 2, figsize=(W, 1.9), sharey=True)
for ax, metric, title in [(axes[0], "tpr", "Recall (TPR)"), (axes[1], "fpr", "False-alarm rate (FPR)")]:
    for k, (s, lab, col) in enumerate(SETS):
        d = gc[(gc.setting == s) & (gc.metric == metric)].set_index("group").loc[groups]
        yv = np.arange(3) + (k - 1.5) * 0.18
        ax.errorbar(d.estimate, yv, xerr=[d.estimate - d.ci_low, d.ci_high - d.estimate], fmt="o", ms=2.8,
                    color=col, capsize=1.2, lw=0.8, label=lab)
    ax.set_title(title)
    ax.set_yticks(range(3))
    ax.set_yticklabels(["Tier 1\nmetro", "Tier 2\nlarge", "Tier 3\nsmall"])
axes[0].invert_yaxis()
h, l = axes[0].get_legend_handles_labels()
fig.legend(h, l, loc="lower center", ncol=2, frameon=False, bbox_to_anchor=(0.5, -0.17))
save(fig, "5_fairness_shift")

# 6. Milestone 4 Pareto frontier (training OOF), LR full and RF full
pa = tab("m4_pareto")
fig, ax = plt.subplots(figsize=(W, 2.0))
MK = {"single threshold": ("*", 40), "threshold per tier": ("P", 22), "predictive equality": ("o", 8),
      "equalized odds": ("s", 8), "reweighing": ("^", 14)}
for m, col in [("LR full", P.CAT_COLORS[0]), ("RF full", P.CAT_COLORS[2])]:
    d = pa[(pa.model == m) & (pa.data == "training OOF")]
    for meth, (mk, s) in MK.items():
        e = d[d.method == meth]
        ax.scatter(e.eo_diff, e.cost_per_1000, marker=mk, s=s, color=col, alpha=0.75, lw=0.3,
                   edgecolor="#000000" if mk == "*" else "white")
    fr = d[d.pareto].sort_values("eo_diff")
    ax.step(fr.eo_diff, fr.cost_per_1000, where="post", color=col, lw=1.0, label=f"{m} (Pareto frontier)")
from matplotlib.lines import Line2D  # noqa: E402
hh = [Line2D([], [], marker=mk, ls="", color=P.GREY, ms=4 if mk != "*" else 6, label=meth) for meth, (mk, _) in MK.items()]
h2, l2 = ax.get_legend_handles_labels()
ax.legend(handles=h2 + hh, loc="upper right", frameon=False, fontsize=5.6, ncol=2)
ax.set(xlabel="Equalized-odds gap between tiers", ylabel="Cost per 1,000 city-days")
save(fig, "6_pareto")

# 7. Milestone 4 cost curve (validation, FN:FP 1-20)
cc = tab("m4_cost_curve")
fig, ax = plt.subplots(figsize=(W, 1.8))
for m, col, ls in [("Persistence", "#000000", "-"), ("LR full", P.CAT_COLORS[0], "-"), ("DT full", P.CAT_COLORS[1], "--"),
                   ("RF full", P.CAT_COLORS[2], "-"), ("HGB full", P.CAT_COLORS[3], "-")]:
    d = cc[cc.model == m]
    ax.plot(d.ratio, d.cost_per_1000, color=col, ls=ls, label=m)
d = cc[cc.model == "Persistence"]
ax.plot(d.ratio, d.never_alert, color=P.GREY, ls=":", label="Never alert")
ax.axvline(5, color=P.GREY, lw=0.7, ls="--")
ax.set(xlabel="FN:FP cost ratio", ylabel="Cost per 1,000 city-days", ylim=(0, 700))
ax.legend(loc="upper left", frameon=False, ncol=2)
save(fig, "7_cost_curve")

print("wrote", sorted(p.name for p in OUT.glob("fig_m05_paper_*.png")))
