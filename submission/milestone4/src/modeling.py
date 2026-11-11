"""Milestones 3 and 4: data access, feature sets, leakage-free CV, pipelines, tuning and thresholds.

Everything here is fitted on `split == "train"` rows only. The chronological validation
split (2023-09-04 to 2023-12-31) is touched only by modeling.ipynb when it reports results.
2024 is sealed: load_model_frame() refuses any date on or after 2024-01-01.

Observational unit: 1 row = 1 city on 1 local (UTC+5) day; the target is that city's
spike label h days later.

Milestone 4 adds the random forest and histogram gradient boosting pipelines, their random-search
spaces (tune_random) and optional per-fold sample weights in oof_predict (fairness reweighing).
"""
import numpy as np
import pandas as pd
from sklearn.base import clone
from sklearn.compose import ColumnTransformer
from scipy.stats import loguniform, randint
from sklearn.dummy import DummyClassifier
from sklearn.ensemble import HistGradientBoostingClassifier, RandomForestClassifier
from sklearn.linear_model import LogisticRegression, Ridge
from sklearn.model_selection import GridSearchCV, RandomizedSearchCV, StratifiedGroupKFold
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import FunctionTransformer, StandardScaler
from sklearn.tree import DecisionTreeClassifier

from src.config import CLEAN_DIR, WINDOW_START

SEALED_FROM = pd.Timestamp("2024-01-01")
MASTER = CLEAN_DIR / "master_daily.parquet"

# ------------------------------------------------------------------
# Feature sets (names checked against the master in load_model_frame)
# ------------------------------------------------------------------
# AQ history as the margin over the city spike threshold (index - spike_threshold). The label is
# defined relative to each city's threshold (0.36 to 2.18), so the raw pooled index made the city
# dummies act as a threshold correction; the margin removes that.
AQ_HISTORY = ["persist_margin", "margin_lag1", "margin_lag2"]
AQ_HISTORY_RAW = ["persist_index", "index_lag1", "index_lag2"]          # Phase 3 encoding (sensitivity)
FIRE =["fire_cnt_up45_r300_all", "fire_cnt_up45_r300_all_lag1",
        "fire_cnt_up45_r300_all_lag2", "fire_cnt_up45_r300_all_lag3"]   # raw counts; log1p in the pipeline
# Wind sectors: 'calm' is identical to stagnant (vector-mean wind < 2 km/h, 631 of 631 rows), so
# with all 8 sector dummies stagnant would be a linear combination of them. NW, the most
# frequent sector, is the reference instead; stagnant then reads as "calm vs NW wind".
WEATHER = ["stagnant", "stagnant_lag1", "rh_mean_pct", "rain_day", "temp_range_c", "vec_len_kmh",
           "temp_mean_c"] + [f"wind_from_{s}" for s in ["n", "ne", "e", "se", "s", "sw", "w"]]
MONTHS = [f"month_{m:02d}" for m in range(2, 13)]                       # reference: January
CITY_DUMMIES = ["city_faisalabad", "city_multan", "city_rawalpindi", "city_sialkot",
                "city_rahim_yar_khan", "city_islamabad", "city_amritsar", "city_ferozepur",
                "city_ludhiana", "city_jalandhar"]                      # reference: Lahore
CALENDAR_PLACE = MONTHS + CITY_DUMMIES

FEATURE_SETS = {
    "full": AQ_HISTORY + FIRE + WEATHER + CALENDAR_PLACE,
    "weather_only": WEATHER + CALENDAR_PLACE,
    "no_fire": AQ_HISTORY + WEATHER + CALENDAR_PLACE,
}
# Raw-index version of the full set; kept outside FEATURE_SETS so the headline loops stay at 3 sets
FULL_RAW = AQ_HISTORY_RAW + FIRE + WEATHER + CALENDAR_PLACE
CONTINUOUS = AQ_HISTORY + AQ_HISTORY_RAW + ["rh_mean_pct", "temp_range_c", "vec_len_kmh", "temp_mean_c"]
# AQ history goes back to day t-2: a training row dated up to (horizon + 2) days after a held-out
# day carries that day's target index in the AQ-history columns (margins or raw index).
MAX_AQ_LAG = 2


# ------------------------------------------------------------------
# Data access
# ------------------------------------------------------------------
def load_model_frame(horizon=1, path=MASTER):
    """Master rows for one horizon, cleaned for modelling (decision D12).

    Adds the AQ-history margins (index - city spike threshold, the threshold learned on train
    in Milestone 2) and `suspect_target` (target day t+h is a suspect day, shifted within city),
    then drops the 3-day skip, rows with a missing target or feature, and rows whose feature day
    or target day is a suspect day. Returns (frame, drop_log) where drop_log counts the drops per split.
    """
    df = pd.read_parquet(path).sort_values(["city", "date"]).reset_index(drop=True)
    assert (df["date"] < SEALED_FROM).all(), "2024 is sealed: no date may be on or after 2024-01-01"
    target = f"target_spike_h{horizon}"
    missing = [c for c in AQ_HISTORY_RAW + ["spike_threshold"] if c not in df.columns]
    assert not missing, f"AQ columns not in the master: {missing}"
    for margin, raw in zip(AQ_HISTORY, AQ_HISTORY_RAW):
        df[margin] = df[raw] - df["spike_threshold"]
    feats = FEATURE_SETS["full"] + AQ_HISTORY_RAW
    missing = [c for c in feats + [target, "suspect_day", "split"] if c not in df.columns]
    assert not missing, f"feature names not in the master: {missing}"

    df["suspect_target"] = (df.groupby("city")["suspect_day"].shift(-horizon).fillna(0).astype(int))
    steps = {
        "skip split": df["split"] == "skip",
        "missing target": df[target].isna(),
        "missing feature": df[feats].isna().any(axis=1),
        "suspect feature day": df["suspect_day"] == 1,
        "suspect target day": df["suspect_target"] == 1,
    }
    keep = pd.Series(True, index=df.index)
    log = []
    for step, mask in steps.items():
        hit = keep & mask
        log.append(df[hit].groupby("split").size().rename(step))
        keep &= ~mask
    drop_log = pd.concat(log, axis=1).fillna(0).astype(int).T
    drop_log.index.name = "dropped because"

    out = df[keep].reset_index(drop=True)
    out[target] = out[target].astype(int)
    out[feats] = out[feats].astype(float)
    assert ((out["persist_margin"] >= 0).astype(int) == out["persist_spike"]).all(), \
        "today's margin >= 0 must equal persist_spike"
    return out, drop_log


def week_groups(dates):
    """Calendar week counted from WINDOW_START; every city shares the same week number."""
    return ((pd.to_datetime(dates) - pd.Timestamp(WINDOW_START)).dt.days // 7).to_numpy()


# ------------------------------------------------------------------
# Cross-validation (decision D5)
# ------------------------------------------------------------------
def purged_sgkf_splits(df, y, n_splits=5, seeds=range(5), horizon=1):
    """Purged, repeated StratifiedGroupKFold on the training rows of `df`.

    Group = calendar week shared by all cities, so a week is never split between the fit and
    score parts, and Islamabad / Rawalpindi (same CAMS cell) always fall in the same fold.
    Purge: drop from the fit part every row whose target day (t+1 .. t+horizon) falls on a
    held-out day. Embargo: also drop rows up to horizon + MAX_AQ_LAG days after a held-out day,
    whose AQ-history features contain a held-out day's target. Returns [(fit_idx, test_idx)].
    """
    groups = week_groups(df["date"])
    day = (pd.to_datetime(df["date"]) - pd.Timestamp(WINDOW_START)).dt.days.to_numpy()
    y = np.asarray(y)
    splits = []
    for seed in seeds:
        sgkf = StratifiedGroupKFold(n_splits=n_splits, shuffle=True, random_state=seed)
        for fit_idx, test_idx in sgkf.split(np.zeros(len(y)), y, groups):
            held = np.zeros(day.max() + horizon + MAX_AQ_LAG + 2, dtype=bool)
            held[np.unique(day[test_idx])] = True
            d = day[fit_idx]
            near = np.zeros(len(fit_idx), dtype=bool)
            for k in range(1, horizon + 1):                 # purge: target day held out
                near |= held[d + k]
            for k in range(1, horizon + MAX_AQ_LAG + 1):    # embargo: AQ history held out
                near |= held[np.clip(d - k, 0, None)] & (d - k >= 0)
            fit_kept = fit_idx[~near]
            assert not set(groups[fit_kept]) & set(groups[test_idx]), "fit and test weeks overlap"
            splits.append((fit_kept, test_idx))
    return splits


# ------------------------------------------------------------------
# Pipelines and grids (every transform is learned inside the fold)
# ------------------------------------------------------------------
def _log1p():
    return FunctionTransformer(np.log1p, feature_names_out="one-to-one")


def _lr_prep(features):
    """log1p + standardise fire counts, standardise continuous columns, pass binaries through."""
    fire = [c for c in features if c in FIRE]
    cont = [c for c in features if c in CONTINUOUS]
    binary = [c for c in features if c not in fire + cont]
    return ColumnTransformer([
        ("fire", Pipeline([("log1p", _log1p()), ("scale", StandardScaler())]), fire),
        ("cont", StandardScaler(), cont),
        ("bin", "passthrough", binary),
    ], verbose_feature_names_out=False)


def make_lr(features):
    """Logistic regression on the shared linear preprocessing."""
    # liblinear, not saga: saga hit 5,000 iterations without converging at large C with balanced
    # weights (8 s per fit); liblinear converges in < 0.2 s with the same fold PR-AUC (within 0.005).
    # intercept_scaling = 10 keeps liblinear's penalty on the intercept negligible.
    return Pipeline([("prep", _lr_prep(features)),
                     ("model", LogisticRegression(solver="liblinear", intercept_scaling=10,
                                                  max_iter=5000, random_state=42))])


def make_ridge(features):
    """Ridge regression of the continuous next-day index, same preprocessing as the LR."""
    return Pipeline([("prep", _lr_prep(features)), ("model", Ridge())])


def make_tree(features):
    """log1p on fire counts (keeps split points readable), no scaling."""
    fire = [c for c in features if c in FIRE]
    rest = [c for c in features if c not in fire]
    prep = ColumnTransformer([("fire", _log1p(), fire), ("rest", "passthrough", rest)],
                             verbose_feature_names_out=False)
    return Pipeline([("prep", prep), ("model", DecisionTreeClassifier(random_state=42))])


LR_GRID = {
    "model__C": np.logspace(-3, 2, 8),
    "model__l1_ratio": [0.0, 1.0],          # 0 = ridge (L2), 1 = lasso (L1); sklearn >= 1.8 API
    "model__class_weight": [None, "balanced"],
}
DT_GRID = {
    "model__max_depth": list(range(2, 9)),
    "model__min_samples_leaf": [10, 25, 50, 100],
    "model__class_weight": [None, "balanced"],
}
RIDGE_GRID = {"model__alpha": np.logspace(-2, 3, 11)}


def tune(pipe, grid, X, y, splits, n_jobs=-1, scoring="average_precision"):
    """Grid search on the purged folds, scored by PR-AUC by default (spikes are rare), refit on
    all train rows."""
    gs = GridSearchCV(pipe, grid, scoring=scoring, cv=splits, n_jobs=n_jobs,
                      refit=True, error_score="raise")
    return gs.fit(X, y)


# ------------------------------------------------------------------
# Milestone 4: ensemble models and random search
# ------------------------------------------------------------------
def make_rf(features):
    """Random forest on the tree preprocessing (log1p on fire counts, no scaling)."""
    prep = make_tree(features).named_steps["prep"]
    return Pipeline([("prep", prep),
                     ("model", RandomForestClassifier(random_state=42, n_jobs=1))])


def make_hgb(features):
    """Histogram gradient boosting on the tree preprocessing.

    early_stopping=False: HGB's early stopping holds out a random 10% of the fit rows, which would
    put neighbouring days of the same week on both sides and leak. The number of boosting rounds is
    tuned on the purged folds instead.
    """
    prep = make_tree(features).named_steps["prep"]
    return Pipeline([("prep", prep),
                     ("model", HistGradientBoostingClassifier(early_stopping=False, random_state=42))])


RF_DIST = {
    "model__n_estimators": [300, 500],
    "model__max_depth": [3, 4, 5, 6, 8, 10, 12, None],
    "model__min_samples_leaf": [5, 10, 25, 50, 100],
    "model__max_features": ["sqrt", 0.3, 0.5, 1.0],
    "model__class_weight": [None, "balanced", "balanced_subsample"],
}
HGB_DIST = {
    "model__learning_rate": loguniform(0.01, 0.3),
    "model__max_iter": randint(100, 601),
    "model__max_leaf_nodes": [7, 15, 31, 63],
    "model__max_depth": [None, 3, 5, 8],
    "model__min_samples_leaf": randint(10, 101),
    "model__l2_regularization": loguniform(1e-3, 10),
    "model__class_weight": [None, "balanced"],
}
N_ITER = 60


def tune_random(pipe, dist, X, y, splits, n_iter=N_ITER, seed=42, n_jobs=-1):
    """Random search on the purged folds, scored by PR-AUC, refit on all train rows."""
    rs = RandomizedSearchCV(pipe, dist, n_iter=n_iter, scoring="average_precision", cv=splits,
                            n_jobs=n_jobs, refit=True, random_state=seed, error_score="raise")
    return rs.fit(X, y)


def oof_predict(estimator, X, y, splits, n_jobs=-1, method="predict_proba", weight_fn=None):
    """Out-of-fold predictions for every training row (probabilities, or `predict` for Ridge).

    weight_fn(fit_idx) -> sample weights for the fit rows of one fold (Milestone 4 reweighing).
    The weights are computed from that fold's fit rows only, so held-out labels never enter.
    Returns (p_oof, folds): p_oof averages each row's held-out prediction over the repeats;
    folds is [(test_idx, p_test)] for per-fold metrics.
    """
    from joblib import Parallel, delayed

    def one(fit_idx, test_idx):
        if weight_fn is None:
            est = clone(estimator).fit(X.iloc[fit_idx], y[fit_idx])
        else:
            est = clone(estimator).fit(X.iloc[fit_idx], y[fit_idx], model__sample_weight=weight_fn(fit_idx))
        if method == "predict":
            return test_idx, est.predict(X.iloc[test_idx])
        return test_idx, est.predict_proba(X.iloc[test_idx])[:, 1]

    folds = Parallel(n_jobs=n_jobs)(delayed(one)(f, t) for f, t in splits)
    total, count = np.zeros(len(y)), np.zeros(len(y))
    for test_idx, p in folds:
        total[test_idx] += p
        count[test_idx] += 1
    assert (count > 0).all(), "every training row must be held out at least once"
    return total / count, folds


def choose_threshold(y, p, cost_fn=5, cost_fp=1):
    """Alert threshold that minimises cost_fn * FN + cost_fp * FP on out-of-fold predictions.

    Candidates are the distinct predicted values (alert when p >= threshold); ties go to the
    higher threshold (fewer alerts). Returns (threshold, cost per row).
    """
    y, p = np.asarray(y), np.asarray(p)
    order = np.argsort(-p, kind="stable")
    ps, ys = p[order], y[order]
    tp = np.cumsum(ys)
    fp = np.cumsum(1 - ys)
    last = np.r_[ps[1:] != ps[:-1], True]       # end of each block of tied scores
    cand, tp, fp = ps[last], tp[last], fp[last]
    cost = cost_fn * (ys.sum() - tp) + cost_fp * fp
    cand = np.r_[np.inf, cand]                  # +inf = never alert
    cost = np.r_[cost_fn * ys.sum(), cost]
    best = np.flatnonzero(cost == cost.min())[0]
    return float(cand[best]), float(cost[best] / len(y))


# ------------------------------------------------------------------
# Naive benchmarks
# ------------------------------------------------------------------
def make_majority():
    """Majority class: always 'no spike' (score is the training spike rate)."""
    return DummyClassifier(strategy="most_frequent")


def persistence(df):
    """Tomorrow repeats today. Prediction = persist_spike; score = today's margin over the
    city's spike threshold (persist_index - spike_threshold), so scores are comparable across
    cities with different thresholds and score >= 0 exactly when persist_spike == 1."""
    score = (df["persist_index"] - df["spike_threshold"]).to_numpy()
    yhat = df["persist_spike"].to_numpy().astype(int)
    assert ((score >= 0).astype(int) == yhat).all()
    return score, yhat
