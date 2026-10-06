"""Role 2, Part 2B: small, reusable EDA helpers used by merge_analysis.ipynb.

Each function returns a DataFrame so the notebook can print it and the report can
quote it. Nothing here chooses rows: the notebook passes the training rows in.
"""
import numpy as np
import pandas as pd
from scipy import stats


def summary_table(df, cols, labels=None):
    """Mean, median, SD, IQR and skewness for each column (resistant vs non-resistant)."""
    rows = []
    for c in cols:
        x = df[c].astype(float).dropna()
        q1, q3 = x.quantile([0.25, 0.75])
        rows.append({
            "variable": (labels or {}).get(c, c), "n": len(x),
            "mean": x.mean(), "median": x.median(), "sd": x.std(), "iqr": q3 - q1,
            "skew": x.skew(),
            "mean_minus_median_in_sd": (x.mean() - x.median()) / x.std() if x.std() > 0 else np.nan,
            "share_zero_pct": 100 * (x == 0).mean(),
        })
    return pd.DataFrame(rows).set_index("variable")


def outlier_audit(df, cols, labels=None):
    """Both rules from the rubric on each column, plus the two side-effects they cause.

    z-rule: |z| > 3 with the column's own mean and SD.  IQR rule: outside Q1 - 1.5 IQR, Q3 + 1.5 IQR.
    iqr_only: points beyond the IQR fences that the z-rule does not flag.
    masking: the extreme values inflate the SD, which hides other extreme points from the z-rule.
             'z_new_after_removal' re-applies the z-rule after removing the first-pass z-outliers;
             every new hit is a point the first pass had masked.
    variance inflation: SD with all points vs SD without the IQR outliers.
    """
    rows = []
    for c in cols:
        x = df[c].astype(float).dropna()
        z = (x - x.mean()) / x.std()
        z_out = z.abs() > 3
        q1, q3 = x.quantile([0.25, 0.75])
        lo, hi = q1 - 1.5 * (q3 - q1), q3 + 1.5 * (q3 - q1)
        iqr_out = (x < lo) | (x > hi)
        rest = x[~z_out]
        z2 = ((rest - rest.mean()) / rest.std()).abs() > 3 if rest.std() > 0 else rest * 0 > 0
        sd_all, sd_clean = x.std(), x[~iqr_out].std()
        rows.append({
            "variable": (labels or {}).get(c, c), "n": len(x),
            "z_outliers": int(z_out.sum()), "iqr_outliers": int(iqr_out.sum()),
            "iqr_pct": 100 * iqr_out.mean(),
            "iqr_only": int((iqr_out & ~z_out).sum()),
            "z_new_after_removal (masking)": int(z2.sum()),
            "sd_all": sd_all, "sd_without_iqr_outliers": sd_clean,
            "sd_inflation_pct": 100 * (sd_all / sd_clean - 1) if sd_clean > 0 else np.nan,
        })
    return pd.DataFrame(rows).set_index("variable")


def spearman_by_city(df, x, y, cities=None):
    """Spearman rho between x and y inside each city (each city's own days)."""
    d = df if cities is None else df[df["city"].isin(cities)]
    out = {}
    for city, g in d.groupby("city", sort=False):
        g = g[[x, y]].dropna()
        out[city] = stats.spearmanr(g[x], g[y]).statistic if g[x].nunique() > 1 else np.nan
    return pd.Series(out, name=f"rho({x}, {y})")


def wilson_ci(k, n, z=1.96):
    """95% Wilson interval for a proportion k/n (works for 0 and n)."""
    if n == 0:
        return (np.nan, np.nan)
    p = k / n
    centre = (p + z * z / (2 * n)) / (1 + z * z / n)
    half = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / (1 + z * z / n)
    return centre - half, centre + half


def rate_by_condition(df, conditions, y):
    """Share of y == 1 on days where each condition holds vs all other days, with the risk ratio."""
    rows = []
    d = df.dropna(subset=[y])
    for name, mask in conditions.items():
        mask = mask.reindex(d.index).fillna(False).astype(bool)
        yes, no = d.loc[mask, y].astype(float), d.loc[~mask, y].astype(float)
        lo, hi = wilson_ci(yes.sum(), len(yes))
        rows.append({"condition": name, "days_with": len(yes), "spike_rate_with_pct": 100 * yes.mean(),
                     "ci95_low_pct": 100 * lo, "ci95_high_pct": 100 * hi,
                     "days_without": len(no), "spike_rate_without_pct": 100 * no.mean(),
                     "risk_ratio": yes.mean() / no.mean() if no.mean() > 0 else np.nan})
    return pd.DataFrame(rows).set_index("condition")


def contingency(df, row, col, row_labels=None, col_labels=None):
    """2x2 table with counts, chi-square test and odds ratio (Haldane +0.5 if a cell is 0)."""
    d = df[[row, col]].dropna().astype(int)
    tab = pd.crosstab(d[row], d[col]).reindex(index=[0, 1], columns=[0, 1], fill_value=0)
    chi2, p, _, _ = stats.chi2_contingency(tab)
    a, b, c, e = tab.loc[1, 1], tab.loc[1, 0], tab.loc[0, 1], tab.loc[0, 0]
    if min(a, b, c, e) == 0:
        a, b, c, e = a + 0.5, b + 0.5, c + 0.5, e + 0.5
    odds = (a * e) / (b * c)
    se = np.sqrt(1 / a + 1 / b + 1 / c + 1 / e)
    tab.index = [(row_labels or {}).get(i, f"{row}={i}") for i in tab.index]
    tab.columns = [(col_labels or {}).get(i, f"{col}={i}") for i in tab.columns]
    return tab, {"chi2": chi2, "p_value": p, "odds_ratio": odds,
                 "or_ci95": (np.exp(np.log(odds) - 1.96 * se), np.exp(np.log(odds) + 1.96 * se))}
