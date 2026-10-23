"""Milestone 3: metrics, block bootstrap, cost curve and error breakdown.

Each function returns plain numbers or a DataFrame so modeling.ipynb can print it and the
report can quote it. Thresholds always come in from outside (chosen on out-of-fold training
predictions); nothing here looks at validation rows to pick one.
"""
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import average_precision_score, roc_auc_score

from src.modeling import choose_threshold, week_groups

TABLE_DIR = Path("docs/tables")
COST_FN, COST_FP = 5, 1     # headline cost ratio (decision D6)


def binary_metrics(y, score, threshold=None, yhat=None, cost_fn=COST_FN, cost_fp=COST_FP):
    """Accuracy, precision, recall, specificity, F1, ROC-AUC, PR-AUC, Brier, confusion counts and
    the expected cost per 1,000 city-days. Pass either a threshold (alert when score >= threshold)
    or ready-made predictions `yhat` (persistence). AUCs are NaN when the score is constant or y
    has one class; Brier is NaN when the score is not a probability."""
    y, score = np.asarray(y).astype(int), np.asarray(score, dtype=float)
    yhat = (score >= threshold).astype(int) if yhat is None else np.asarray(yhat).astype(int)
    tp = int(((yhat == 1) & (y == 1)).sum())
    fp = int(((yhat == 1) & (y == 0)).sum())
    tn = int(((yhat == 0) & (y == 0)).sum())
    fn = int(((yhat == 0) & (y == 1)).sum())
    n = len(y)
    div = lambda a, b: a / b if b > 0 else np.nan
    prec, rec = div(tp, tp + fp), div(tp, tp + fn)
    ranked = np.unique(score).size > 1 and np.unique(y).size > 1
    is_prob = score.min() >= 0 and score.max() <= 1
    return {
        "accuracy": (tp + tn) / n, "precision": prec, "recall": rec,
        "specificity": div(tn, tn + fp),
        "f1": div(2 * tp, 2 * tp + fp + fn),
        "roc_auc": roc_auc_score(y, score) if ranked else np.nan,
        "pr_auc": average_precision_score(y, score) if ranked else np.nan,
        "brier": float(np.mean((score - y) ** 2)) if is_prob else np.nan,
        "tp": tp, "fp": fp, "tn": tn, "fn": fn, "n": n,
        "cost_per_1000": 1000 * (cost_fn * fn + cost_fp * fp) / n,
    }


def cv_metrics(y, folds, threshold=None, yhat=None):
    """Mean and SD of binary_metrics over the CV folds.

    folds = [(test_idx, score_test)]. Every fold uses the same threshold (chosen on the pooled
    out-of-fold predictions), which makes the fold scores slightly optimistic. With `yhat`
    (full-length array), the fold predictions are taken from it instead.
    """
    y = np.asarray(y)
    rows = [binary_metrics(y[t], s, threshold=threshold,
                           yhat=None if yhat is None else np.asarray(yhat)[t]) for t, s in folds]
    rows = pd.DataFrame(rows)
    return pd.concat([rows.mean().add_suffix("_mean"), rows.std().add_suffix("_sd")])


def block_bootstrap(df, fn, n=1000, seed=42):
    """95% percentile CIs by resampling whole calendar weeks (all cities together) of `df`.

    fn(sub_df) -> dict of numbers. Returns a DataFrame with the point estimate on the full
    frame and the 2.5% / 97.5% percentiles over the resamples. Paired differences are just an
    fn that returns model A minus model B on the same resample.
    """
    df = df.reset_index(drop=True)
    weeks = week_groups(df["date"])
    idx_by_week = [np.flatnonzero(weeks == w) for w in np.unique(weeks)]
    rng = np.random.default_rng(seed)
    point = fn(df)
    draws = []
    for _ in range(n):
        pick = rng.integers(0, len(idx_by_week), len(idx_by_week))
        draws.append(fn(df.iloc[np.concatenate([idx_by_week[i] for i in pick])]))
    draws = pd.DataFrame(draws)
    return pd.DataFrame({"estimate": pd.Series(point),
                         "ci_low": draws.quantile(0.025), "ci_high": draws.quantile(0.975),
                         "n_weeks": len(idx_by_week)})


def cost_curve(y_oof, p_oof, y_val, p_val, ratios=range(1, 21), yhat_val=None):
    """Validation cost per 1,000 city-days for each FN:FP ratio.

    For a scored model the threshold is re-optimised on the out-of-fold training predictions at
    every ratio; with `yhat_val` (persistence) the predictions stay fixed. Also returns the
    'never alert' and 'always alert' reference costs.
    """
    y_val = np.asarray(y_val).astype(int)
    n, pos = len(y_val), y_val.sum()
    rows = []
    for r in ratios:
        if yhat_val is None:
            thr, _ = choose_threshold(y_oof, p_oof, cost_fn=r, cost_fp=1)
            yhat = (np.asarray(p_val) >= thr).astype(int)
        else:
            thr, yhat = np.nan, np.asarray(yhat_val).astype(int)
        fn = int(((yhat == 0) & (y_val == 1)).sum())
        fp = int(((yhat == 1) & (y_val == 0)).sum())
        rows.append({"ratio": r, "threshold": thr, "fn": fn, "fp": fp,
                     "cost_per_1000": 1000 * (r * fn + fp) / n,
                     "never_alert": 1000 * r * pos / n, "always_alert": 1000 * (n - pos) / n})
    return pd.DataFrame(rows)


def error_breakdown(df, y, yhat, score, index_col="target_index_h1"):
    """Where the errors are.

    Onset days: the target is a spike while today is not (persist_spike == 0); continuation
    days: today is already a spike. Returns a dict of DataFrames: 'onset' (error type x day
    type), 'city_month' (FN / FP per city and month), 'top_fn' (10 missed spikes with the
    highest next-day index), 'top_fp' (10 false alarms with the highest score).
    """
    d = df[["city", "date", "persist_spike", index_col]].copy()
    d["y"], d["yhat"], d["score"] = np.asarray(y), np.asarray(yhat), np.asarray(score)
    d["error"] = np.select([(d.y == 1) & (d.yhat == 0), (d.y == 0) & (d.yhat == 1),
                            (d.y == 1) & (d.yhat == 1)], ["FN", "FP", "TP"], "TN")
    d["day_type"] = np.where(d.persist_spike == 1, "continuation", "onset")
    onset = pd.crosstab(d["error"], d["day_type"])
    d["month"] = d["date"].dt.strftime("%Y-%m")
    city_month = (d[d.error.isin(["FN", "FP"])]
                  .pivot_table(index=["city"], columns=["month", "error"], values="y",
                               aggfunc="size", fill_value=0))
    cols = ["city", "date", "day_type", index_col, "score"]
    top_fn = d[d.error == "FN"].nlargest(10, index_col)[cols]
    top_fp = d[d.error == "FP"].nlargest(10, "score")[cols]
    return {"onset": onset, "city_month": city_month, "top_fn": top_fn, "top_fp": top_fp, "rows": d}


def save_table(df, name, index=True):
    """Write docs/tables/<name>.csv at 4 decimals (the report reads only these files)."""
    path = TABLE_DIR / f"{name}.csv"
    path.parent.mkdir(parents=True, exist_ok=True)
    df.round(4).to_csv(path, index=index)
    return path
