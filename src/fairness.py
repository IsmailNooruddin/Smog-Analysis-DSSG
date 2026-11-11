"""Milestone 4: geographic fairness audit and bias mitigation.

Sensitive attribute = geography (agreed with the instructor): country (PK, IN), city (11) and a
city-size tier from census population (Dataset/external/city_population.csv, decision P1).
The "positive prediction" is a smog alert for tomorrow.

Everything that is chosen (weights, thresholds) is chosen on out-of-fold training predictions.
Validation rows are only scored.
"""
import numpy as np
import pandas as pd

from src.config import CITY_POP_FILE
from src.modeling import choose_threshold

TIER_LABEL = {1: "Tier 1 metro (≥ 3 M)", 2: "Tier 2 large (1–3 M)", 3: "Tier 3 small (< 1 M)"}
COUNTRY_LABEL = {"PK": "Pakistan", "IN": "India"}


# ------------------------------------------------------------------
# Groups
# ------------------------------------------------------------------
def load_city_tiers(path=CITY_POP_FILE):
    """City table with census population and tier (one row per city)."""
    tab = pd.read_csv(path)
    assert tab["city"].is_unique and len(tab) == 11, "expected one row for each of the 11 cities"
    assert set(tab["tier"]) == {1, 2, 3}
    return tab


def add_groups(df, tiers=None):
    """Adds `tier` (label) and `country_name` to a frame that has `city` and `country`."""
    tiers = load_city_tiers() if tiers is None else tiers
    out = df.copy()
    out["tier"] = out["city"].map(tiers.set_index("city")["tier"].map(TIER_LABEL))
    out["country_name"] = out["country"].map(COUNTRY_LABEL)
    assert out["tier"].notna().all() and out["country_name"].notna().all(), "city without a group"
    return out


# ------------------------------------------------------------------
# Group metrics and disparity
# ------------------------------------------------------------------
def _rates(y, yhat, cost_fn=5, cost_fp=1):
    y, yhat = np.asarray(y).astype(int), np.asarray(yhat).astype(int)
    tp = int(((yhat == 1) & (y == 1)).sum())
    fp = int(((yhat == 1) & (y == 0)).sum())
    pos, neg, n = int(y.sum()), int((y == 0).sum()), len(y)
    div = lambda a, b: a / b if b > 0 else np.nan
    return {"n": n, "spikes": pos, "base_rate": div(pos, n), "alerts": int(yhat.sum()),
            "selection_rate": div(int(yhat.sum()), n), "tpr": div(tp, pos), "fpr": div(fp, neg),
            "fnr": div(pos - tp, pos), "precision": div(tp, tp + fp), "fn": pos - tp, "fp": fp,
            "cost_per_1000": div(1000 * (cost_fn * (pos - tp) + cost_fp * fp), n)}


def group_metrics(y, yhat, groups, cost_fn=5, cost_fp=1):
    """One row per group: n, spikes, base rate, alerts, selection (alert) rate, TPR, FPR, FNR,
    precision, FN, FP and the cost per 1,000 city-days."""
    y, yhat, groups = np.asarray(y), np.asarray(yhat), np.asarray(groups)
    rows = {g: _rates(y[groups == g], yhat[groups == g], cost_fn, cost_fp) for g in sorted(set(groups))}
    out = pd.DataFrame(rows).T
    out.index.name = "group"
    return out


def disparity(gm, privileged):
    """Group-fairness summary from a group_metrics table.

    - dir_vs_priv_min / max: lowest and highest ratio of a group's alert rate to the privileged
      group's (disparate impact ratio, DIR). The 80% rule is read two-sided (0.8 to 1.25),
      because an alert both protects (fewer missed spikes) and costs (false alarms).
    - dir_min_over_max: lowest alert rate over the highest, over all groups.
    - dp_diff: max - min alert rate (demographic parity difference).
    - eop_diff: max - min TPR (equal opportunity). pe_diff: max - min FPR (predictive equality).
    - eo_diff: max(eop_diff, pe_diff) (equalized odds difference).
    Groups whose rate is undefined (no spikes or no clean days) are left out of that measure.
    """
    sel = gm["selection_rate"].astype(float)
    ratio = (sel / sel[privileged]).drop(privileged)
    spread = lambda col: float(gm[col].astype(float).max() - gm[col].astype(float).min())
    out = {"dir_vs_priv_min": float(ratio.min()), "dir_vs_priv_max": float(ratio.max()),
           "dir_min_over_max": float(sel.min() / sel.max()) if sel.max() > 0 else np.nan,
           "dp_diff": spread("selection_rate"), "eop_diff": spread("tpr"), "pe_diff": spread("fpr")}
    out["eo_diff"] = max(out["eop_diff"], out["pe_diff"])
    out["passes_80_rule"] = bool((ratio >= 0.8).all() and (ratio <= 1.25).all())
    return out


def disparity_fn(y_col, yhat_col, group_col, privileged):
    """fn(frame) -> disparity dict, for evaluate.block_bootstrap."""
    def fn(d):
        gm = group_metrics(d[y_col], d[yhat_col], d[group_col])
        if privileged not in gm.index:
            return {k: np.nan for k in ["dir_vs_priv_min", "dir_vs_priv_max", "dir_min_over_max",
                                        "dp_diff", "eop_diff", "pe_diff", "eo_diff"]}
        out = disparity(gm, privileged)
        out.pop("passes_80_rule")
        return out
    return fn


# ------------------------------------------------------------------
# Pre-processing mitigation: reweighing (Kamiran and Calders, 2012)
# ------------------------------------------------------------------
def reweigh_weights(groups, y, alpha=1.0):
    """w(g, y) = P(g) P(y) / P(g, y), raised to alpha (0 = no reweighing, 1 = full) and scaled to
    mean 1. Group and label become independent in the weighted fit data."""
    groups, y = np.asarray(groups), np.asarray(y).astype(int)
    d = pd.DataFrame({"g": groups, "y": y})
    pg = d["g"].map(d["g"].value_counts(normalize=True))
    py = d["y"].map(d["y"].value_counts(normalize=True))
    pgy = d.groupby(["g", "y"])["y"].transform("size") / len(d)
    w = ((pg * py / pgy) ** alpha).to_numpy()
    return w / w.mean()


# ------------------------------------------------------------------
# Post-processing mitigation: group-specific thresholds
# ------------------------------------------------------------------
def apply_thresholds(p, groups, thr):
    """Alert when p >= the threshold of the row's group (thr = {group: threshold})."""
    p, groups = np.asarray(p), np.asarray(groups)
    t = np.array([thr[str(g)] for g in groups], dtype=float)
    return (p >= t).astype(int)


def group_thresholds(y, p, groups, cost_fn=5, cost_fp=1):
    """Cost-optimal threshold for each group separately (asymmetric threshold tuning per group)."""
    y, p, groups = np.asarray(y), np.asarray(p), np.asarray(groups)
    return {str(g): choose_threshold(y[groups == g], p[groups == g], cost_fn, cost_fp)[0]
            for g in sorted(set(groups))}


def _curve(y, p, cost_fn, cost_fp):
    """Every candidate threshold of one group (alert when p >= t; +inf = never) with its TPR,
    FPR and cost in counts."""
    y, p = np.asarray(y).astype(int), np.asarray(p, dtype=float)
    order = np.argsort(-p, kind="stable")
    ps, ys = p[order], y[order]
    last = np.r_[ps[1:] != ps[:-1], True]
    tp, fp = np.cumsum(ys)[last], np.cumsum(1 - ys)[last]
    pos, neg = ys.sum(), len(ys) - ys.sum()
    thr = np.r_[np.inf, ps[last]]
    tp, fp = np.r_[0, tp], np.r_[0, fp]
    return {"thr": thr, "tpr": tp / max(pos, 1), "fpr": fp / max(neg, 1),
            "cost": cost_fn * (pos - tp) + cost_fp * fp}


def constrained_thresholds(y, p, groups, eps, kind="eo", cost_fn=5, cost_fp=1,
                           fpr_grid=np.arange(0, 0.3001, 0.0025), tpr_grid=np.arange(0, 1.0001, 0.02)):
    """Group thresholds that minimise the total cost subject to a fairness band of width eps.

    kind="fpr" (predictive equality): every group's FPR lies within eps/2 of a common target f,
    so the max FPR gap is at most eps. kind="eo" (equalized odds): the same band on FPR and on
    TPR (target pair f, t). The targets are searched on a grid; per group the cheapest threshold
    inside the band is taken. Returns (thresholds, total cost in counts), or (None, inf) when no
    target is feasible.
    """
    y, p, groups = np.asarray(y), np.asarray(p), np.asarray(groups)
    curves = {str(g): _curve(y[groups == g], p[groups == g], cost_fn, cost_fp) for g in sorted(set(groups))}
    half = eps / 2 + 1e-12
    targets = ([(f, None) for f in fpr_grid] if kind == "fpr"
               else [(f, t) for f in fpr_grid for t in tpr_grid])
    best, best_cost = None, np.inf
    for f, t in targets:
        pick, total = {}, 0.0
        for g, c in curves.items():
            ok = np.abs(c["fpr"] - f) <= half
            if t is not None:
                ok &= np.abs(c["tpr"] - t) <= half
            if not ok.any():
                break
            k = np.flatnonzero(ok)[np.argmin(c["cost"][ok])]
            pick[g], total = float(c["thr"][k]), total + c["cost"][k]
        else:
            if total < best_cost:
                best, best_cost = pick, total
    return best, best_cost


def pareto_mask(cost, gap):
    """True for points that no other point beats on both cost and gap (lower is better)."""
    cost, gap = np.asarray(cost, dtype=float), np.asarray(gap, dtype=float)
    keep = np.ones(len(cost), dtype=bool)
    for i in range(len(cost)):
        dominated = (cost <= cost[i]) & (gap <= gap[i]) & ((cost < cost[i]) | (gap < gap[i]))
        keep[i] = not dominated.any()
    return keep
