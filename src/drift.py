"""Milestone 5: covariate-shift, label-shift and concept-drift tests between two data waves.

- Feature (covariate) drift: two-sample Kolmogorov-Smirnov test for continuous columns, chi-square
  test of homogeneity for binary or categorical columns, and the Population Stability Index (PSI)
  for both. p-values are adjusted with the Benjamini-Hochberg false-discovery rate.
- Joint shift: a domain classifier ("adversarial validation") tries to tell the waves apart.
  A cross-validated ROC-AUC of 0.5 means the waves cannot be told apart.
- Concept drift: a pooled logit with wave x predictor interactions. The interaction block tests
  whether P(spike | X) changed between the waves.

Every function compares a reference sample (the initial wave) with a new sample.
"""
import numpy as np
import pandas as pd
import statsmodels.api as sm
from scipy import stats
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import StratifiedGroupKFold

PSI_EPS = 1e-4                       # smoothing so empty bins do not give log(0)
PSI_BANDS = [(0.10, "stable"), (0.25, "moderate shift")]   # >= 0.25: major shift


def psi_band(v):
    for cut, label in PSI_BANDS:
        if v < cut:
            return label
    return "major shift"


def _bin_shares(ref, new, bins):
    """Shares per bin. Continuous: reference-quantile edges (ties merged). Few distinct values:
    one bin per value seen in either sample."""
    ref, new = np.asarray(ref, float), np.asarray(new, float)
    ref, new = ref[~np.isnan(ref)], new[~np.isnan(new)]
    values = np.union1d(np.unique(ref), np.unique(new))
    if len(values) <= bins:
        r = np.array([(ref == v).mean() for v in values])
        n = np.array([(new == v).mean() for v in values])
        return r, n
    edges = np.unique(np.quantile(ref, np.linspace(0, 1, bins + 1)[1:-1]))
    r = np.bincount(np.searchsorted(edges, ref, side="right"), minlength=len(edges) + 1) / len(ref)
    n = np.bincount(np.searchsorted(edges, new, side="right"), minlength=len(edges) + 1) / len(new)
    return r, n


def psi(ref, new, bins=10, eps=PSI_EPS):
    """Population Stability Index: sum over bins of (new - ref) * ln(new / ref)."""
    r, n = _bin_shares(ref, new, bins)
    r, n = np.clip(r, eps, None), np.clip(n, eps, None)
    return float(np.sum((n - r) * np.log(n / r)))


def bh_fdr(p):
    """Benjamini-Hochberg adjusted p-values (q-values), same order as the input."""
    p = np.asarray(p, float)
    order = np.argsort(p)
    ranked = p[order] * len(p) / np.arange(1, len(p) + 1)
    q = np.minimum.accumulate(ranked[::-1])[::-1]
    out = np.empty_like(q)
    out[order] = np.minimum(q, 1.0)
    return out


def chi2_homogeneity(ref, new):
    """Chi-square test that the category shares are the same in both samples."""
    ref, new = pd.Series(ref).dropna(), pd.Series(new).dropna()
    cats = sorted(set(ref.unique()) | set(new.unique()))
    table = np.array([[int((ref == c).sum()) for c in cats], [int((new == c).sum()) for c in cats]])
    table = table[:, table.sum(axis=0) > 0]
    if table.shape[1] < 2:
        return np.nan, np.nan, 0
    chi2, p, dof, _ = stats.chi2_contingency(table, correction=False)
    return float(chi2), float(p), int(dof)


def drift_table(ref, new, cont_cols, cat_cols, bins=10, labels=None):
    """One row per column: test, statistic, p-value, BH q-value, PSI and its band, and the
    mean (or share) in each sample. labels: optional {column: readable name}."""
    rows = []
    for c in cont_cols:
        a, b = ref[c].dropna().astype(float), new[c].dropna().astype(float)
        ks = stats.ks_2samp(a, b)
        rows.append({"feature": c, "type": "continuous", "test": "KS", "statistic": float(ks.statistic),
                     "p_value": float(ks.pvalue), "psi": psi(a, b, bins), "ref_mean": a.mean(),
                     "new_mean": b.mean(), "ref_sd": a.std(), "new_sd": b.std(),
                     "std_mean_diff": (b.mean() - a.mean()) / a.std() if a.std() > 0 else np.nan,
                     "n_ref": len(a), "n_new": len(b)})
    for c in cat_cols:
        a, b = ref[c].dropna(), new[c].dropna()
        chi2, p, dof = chi2_homogeneity(a, b)
        num = pd.api.types.is_numeric_dtype(a)
        rows.append({"feature": c, "type": "binary/categorical", "test": f"chi-square (df {dof})",
                     "statistic": chi2, "p_value": p,
                     "psi": psi(pd.factorize(pd.concat([a, b]))[0][:len(a)],
                                pd.factorize(pd.concat([a, b]))[0][len(a):], bins),
                     "ref_mean": a.astype(float).mean() if num else np.nan,
                     "new_mean": b.astype(float).mean() if num else np.nan,
                     "ref_sd": np.nan, "new_sd": np.nan, "std_mean_diff": np.nan,
                     "n_ref": len(a), "n_new": len(b)})
    out = pd.DataFrame(rows)
    out["q_value_bh"] = bh_fdr(out["p_value"].fillna(1.0))
    out["significant_q05"] = (out["q_value_bh"] < 0.05).astype(int)
    out["psi_band"] = out["psi"].map(psi_band)
    if labels:
        out.insert(1, "label", out["feature"].map(labels).fillna(out["feature"]))
    return out


def domain_auc(X_ref, X_new, groups, n_splits=5, seed=42):
    """Cross-validated ROC-AUC of a shallow gradient-boosting classifier that predicts the wave
    (0 = reference, 1 = new) from X. Folds are grouped (e.g. by calendar week) so neighbouring
    days never sit on both sides. Returns (auc, out-of-fold scores, permutation importances)."""
    X = pd.concat([X_ref, X_new], ignore_index=True).astype(float)
    y = np.r_[np.zeros(len(X_ref)), np.ones(len(X_new))].astype(int)
    oof = np.zeros(len(y))
    cv = StratifiedGroupKFold(n_splits=n_splits, shuffle=True, random_state=seed)
    for fit, test in cv.split(X, y, groups):
        clf = HistGradientBoostingClassifier(max_depth=3, max_iter=200, learning_rate=0.05,
                                             early_stopping=False, random_state=seed)
        clf.fit(X.iloc[fit], y[fit])
        oof[test] = clf.predict_proba(X.iloc[test])[:, 1]
    return float(roc_auc_score(y, oof)), oof, y


def concept_lr_test(df, terms, wave_col, cluster_col, controls=()):
    """Pooled logit: y ~ terms + controls + wave + wave x terms.

    Returns (per-term table, summary dict). The per-term table gives the reference-wave odds ratio of
    each term and the ratio of odds ratios (new / reference) from the interaction, with city-cluster
    robust 95% CIs. The summary holds the likelihood-ratio test and the cluster-robust Wald test of
    all interactions together (H0: P(spike | X) is the same in both waves)."""
    y = df["y"].astype(int).to_numpy()
    base = df[list(terms) + list(controls)].astype(float)
    w = df[wave_col].astype(float)
    inter = base[list(terms)].mul(w, axis=0).add_suffix("_x_new")
    X_r = sm.add_constant(pd.concat([base, w.rename("wave_new")], axis=1))
    X_f = pd.concat([X_r, inter], axis=1)
    groups = pd.factorize(df[cluster_col])[0]
    fit_r = sm.Logit(y, X_r).fit(disp=0, maxiter=200)
    fit_f = sm.Logit(y, X_f).fit(disp=0, maxiter=200)
    fit_c = sm.Logit(y, X_f).fit(disp=0, maxiter=200, cov_type="cluster", cov_kwds={"groups": groups})
    lr = 2 * (fit_f.llf - fit_r.llf)
    k = inter.shape[1]
    names = list(inter.columns)
    R = np.zeros((k, X_f.shape[1]))
    for i, n in enumerate(names):
        R[i, list(X_f.columns).index(n)] = 1
    wald = fit_c.wald_test(R, scalar=True)
    ci = fit_c.conf_int()
    rows = []
    for t in terms:
        ti = f"{t}_x_new"
        rows.append({"term": t,
                     "or_reference_wave": np.exp(fit_c.params[t]),
                     "or_ref_lo": np.exp(ci.loc[t, 0]), "or_ref_hi": np.exp(ci.loc[t, 1]),
                     "ratio_of_or_new_vs_ref": np.exp(fit_c.params[ti]),
                     "ratio_lo": np.exp(ci.loc[ti, 0]), "ratio_hi": np.exp(ci.loc[ti, 1]),
                     "p_interaction_cluster": float(fit_c.pvalues[ti])})
    rows.append({"term": "wave (new vs reference), intercept shift",
                 "ratio_of_or_new_vs_ref": np.exp(fit_c.params["wave_new"]),
                 "ratio_lo": np.exp(ci.loc["wave_new", 0]), "ratio_hi": np.exp(ci.loc["wave_new", 1]),
                 "p_interaction_cluster": float(fit_c.pvalues["wave_new"])})
    summary = {"n": int(len(y)), "events": int(y.sum()), "events_reference": int(y[w.to_numpy() == 0].sum()),
               "events_new": int(y[w.to_numpy() == 1].sum()), "interactions": k,
               "lr_stat": float(lr), "lr_df": k, "lr_p": float(stats.chi2.sf(lr, k)),
               "wald_cluster_stat": float(np.squeeze(wald.statistic)), "wald_cluster_p": float(wald.pvalue),
               "pseudo_r2_restricted": float(fit_r.prsquared), "pseudo_r2_full": float(fit_f.prsquared)}
    return pd.DataFrame(rows), summary


def calibration_table(y, p, bins=(0, .02, .05, .1, .2, .4, .6, 1.0001)):
    """Observed spike rate against mean predicted probability in fixed probability bins."""
    d = pd.DataFrame({"y": np.asarray(y), "p": np.asarray(p)})
    d["bin"] = pd.cut(d["p"], bins, right=False)
    g = d.groupby("bin", observed=True).agg(n=("y", "size"), mean_predicted=("p", "mean"), observed_rate=("y", "mean"))
    return g.reset_index().assign(bin=lambda t: t["bin"].astype(str))
