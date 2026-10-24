"""Builds the Milestone 2 report (Sections 1-6) as a JSON content model.

Tables are read from docs/tables/*.csv, which merge_analysis.ipynb writes, so the numbers in
the report are the numbers the notebook printed. render_docx.js turns the JSON into Word, in the
layout of the team's stream reports (Report_Weather.docx).

With --milestone 3 it builds the Milestone 3 report instead: Sections 1-6 as in Milestone 2 (new
title, one abstract sentence, one closing line in Section 4, an updated Section 6) plus Sections
7-12, whose numbers come from the docs/tables/m3_*.csv files that modeling.ipynb writes.

Run from the repository root, after the four notebooks (and modeling.ipynb for Milestone 3):
    python docs/manuscript/build_manuscript.py               # Milestone 2
    node docs/manuscript/render_docx.js
    python docs/manuscript/build_manuscript.py --milestone 3
    node docs/manuscript/render_docx.js 3
"""
import argparse
import json
from pathlib import Path

import pandas as pd

ap = argparse.ArgumentParser()
ap.add_argument("--milestone", type=int, choices=[2, 3], default=2)
M3 = ap.parse_args().milestone == 3

ROOT = Path(__file__).resolve().parents[2]
T = ROOT / "docs" / "tables"
OUT = ROOT / "docs" / "manuscript" / ("manuscript_m3.json" if M3 else "manuscript.json")

blocks = []
counters = {"table": 0, "figure": 0}


def tab(name, **kw):
    return pd.read_csv(T / f"{name}.csv", **kw)


def h1(text):
    blocks.append({"t": "h1", "text": text})


def h2(text):
    blocks.append({"t": "h2", "text": text})


def p(text):
    """Paragraph; **bold** and *italic* are rendered."""
    blocks.append({"t": "p", "text": text})


def bullets(items):
    blocks.append({"t": "bullets", "items": items})


def table(caption, header, rows, widths, note=None, font=8):
    counters["table"] += 1
    blocks.append({"t": "table", "caption": f"**Table {counters['table']}.** {caption}", "header": header,
                   "rows": [[str(c) for c in r] for r in rows], "widths": widths, "note": note, "font": font})
    return counters["table"]


def figure(path, caption, width_in=6.0):
    counters["figure"] += 1
    blocks.append({"t": "figure", "path": str(ROOT / path), "caption": f"**Figure {counters['figure']}.** {caption}",
                   "width_in": width_in})
    return counters["figure"]


def f(x, d=2):
    out = f"{x:,.{d}f}"
    return out[1:] if out.startswith("-") and float(out) == 0 else out    # no "-0.00"


# Tables written by merge_analysis.ipynb
ov = tab("master_overview", index_col=0)["value"]
sp = tab("split_counts", index_col=0)
fs = tab("fire_setting_skew", index_col=0)
s = tab("summary_train", index_col=0)
o = tab("outlier_audit_train", index_col=0)
mo = tab("groupby_month", index_col=0)
cs = tab("contingency_stagnant", index_col=0)
cvr = tab("cone_vs_radius", index_col=[0, 1])
lag = tab("lagged_fire_correlation")
tr = tab("weather_trap_harvest", index_col=0)
xb = tab("cross_border", index_col=0)
w = tab("weight_check_train", index_col=0)
hm = tab("hypothesis_mapping", index_col=0)
HEAD = "Training Oct-Dec (headline)"
up_lag = lag[lag["setting"].str.startswith("Upwind")].set_index("lag_days")["median_rho"]


# =====================================================================
# Milestone 3 content (only with --milestone 3): Sections 7-12 and the small changes to Sections 1-6.
# Every number comes from docs/tables/m3_*.csv, written by modeling.ipynb.
# =====================================================================
def pct(x, d=1):
    return f(100 * x, d)


def ci(est, lo, hi, d=3):
    return f"{f(est, d)} [{f(lo, d)}, {f(hi, d)}]"


if M3:
    sb = tab("m3_split_balance", index_col=0)
    cvf = tab("m3_cv_folds")
    leak = tab("m3_leakage_check").set_index(["model", "scheme"])
    mv = tab("m3_metrics_validation").set_index(["model", "metric"])
    mcv = tab("m3_metrics_cv", index_col=0)
    vcount = tab("m3_validation_counts", index_col=0)
    abl = tab("m3_fire_ablation").set_index(["comparison", "metric"])
    cost = tab("m3_cost", index_col=0)
    curve = tab("m3_cost_curve")
    cwide = curve.pivot(index="ratio", columns="model", values="cost_per_1000")
    onset = tab("m3_errors_onset").set_index(["model", "outcome", "day_type"])["count"]
    ecm = tab("m3_errors_city_month")
    topr = tab("m3_top_errors")
    fnc = tab("m3_fn_context", index_col=0)
    grp = tab("m3_error_rates_group").set_index(["model", "level", "group", "metric"])
    odds = tab("m3_odds_ratios")
    h2t = tab("m3_h2_logit", index_col=0)
    imp = tab("m3_importance")
    mw = tab("m3_label_monthwise").set_index(["label", "model"])
    hz = tab("m3_horizons").set_index(["horizon", "model"])
    enc = tab("m3_aq_encoding").set_index(["encoding", "model"])
    reg = tab("m3_index_regression")
    tun = {"lr": tab("m3_tuning_lr"), "dt": tab("m3_tuning_dt")}

    def V(model, metric, col="estimate"):
        return mv.loc[(model, metric), col]

    def best(fam, s):
        t = tun[fam]
        return t[(t.feature_set == s) & (t["rank"] == 1)].iloc[0]

    def thr(model, ratio=5):
        return curve[(curve.model == model) & (curve.ratio == ratio)]["threshold"].iloc[0]

    def lr_setting(s):
        b = best("lr", s)
        return f"C = {f(b.C, 3)}, {b.penalty}, class weight {b.class_weight}"

    def dt_setting(s):
        b = best("dt", s)
        return f"depth {int(b.max_depth)}, min. leaf {int(b.min_samples_leaf)}, class weight {b.class_weight}"

    BE = min(r for r in cwide.index if cwide.loc[r, "LR full"] < cwide.loc[r, "Persistence"])   # break-even ratio
    BE_DT = min(r for r in cwide.index if cwide.loc[r, "DT full"] < cwide.loc[r, "Persistence"])
    nz = odds[(odds.feature_set == "full") & (odds.coef != 0)].set_index("feature")
    n_full = int((odds.feature_set == "full").sum())
    tr_, va_ = sb.loc["train"], sb.loc["validation"]

    M3_ABSTRACT = (
        " Milestone 3 adds baseline forecasts of a spike on the next day, scored with purged, week-grouped cross-validation and on an "
        f"out-of-time validation season (September–December 2023): a sparse logistic regression on today's index margin over the city threshold "
        f"and the mean temperature ranks spikes as well as persistence (PR-AUC {f(V('LR full', 'pr_auc'), 3)} against {f(V('Persistence', 'pr_auc'), 3)}) "
        f"and gives cheaper alerts whenever a missed spike is weighted at least {BE} times a false alarm "
        f"({f(V('LR full', 'cost_per_1000'), 1)} against {f(V('Persistence', 'cost_per_1000'), 1)} per 1,000 city-days at 5:1), "
        "while upwind fires add no next-day skill once today's smog is known.")
    M3_SECTION4_CLOSE = (
        "**Status after Milestone 3.** Sections 7–12 answer two of the five hypotheses. H2 (weather trap) is supported on every component (Section 11.1). "
        "H5 (forecast value) is answered for the next day: the models match persistence in ranking and beat it on alert cost, and fires add no skill "
        "(Sections 9 and 10). H1, H3 and H4 are tested in Milestone 4.")


def m3_reproducibility():
    p("**Milestone 3.** modeling.ipynb (sections M3.1–M3.10) reads only the master table and role2_params.json and runs top to bottom in about five minutes "
      "on 8 cores. It writes every table of Sections 7–12 to docs/tables/m3_*.csv, the figures to figures/fig_m3_*.png, the tuned hyperparameters and "
      "alert thresholds to Dataset/clean/m3_params.json, and the ten fitted pipelines to models/*.joblib. The modelling code sits in two modules: "
      "src/modeling.py (data access, feature sets, the purged cross-validation splitter, pipelines, tuning and thresholds) and src/evaluate.py (metrics, "
      "week-block bootstrap, cost curve, error breakdown). All seeds are fixed, and two consecutive runs write byte-identical tables. "
      "The decision log (DECISIONS.md, rows S1–S19) records every Milestone 3 choice with its row counts.")


def m3_sections():
    lrf, dtf, pers = "LR full", "DT full", "Persistence"
    # =================================================================
    # 7. Baseline models
    # =================================================================
    h1("7. Baseline Models and Justification")
    p(f"The headline task is a binary forecast: will city *c* have a smog spike on day *t* + 1, given what is known on day *t*? Spikes are "
      f"{f(tr_['spike rate (%)'], 2)}% of training city-days, so the models are judged on how well they find the rare positive days and on what their "
      "errors cost. Four models, from the simplest to the most flexible, set the benchmarks (Table 13).")
    table("Baseline models, their role, why they suit this problem, and the setting chosen by cross-validated PR-AUC (full feature set).",
          ["Model", "Role", "Why for this problem", "Tuned setting (CV PR-AUC)"],
          [["Majority class", "Floor", "Always predicts \"no spike\". Shows how misleading accuracy is when about 95% of days are clean.", "–"],
           ["Persistence", "Benchmark", "Tomorrow repeats today. Today's index has ρ = 0.82 with tomorrow's (Section 3.3), so any forecast must beat this rule. "
            "Its ranking score is today's margin over the city's spike threshold.", f"Fixed rule ({f(mcv.loc[pers, 'pr_auc_mean'], 3)})"],
           ["Logistic regression (LR)", "Main baseline", "Additive and interpretable: odds ratios a health department can read, and probabilities that can be "
            "thresholded for any cost ratio. L1/L2 regularisation copes with correlated weather columns.",
            f"{lr_setting('full')} ({f(best('lr', 'full').cv_pr_auc_mean, 3)})"],
           ["Decision tree (DT)", "Non-linear baseline", "Finds interactions (for example stagnant **and** humid) without specifying them, and can be drawn as a "
            "flow chart for officials.", f"{dt_setting('full')} ({f(best('dt', 'full').cv_pr_auc_mean, 3)})"]],
          [1500, 1100, 4700, 2492])
    p("K-nearest neighbours was not used: distances on a mix of binary dummies and continuous weather columns are hard to justify, and it gives no "
      "readable drivers. Random forests and gradient boosting are left for Milestone 4, so that the baselines stay interpretable. "
      "**Feature sets.** LR and DT are each fitted on three sets. **Full** (42 columns) holds AQ history (today and lags 1–2), upwind fire counts (±45° cone, "
      "300 km, day *t* and lags 1–3), weather (stagnant today and yesterday, humidity, rain day, temperature range, vector-mean wind, mean temperature, "
      "7 wind sectors), and 11 month and 10 city dummies. **Weather-only** (35) drops AQ history and fire. **No-fire** (38) drops only the four fire "
      "columns and is the ablation that tests the project's central claim. The calm sector is identical to the stagnant flag (631 of 631 days), so the "
      "most frequent sector, north-west, is the wind reference instead.")
    p("**AQ history as a margin over the city threshold.** The spike label is defined relative to each city's threshold, which runs from 0.36 (Rahim Yar Khan) "
      "to 2.18 (Lahore). AQ history therefore enters as today's (and the two previous days') index **minus the city threshold**, so that a margin of 0 or "
      "more means the day is a spike. With the raw pooled index, the city dummies had to act as threshold corrections and produced meaningless odds "
      f"ratios (up to {f(enc.loc[('raw index (Phase 3)', lrf), 'lr_max_city_or'], 0)} for Rahim Yar Khan against Lahore). The margin encoding was "
      "fixed as the headline before any result was seen; the raw-index version is kept as a sensitivity run (Section 9.3). The thresholds were "
      "learned on training days in Milestone 2, so the margin adds no information beyond the label itself.")

    # =================================================================
    # 8. Experimental setup
    # =================================================================
    h1("8. Experimental Setup")
    h2("8.1 Split and class balance")
    p(f"The outer split is chronological, as in Milestone 2: training runs from {tr_['first day']} to {tr_['last day']} "
      f"({int(tr_['city-days']):,} city-days, {f(tr_['share of rows (%)'], 1)}%), then a 3-day gap, then validation from {va_['first day']} to "
      f"{va_['last day']} ({int(va_['city-days']):,} city-days, {f(va_['share of rows (%)'], 1)}%). Rows whose feature day or target day is one of the "
      f"flagged suspect days ({int(tr_['suspect rows dropped'])} training rows), and rows without a target or an index lag, are dropped. Training "
      f"then has {int(tr_['spikes'])} spikes ({f(tr_['spike rate (%)'], 2)}%) and validation {int(va_['spikes'])} ({f(va_['spike rate (%)'], 2)}%). "
      "Validation is the out-of-time test: nothing is fitted, tuned or thresholded on it. Its spike rate is higher because it covers only September "
      "to December and ends in the peak month, while training covers a whole year including the spike-free summer. Stratification is therefore "
      "checked rather than forced on the outer split, and applied inside the cross-validation (Section 8.3).")
    h2("8.2 Why not a random stratified split?")
    a, b, c_, d_ = [k for k in leak.loc[lrf].index if not k.startswith("reference")]
    ref = [k for k in leak.loc[lrf].index if k.startswith("reference")][0]

    def lk(m, k, col):
        r = leak.loc[(m, k)]
        sd = r[f"{col}_sd"]
        return f(r[f"{col}_mean"], 3) + ("" if pd.isna(sd) else f" ± {f(sd, 3)}")
    p("Neighbouring days are near-copies (ρ = 0.82), Islamabad and Rawalpindi share one series, and all cities share the same weather on the same day. "
      "A random split puts near-duplicates of every test row into the training part. Table 14 measures the effect on the training rows: the same "
      "tuned pipelines are scored under a random stratified 80/20 split, plain stratified 5-fold CV, week-grouped 5-fold CV and our purged design.")
    table("Leakage check on training rows: the same tuned pipelines scored under four splitting schemes (mean ± SD over folds). The last row is the "
          "chronological validation score, for reference.",
          ["Splitting scheme", "Folds", "LR full PR-AUC", "LR full ROC-AUC", "DT full PR-AUC", "DT full ROC-AUC"],
          [[k[4:] if not k.startswith("reference") else "Chronological validation (Sep–Dec 2023)", int(leak.loc[(lrf, k), "n_folds"]),
            lk(lrf, k, "pr_auc"), lk(lrf, k, "roc_auc"), lk(dtf, k, "pr_auc"), lk(dtf, k, "roc_auc")] for k in [a, b, c_, d_, ref]],
          [3300, 700, 1450, 1450, 1450, 1442])
    infl_lr = leak.loc[(lrf, a), "pr_auc_mean"] - leak.loc[(lrf, d_), "pr_auc_mean"]
    infl_dt = leak.loc[(dtf, a), "pr_auc_mean"] - leak.loc[(dtf, d_), "pr_auc_mean"]
    p(f"A random stratified split overstates PR-AUC by {f(infl_lr, 3)} for the LR and {f(infl_dt, 3)} for the tree, and plain stratified K-fold by "
      f"{f(leak.loc[(lrf, b), 'pr_auc_mean'] - leak.loc[(lrf, d_), 'pr_auc_mean'], 3)} and "
      f"{f(leak.loc[(dtf, b), 'pr_auc_mean'] - leak.loc[(dtf, d_), 'pr_auc_mean'], 3)}. Grouping by week does most of the correction; the purge and "
      f"embargo remove a further {f(leak.loc[(dtf, c_), 'pr_auc_mean'] - leak.loc[(dtf, d_), 'pr_auc_mean'], 3)} for the tree. ROC-AUC, dominated "
      "by the many easy clean days, barely moves. Validation sits above our CV because December 2023 was unusually persistent (persistence: "
      f"{f(V(pers, 'pr_auc'), 3)} against {f(mcv.loc[pers, 'pr_auc_mean'], 3)} in CV), so the inflation is judged against grouped CV on the same rows.")
    h2("8.3 Purged, grouped cross-validation")
    p(f"Tuning, thresholds and CV scores use **purged, repeated StratifiedGroupKFold** on the training rows: 5 folds × 5 repeats (seeds 0–4) = "
      f"{len(cvf)} folds (Roberts et al., 2017). The **group** is the calendar week shared by all 11 cities, so a week is never split between fitting "
      "and scoring. **Stratification** on the spike label gives every fold its share of spikes. The **purge** drops fit rows whose target day falls "
      "on a held-out day. The **embargo** drops fit rows up to three days after a held-out day, because their AQ history (back to *t* − 2) contains "
      f"that day's index. Each fold holds out {int(cvf['test weeks'].min())}–{int(cvf['test weeks'].max())} weeks "
      f"({int(cvf['test rows'].min())}–{int(cvf['test rows'].max())} rows), and the purge and embargo remove "
      f"{int(cvf['purged/embargoed rows'].min())}–{int(cvf['purged/embargoed rows'].max())} fit rows. The test-fold spike rate averages "
      f"{f(cvf['test spike rate (%)'].mean(), 2)}% (SD {f(cvf['test spike rate (%)'].std(), 2)}, range {f(cvf['test spike rate (%)'].min(), 2)}–"
      f"{f(cvf['test spike rate (%)'].max(), 2)}%), against {f(tr_['spike rate (%)'], 2)}% overall (Figure 7).")
    figure("figures/fig_m3_1_cv_folds.png",
           "Purged, grouped 5 × 5 cross-validation inside the training period. (A) Fold layout of the first repeat over the training calendar: fit part, "
           "rows removed by the purge and embargo, held-out weeks, and dropped days. (B) Spike rate of each of the 25 test folds against the rate over all "
           "training rows. Produced by modeling.ipynb (Figure M3.1).", 5.6)
    h2("8.4 Tuning, thresholds and leakage guards")
    lr_t = tun["lr"]
    lr_full_c = lr_t[(lr_t.feature_set == "full")].groupby("C", as_index=False)["cv_pr_auc_mean"].max()   # best setting at each C
    p("Hyperparameters are chosen by grid search on the 25 purged folds, scored by **PR-AUC** (average precision), which is more informative than ROC-AUC "
      "when positives are rare (Saito & Rehmsmeier, 2015). The LR grid has C from 0.001 to 100 (8 log-spaced values), L1 or L2, and class weights "
      "none or balanced (32 settings). The tree grid has depth 2–8, minimum leaf size 10/25/50/100 and the same class weights (56 settings). "
      f"The LR curve is flat between C = 0.005 and 0.14 (best CV PR-AUC {f(lr_full_c[(lr_full_c.C > 0.004) & (lr_full_c.C < 0.15)].cv_pr_auc_mean.min(), 3)}–"
      f"{f(lr_full_c.cv_pr_auc_mean.max(), 3)}) and falls as the penalty weakens ({f(lr_full_c[lr_full_c.C == lr_full_c.C.max()].cv_pr_auc_mean.max(), 3)} "
      "at C = 100), so the optimum lies inside the grid. The tree peaks at depth 4 (Figure 8). The best setting is refitted on all training rows.")
    figure("figures/fig_m3_2_tuning.png",
           "Hyperparameter tuning on the purged training folds: mean cross-validated PR-AUC (band ± 1 SD over 25 folds) against (A) the LR inverse "
           "regularisation strength C and (B) the tree depth, for the three feature sets; at each value the best setting of the other hyperparameters is "
           "shown. Produced by modeling.ipynb (Figure M3.2).", 4.8)
    p(f"**Alert thresholds.** Each model's threshold minimises 5·FN + 1·FP on its out-of-fold training predictions (Section 10), and all thresholds are "
      f"fixed before any validation metric is computed: alert when the spike probability is at least {pct(thr(lrf))}% (LR full) or {pct(thr(dtf))}% "
      "(DT full). **Leakage guards.** Every transform (log1p of fire counts, standard scaling) sits inside the pipeline and is re-learned in each fold; "
      "an assertion before every fit checks that only training rows reach it; the loader refuses any 2024 date; and fold groups are asserted disjoint. "
      "The LR uses the liblinear solver, because saga failed to converge within 5,000 iterations at weak penalties; liblinear gives the same fold "
      "scores within 0.005 in under 0.2 s per fit. All models use scikit-learn (Pedregosa et al., 2011).")

    # =================================================================
    # 9. Results
    # =================================================================
    h1("9. Results")
    h2("9.1 Classification metrics")
    order = ["Majority class", pers, lrf, "LR no-fire", "LR weather-only", dtf, "DT no-fire", "DT weather-only"]

    def cell(m, k, d=3):
        v = V(m, k)
        return "–" if pd.isna(v) else f(v, d)
    rows = [[m, cell(m, "accuracy"), cell(m, "precision"), cell(m, "recall"), cell(m, "specificity"), cell(m, "f1"), cell(m, "roc_auc"),
             "–" if pd.isna(V(m, "pr_auc")) else ci(V(m, "pr_auc"), V(m, "pr_auc", "ci_low"), V(m, "pr_auc", "ci_high")),
             f(V(m, "cost_per_1000"), 1)] for m in order]
    table(f"Validation metrics (Sep–Dec 2023, {int(va_['city-days']):,} city-days, {int(va_['spikes'])} spikes) at each model's 5:1 threshold. "
          f"PR-AUC with a 95% CI from a block bootstrap over the {int(mv['n_weeks'].iloc[0])} validation weeks (1,000 resamples). Cost = (5·FN + FP) "
          "per 1,000 city-days.",
          ["Model", "Accuracy", "Precision", "Recall", "Specificity", "F1", "ROC-AUC", "PR-AUC [95% CI]", "Cost"], rows,
          [1650, 900, 900, 800, 1000, 700, 900, 1700, 700], font=7)
    tp = lambda m, k: int(vcount.loc[m, k])
    p(f"**Accuracy misleads.** The majority class scores {pct(V('Majority class', 'accuracy'))}% accuracy, more than LR full "
      f"({pct(V(lrf, 'accuracy'))}%), yet catches no spike and has the highest cost. **Ranking.** LR full ranks spikes at least as well as persistence "
      f"(PR-AUC {f(V(lrf, 'pr_auc'), 3)} against {f(V(pers, 'pr_auc'), 3)}; ROC-AUC {f(V(lrf, 'roc_auc'), 3)} against {f(V(pers, 'roc_auc'), 3)}), "
      f"and the tree is behind ({f(V(dtf, 'pr_auc'), 3)}). **The alert decision.** At 5:1, LR full catches {tp(lrf, 'tp')} of {int(va_['spikes'])} spikes "
      f"(recall {pct(V(lrf, 'recall'))}%) against {tp(pers, 'tp')} for persistence ({pct(V(pers, 'recall'))}%), at lower precision "
      f"({pct(V(lrf, 'precision'))}% vs {pct(V(pers, 'precision'))}%). DT full has the lowest cost ({f(V(dtf, 'cost_per_1000'), 1)} per 1,000 city-days). "
      f"Cross-validation agrees: PR-AUC {f(mcv.loc[pers, 'pr_auc_mean'], 3)} ± {f(mcv.loc[pers, 'pr_auc_sd'], 3)} for persistence, "
      f"{f(mcv.loc[lrf, 'pr_auc_mean'], 3)} ± {f(mcv.loc[lrf, 'pr_auc_sd'], 3)} for LR full and {f(mcv.loc[dtf, 'pr_auc_mean'], 3)} ± "
      f"{f(mcv.loc[dtf, 'pr_auc_sd'], 3)} for DT full; cost {f(mcv.loc[pers, 'cost_per_1000_mean'], 1)}, {f(mcv.loc[lrf, 'cost_per_1000_mean'], 1)} and "
      f"{f(mcv.loc[dtf, 'cost_per_1000_mean'], 1)}. Without AQ history the models lose most of their skill (LR weather-only PR-AUC "
      f"{f(V('LR weather-only', 'pr_auc'), 3)}). With 18 validation weeks and most spikes in December, every CI is wide.")
    figure("figures/fig_m3_3_roc_pr.png",
           "Validation ROC curves (A) and precision-recall curves (B) for persistence and the six tuned models; markers show the operating points at the "
           "5:1 thresholds. Colour = feature set, solid = LR, dashed = DT, black = persistence. Produced by modeling.ipynb (Figure M3.3).", 5.2)

    h2("9.2 Do upwind fires add skill?")

    def ab(comp, k="pr_auc"):
        r = abl.loc[(comp, k)]
        return r
    comps = [("LR full − LR no-fire", "Fire, LR"), ("DT full − DT no-fire", "Fire, DT"), ("LR no-fire − LR weather-only", "AQ history, LR"),
             ("LR full − Persistence", "LR full vs persistence"), ("DT full − Persistence", "DT full vs persistence")]
    table("Paired comparisons on validation (difference with 95% week-block bootstrap CI) and in the 25 CV folds (mean difference; folds where the "
          "first model is better).",
          ["Comparison", "Question", "ΔPR-AUC, validation", "ΔROC-AUC, validation", "ΔPR-AUC, CV mean", "CV folds better"],
          [[c.replace("Persistence", "persistence"), q, ci(ab(c).validation_diff, ab(c).ci_low, ab(c).ci_high),
            ci(ab(c, "roc_auc").validation_diff, ab(c, "roc_auc").ci_low, ab(c, "roc_auc").ci_high, 4),
            f(ab(c).cv_diff_mean, 4), f"{int(ab(c).cv_folds_a_better)} of 25"] for c, q in comps],
          [2300, 1500, 1800, 1900, 1200, 1092])
    p("**Fires add no next-day skill once today's smog is known.** The L1 penalty of the tuned LR sets all four fire coefficients to zero, so LR full and "
      f"LR no-fire give identical validation predictions; across the CV refits the full model is better in only {int(ab('LR full − LR no-fire').cv_folds_a_better)} "
      f"of 25 folds. The tree shows the same null (ΔPR-AUC {f(ab('DT full − DT no-fire').validation_diff, 3)}). AQ history is what matters "
      f"(ΔPR-AUC {f(ab('LR no-fire − LR weather-only').validation_diff, 3)}, better in all 25 folds). Against persistence, LR full gains a little: "
      f"ΔPR-AUC {f(ab('LR full − Persistence').validation_diff, 3)} with a CI that includes 0, but ΔROC-AUC "
      f"{f(ab('LR full − Persistence', 'roc_auc').validation_diff, 4)} with a CI above 0, and better in {int(ab('LR full − Persistence').cv_folds_a_better)} "
      "of 25 folds. This does not show that fires do not cause smog: Milestone 2 found that cone fires track next-day smog (ρ ≈ 0.23), but whatever "
      "smoke they add is already in today's index, the strongest input.")

    h2("9.3 Sensitivity checks")
    mwl = "month-wise P90"
    rr = reg.set_index(["kind", "name", "metric"])
    raw_lr = enc.loc[("raw index (Phase 3)", lrf)]
    raw_dt, mar_dt = enc.loc[("raw index (Phase 3)", dtf)], enc.loc[("threshold margin (headline)", dtf)]
    sens = [["Month-wise spike label (city × month P90)", "PR-AUC, validation (CV)",
             *[f"{f(mw.loc[(mwl, m), 'val_pr_auc'], 3)} ({f(mw.loc[(mwl, m), 'cv_pr_auc_mean'], 3)})" for m in [pers, lrf, "LR no-fire", dtf]]]]
    for h in (2, 3):
        sens.append([f"Horizon *t* + {h}, h1 hyperparameters", "PR-AUC, validation (CV)",
                     *[f"{f(hz.loc[(h, m), 'val_pr_auc'], 3)} ({f(hz.loc[(h, m), 'cv_pr_auc_mean'], 3)})" for m in [pers, lrf, "LR no-fire", dtf]]])
    sens.append(["Raw index instead of the margin (retuned)", "PR-AUC, validation (CV)", f(V(pers, "pr_auc"), 3),
                 f"{f(raw_lr.val_pr_auc, 3)} ({f(raw_lr.cv_pr_auc, 3)})", "–", f"{f(raw_dt.val_pr_auc, 3)} ({f(raw_dt.cv_pr_auc, 3)})"])
    sens.append(["Continuous index, Ridge regression", "MAE, validation (CV)",
                 *[f"{f(rr.loc[('model', n, 'mae'), 'validation'], 3)} ({f(rr.loc[('model', n, 'mae'), 'cv_mean'], 3)})"
                   for n in ["Persistence (index)", "Ridge full", "Ridge no-fire"]], "–"])
    table("Sensitivity runs. Columns give persistence and the full, no-fire and tree models (for the index regression: Ridge with the full and no-fire "
          "sets). For PR-AUC higher is better, for MAE lower.",
          ["Run", "Metric", "Persistence", "LR (Ridge) full", "LR (Ridge) no-fire", "DT full"], sens, [2900, 1500, 1350, 1400, 1450, 1192])
    d_fire = rr.loc[("difference", "Ridge full − Ridge no-fire", "mae")]
    d_pers = rr.loc[("difference", "Ridge full − Persistence (index)", "mae")]
    bullets([
        "**Month-wise label** (about 10% spikes in every month, so October–November fire episodes count as much as December fog): persistence "
        f"still leads, and fire adds nothing robust (full − no-fire {f(mw.loc[(mwl, lrf), 'cv_pr_auc_mean'] - mw.loc[(mwl, 'LR no-fire'), 'cv_pr_auc_mean'], 3)} "
        f"in CV). Autumn 2023 was cleaner than 2022: only {pct(mw.loc[(mwl, pers), 'val_spike_rate'])}% of validation days pass the 2022 thresholds.",
        "**Horizons:** skill fades from *t* + 1 to *t* + 3; LR stays slightly ahead of persistence in validation and CV, and fire never helps.",
        f"**Raw-index encoding:** worse for both models, above all the tree ({f(raw_dt.val_pr_auc, 3)} against {f(mar_dt.val_pr_auc, 3)}), which "
        "with the margin needs one split where it needed many city × index splits.",
        f"**Continuous index:** Ridge full is not better than persistence on validation (ΔMAE {f(d_pers.validation, 3)} [{f(d_pers.ci_low, 3)}, "
        f"{f(d_pers.ci_high, 3)}]; better in {int(d_pers.cv_folds_a_better)} of 25 CV folds), and fire adds nothing on this more sensitive target "
        f"(ΔMAE {f(d_fire.validation, 4)} [{f(d_fire.ci_low, 4)}, {f(d_fire.ci_high, 4)}]). For H5 the null (ΔMAE ≥ 0) is not rejected for the index."])

    # =================================================================
    # 10. Asymmetric error cost
    # =================================================================
    h1("10. Asymmetric Error Cost Analysis")
    h2("10.1 What each error costs, and to whom")
    table("The two errors of a next-day smog alert.",
          ["Error", "Who bears it", "Consequence", "Reversible?"],
          [["False negative: a spike day without an alert", "Children, the elderly, asthma and heart patients, outdoor and daily-wage workers, hospitals",
            "Unprotected exposure at PM2.5 levels several times the WHO guideline (WHO, 2021); respiratory and cardiac admissions; school days lost to illness",
            "No: the exposure has happened"],
           ["False positive: an alert on a normal day", "Schools, brick kilns, transport, traders and daily-wage workers",
            "A needless school closure or activity restriction, lost income, and alert fatigue that weakens trust in the next real warning",
            "Mostly: one day of disruption"]],
          [2000, 2600, 3700, 1492])
    p("We weight a missed spike as **five** false alarms (FN:FP = 5:1). This ratio is a **stated policy assumption, not an estimate**: we found no verified "
      "study that prices one missed smog day against one unnecessary advisory day in Punjab. The health side is large: in India in 2019, air pollution was "
      "linked to 1.67 million deaths (17.8% of all deaths) and to lost output of US$36.8 billion, 1.36% of GDP (Pandey et al., 2021). Because the ratio "
      "is uncertain, the robust result is the **break-even ratio**, the smallest ratio at which a model alert is cheaper than persistence, read from a "
      "cost curve over every ratio from 1 to 20. At each ratio the threshold is re-chosen on the out-of-fold training predictions, never on validation.")
    h2("10.2 Expected cost and the break-even ratio")
    cost_rows = []
    for m in ["Majority class (= never alert)", pers, lrf, dtf, "LR weather-only", "Always alert"]:
        r = cost.loc[m]
        n_beat = r["ratios_beating_persistence"]
        cost_rows.append([m, int(r.fn), int(r.fp), f(r.cost_per_1000_at_5to1, 1), f(r.saving_vs_never_alert_pct, 1),
                          "–" if pd.isna(n_beat) or m == pers else f"{int(n_beat)} of 20"])
    table("Validation error cost at 5:1 (per 1,000 city-days) and the number of cost ratios (1 to 20) at which the model is cheaper than persistence.",
          ["Policy", "Missed spikes (FN)", "False alarms (FP)", "Cost at 5:1", "Saving vs never alert (%)", "Ratios cheaper than persistence"],
          cost_rows, [2600, 1300, 1300, 1200, 1700, 1692])
    p(f"At 5:1, never alerting costs {f(cost.loc['Majority class (= never alert)', 'cost_per_1000_at_5to1'], 1)} per 1,000 city-days; persistence "
      f"cuts this to {f(cost.loc[pers, 'cost_per_1000_at_5to1'], 1)}, LR full to {f(cost.loc[lrf, 'cost_per_1000_at_5to1'], 1)} and DT full to "
      f"{f(cost.loc[dtf, 'cost_per_1000_at_5to1'], 1)}. **The break-even ratio is {BE}:1** for LR full and {BE_DT}:1 for DT full (Figure 10): persistence "
      f"is cheaper only when a missed spike costs less than {BE} false alarms, and the gap widens with the ratio (at 20:1, "
      f"{f(cwide.loc[20, lrf], 1)} for LR full against {f(cwide.loc[20, pers], 1)} for persistence). A health department only has to judge a missed "
      f"smog day at least {BE} times as costly as an unnecessary advisory for a model alert to beat \"tomorrow = today\". The price is more false alarms: "
      f"{pct(1 - V(lrf, 'specificity'))}% of clean days for LR full and {pct(1 - V(dtf, 'specificity'))}% for DT full, against "
      f"{pct(1 - V(pers, 'specificity'))}% for persistence.")
    figure("figures/fig_m3_4_cost_curve.png",
           "Expected validation cost per 1,000 city-days against the FN:FP cost ratio; thresholds re-chosen on out-of-fold training predictions at each "
           "ratio. Grey lines: never alert (= majority class) and always alert; dashed vertical line: the 5:1 headline. Produced by modeling.ipynb "
           "(Figure M3.4).", 3.9)
    h2("10.3 Confusion matrices and edge cases")
    figure("figures/fig_m3_5_confusion.png",
           "Validation confusion matrices at the 5:1 threshold for persistence, LR full and DT full (counts and shares of all city-days; colour on a log "
           "scale). Produced by modeling.ipynb (Figure M3.5).", 5.0)
    o_ = lambda m, k, t: int(onset.loc[(m, k, t)])
    on_total = o_(pers, "FN", "onset")
    lr_err = ecm[ecm.model == lrf]
    by_city = lr_err.groupby("city")[["fn", "fp"]].sum()
    by_month = lr_err.groupby("month")[["spikes", "fn", "fp"]].sum()
    fp_city = by_city.fp.sort_values(ascending=False)
    fn_ = topr[topr.kind.str.startswith("FN")]
    fp_ = topr[topr.kind.str.startswith("FP")]
    p(f"**Onsets are where a model adds value.** On an onset day (tomorrow a spike, today not) persistence fails by construction: it misses all {on_total} "
      f"onsets. LR full catches {o_(lrf, 'TP', 'onset')} of {on_total} ({pct(o_(lrf, 'TP', 'onset') / on_total)}%) and DT full "
      f"{o_(dtf, 'TP', 'onset')}; both catch all {o_(lrf, 'TP', 'continuation')} continuation days. **When and where.** All validation spikes fall in "
      f"November ({int(by_month.loc['2023-11', 'spikes'])}) and December ({int(by_month.loc['2023-12', 'spikes'])}). LR's {int(by_city.fn.sum())} "
      f"misses are spread out (no city above {int(by_city.fn.max())}). Its {int(by_city.fp.sum())} false alarms fall on onset-type days "
      f"({o_(lrf, 'FP', 'onset')}) and on episode ends ({o_(lrf, 'FP', 'continuation')}), and concentrate in "
      + ", ".join(f"{c} ({int(v)})" for c, v in fp_city.head(4).items()) + ".")
    p(f"**Edge cases.** The ten worst misses are all onset days, mostly in December (for example {fn_.iloc[0].city}, {fn_.iloc[0].date}), with LR "
      f"probabilities of at most {f(fn_.lr_full_probability.max(), 3)} against a threshold of {f(thr(lrf), 3)}. On the feature day of the missed spikes, "
      f"today's index sat {f(-fnc.loc['FN', 'today_margin'], 2)} units below the city threshold (caught spikes: {f(fnc.loc['TP', 'today_margin'], 2)} "
      f"above), fewer days were stagnant ({pct(fnc.loc['FN', 'stagnant'])}% vs {pct(fnc.loc['TP', 'stagnant'])}%), humidity was lower "
      f"({f(fnc.loc['FN', 'rh_mean_pct'], 1)}% vs {f(fnc.loc['TP', 'rh_mean_pct'], 1)}%), and upwind fires were *higher* "
      f"({f(fnc.loc['FN', 'fire_cnt_up45_r300_all'], 1)} vs {f(fnc.loc['TP', 'fire_cnt_up45_r300_all'], 1)} detections): sudden jumps that today's "
      f"conditions do not announce. The most confident false alarms are episode ends where the next-day index stays high but just below the "
      f"threshold (for example {fp_.iloc[0].city}, {fp_.iloc[0].date}: next-day index {f(fp_.iloc[0].target_index_h1, 2)}).")
    h2("10.4 Preliminary disparity check: Pakistan and India")

    def gr(m, level, g, k, d=3):
        r = grp.loc[(m, level, g, k)]
        return ci(r.estimate, r.ci_low, r.ci_high, d) if k != "spikes" and k != "alerts" else str(int(r.estimate))
    grows = []
    for m in [pers, lrf]:
        for g in ["Pakistan (7 cities)", "India (4 cities)"]:
            grows.append([m, g, gr(m, "country", g, "spikes"), gr(m, "country", g, "alerts"), gr(m, "country", g, "recall"),
                          gr(m, "country", g, "fpr"), gr(m, "country", g, "precision")])
        grows.append([m, "Gap PK − IN", "–", "–", gr(m, "country gap", "PK − IN", "recall"), gr(m, "country gap", "PK − IN", "fpr"),
                      gr(m, "country gap", "PK − IN", "precision")])
    table("Validation error rates by country at the 5:1 threshold, with 95% week-block bootstrap CIs. FPR = share of clean days with a false alarm.",
          ["Model", "Group", "Spikes", "Alerts", "Recall", "FPR", "Precision"], grows, [1300, 1700, 700, 700, 1800, 1800, 1792], font=7)
    cg = lambda g, k: grp.loc[(lrf, "city", g, k), "estimate"]
    cities = sorted({k[2] for k in grp.index if k[0] == lrf and k[1] == "city"}, key=lambda c: -cg(c, "fpr"))
    p("The brief asks about potential bias. Our groups are countries and cities, not people, so this is a first check of whether the alert serves "
      f"both sides of the border equally. LR full warns of {pct(grp.loc[(lrf, 'country', 'Pakistan (7 cities)', 'recall'), 'estimate'])}% of "
      f"Pakistani and {pct(grp.loc[(lrf, 'country', 'India (4 cities)', 'recall'), 'estimate'])}% of Indian spikes, with false-alarm rates of "
      f"{pct(grp.loc[(lrf, 'country', 'Pakistan (7 cities)', 'fpr'), 'estimate'])}% and {pct(grp.loc[(lrf, 'country', 'India (4 cities)', 'fpr'), 'estimate'])}%; "
      "every country gap has a CI that includes 0. Between cities the burden is uneven: false alarms hit "
      + ", ".join(f"{c} ({pct(cg(c, 'fpr'), 0)}%)" for c in cities[:4])
      + f" of clean days, against {pct(cg('Islamabad', 'fpr'), 0)}% in Islamabad and Rawalpindi and {pct(cg('Lahore', 'fpr'), 0)}% in Lahore. "
      "These rates rest on 0 to "
      f"{int(max(cg(c, 'spikes') for c in cities))} spikes per city and are descriptive; the full fairness audit is planned for Milestone 4.")

    # =================================================================
    # 11. Drivers and policy
    # =================================================================
    h1("11. Drivers and Initial Policy Takeaways")
    h2("11.1 The weather trap (H2)")
    h2_rows = []
    names = {"stagnant": "Stagnant air (vector wind < 2 km/h), 0 → 1", "rh_mean_pct_sd": "Relative humidity, per 1 SD",
             "temp_range_c_sd": "Temperature range, per 1 SD", "temp_mean_c_sd": "Mean temperature, per 1 SD (control)"}
    for t, lab in names.items():
        r = h2t.loc[t]
        h2_rows.append([lab, f(r.odds_ratio, 2), f"{f(r.or_ci_low_city, 2)}–{f(r.or_ci_high_city, 2)}",
                        "< 0.001" if r.p_one_sided_city < 0.001 else f(r.p_one_sided_city, 3),
                        f"{f(r.or_ci_low_week, 2)}–{f(r.or_ci_high_week, 2)}"])
    rain = h2t.loc[[i for i in h2t.index if i.startswith("rain_day")][0]]
    h2_rows.append(["Rain day (Fisher exact test, all training rows)", "0", "–",
                    "< 0.0001" if rain.p_one_sided_city < 0.0001 else f(rain.p_one_sided_city, 4), "–"])
    table(f"H2 weather-trap test: Logit of a spike tomorrow on rain-free training days in September–February (n = {int(h2t.n.iloc[0]):,}, "
          f"{int(h2t.spikes.iloc[0])} spikes, pseudo R² {f(h2t.pseudo_r2.iloc[0], 2)}), controlling for mean temperature, month and city; standard errors "
          f"clustered by city ({int(h2t.clusters_city.iloc[0])} clusters), with a week-clustered check (statsmodels; Seabold & Perktold, 2010). "
          f"Rain: {rain.note}.",
          ["Term", "Odds ratio", "95% CI (city)", "One-sided p", "95% CI (week)"], h2_rows, [3800, 1100, 1500, 1500, 1892])
    p("**H2 is supported on every component.** Stagnant air, humidity and a large day–night temperature range each raise the odds of a spike the next "
      "day, and no training rain day was followed by a spike. Two features of the data shaped the test: rain and the months March to August have no "
      "spikes at all, so an unpenalised Logit has no finite estimate for them. Rain is therefore tested exactly, and the Logit uses rain-free days of "
      "the months that have spikes. With 11 city clusters (10 independent air-quality series) the clustered errors are approximate; the week-clustered "
      "version gives the same conclusions.")
    h2("11.2 What drives the forecast")
    pi_ = imp[imp.method.str.startswith("permutation")].set_index(["model", "group"])["mean"]
    gini = imp[imp.method.str.startswith("Gini")].set_index("group")["mean"]
    wo = odds[odds.feature_set == "weather_only"].set_index("feature")
    p(f"**The forecast rests on today's margin, with temperature second.** The L1 penalty of LR full keeps only {len(nz)} of its {n_full} columns: today's "
      f"margin over the city threshold (odds ratio {f(nz.loc['persist_margin', 'odds_ratio'], 1)} per SD) and the mean temperature "
      f"({f(nz.loc['temp_mean_c', 'odds_ratio'], 2)} per SD: colder days raise the risk). Shuffling AQ history costs "
      f"{f(pi_.loc[(lrf, 'AQ history (today, lags 1–2)')], 3)} of validation PR-AUC, and shuffling mean temperature "
      f"{f(pi_.loc[(lrf, 'Mean temperature')], 3)}; every other group costs nothing (Figure {counters['figure'] + 1}). The tree agrees: its Gini importance is "
      f"{f(gini.loc['AQ history (today, lags 1–2)'], 2)} for AQ history and {f(gini.loc['Mean temperature'], 3)} for mean temperature. Without AQ history, "
      f"the weather-only LR shows the trap pattern of H2: mean temperature {f(wo.loc['temp_mean_c', 'odds_ratio'], 2)}, vector wind "
      f"{f(wo.loc['vec_len_kmh', 'odds_ratio'], 2)}, humidity {f(wo.loc['rh_mean_pct', 'odds_ratio'], 2)} and temperature range "
      f"{f(wo.loc['temp_range_c', 'odds_ratio'], 2)} per SD, rain day {f(wo.loc['rain_day', 'odds_ratio'], 2)}. The weather trap is real, but it acts "
      "mostly through today's smog: stagnant, humid, rain-free days make today's index high, and the forecast reads that index.")
    figure("figures/fig_m3_6_drivers.png",
           "Drivers of the next-day spike forecast. (A) Odds ratios of the weather-only LR (bars; per 1 SD for continuous columns, 0 → 1 for binary ones) "
           "and the two non-zero odds ratios of LR full (diamonds); log scale, 1 = no effect. (B) Drop in validation PR-AUC when a group of columns is "
           "shuffled (±1 SD over 30 repeats), LR full and DT full. Produced by modeling.ipynb (Figure M3.6).", 5.8)
    p(f"**City effects are gone.** With the raw index, LR's city odds ratios reached {f(raw_lr.lr_max_city_or, 0)} (Rahim Yar Khan against Lahore), a "
      "correction for the city-specific thresholds rather than a risk ranking. With the margin encoding every city coefficient is 0, so no city is "
      f"flagged as riskier once its own threshold is accounted for. **The tree as a flow chart** (Figure {counters['figure'] + 1}): the first split asks whether today is "
      "a spike (margin ≤ 0); the next splits use the margin again and the mean temperature, so that colder days close to the threshold carry a "
      "higher risk, and days well above it are mostly followed by another spike.")
    figure("figures/fig_m3_7_tree.png",
           "Depth-3 decision tree for a spike tomorrow, fitted on the training rows with the tuned leaf size and class weights. Value = shares of no-spike "
           "and spike days; blue = mostly spike. Margin = index minus city threshold. Produced by modeling.ipynb (Figure M3.7).", 5.6)
    h2("11.3 Initial policy takeaways")
    bullets([
        "**A next-day, city-specific smog alert (Pakistan first).** Punjab's Environment Protection Department already has a smog policy and standing "
        "instructions for episodes of poor air quality (Environment Protection Department, n.d.), and in November 2024 the provincial government closed "
        "schools across several divisions and moved them online for days at a time (Waqar & Gabol, 2024). An alert built from today's index margin and "
        "temperature gives one day's notice, city by city, and catches onsets that a \"tomorrow = today\" rule misses by construction.",
        f"**Use the cost view to set the alert level.** A model alert beats persistence whenever a missed spike is judged at least {BE} times as costly as "
        "an unnecessary advisory. Officials can choose their ratio and read the threshold off the cost curve, instead of taking our 5:1.",
        "**A weather-trap checklist.** Stagnant, humid, rain-free days with a large day–night range and cold temperatures raise next-day risk (H2). "
        "Rain is a strong all-clear signal: no training rain day was followed by a spike, so advisories can be lifted after rain.",
        "**Fire control is source reduction, not a forecasting tool.** Fires did not add next-day skill once today's smog was known. Their smoke "
        "shows up in today's index, so the benefit of fire control appears as lower smog levels, not as extra forecast lead time.",
        "**Cross-border.** India's Graded Response Action Plan for Delhi-NCR is triggered by daily air-quality levels and, in the severe band "
        "(AQI 401–450), mandates hybrid learning up to Class V (Tribune News Service, 2024). The model warns Pakistani and Indian Punjab cities "
        "equally well (Section 10.4), so a shared next-day alert across the border is feasible. Whether India-origin smoke drives Pakistani smog (H4) "
        "cannot be settled from these baselines and is tested in Milestone 4.",
        "**Equity before deployment.** False alarms fall unevenly (Rahim Yar Khan, Multan, Faisalabad, Ferozepur). Repeated needless closures there "
        "would cost the same communities most, so per-city thresholds should be checked before any operational use."])

    # =================================================================
    # 12. Limitations and roadmap
    # =================================================================
    h1("12. Limitations and Milestone 4 Roadmap")
    bullets([
        "**Persistence is a strong benchmark.** LR full ranks spikes only slightly better than persistence (the PR-AUC CI includes 0), and for the "
        "continuous index no model beats persistence on validation. The models gain mainly at the alert decision.",
        f"**Class imbalance and one training winter.** Spikes are {f(tr_['spike rate (%)'], 1)}% of training days and come from a single winter; "
        "every threshold and hyperparameter rests on it.",
        f"**A short validation season.** 18 weeks, with {int(by_month.loc['2023-12', 'spikes'])} of {int(va_['spikes'])} spikes in December, give "
        "wide CIs, and December 2023 was unusually persistent.",
        "**Dependent series and model data.** Islamabad and Rawalpindi share one CAMS series; air quality is CAMS model output, not monitor data; "
        "one UTC+5 clock is used for India.",
        "**Label timing.** The Milestone 2 label puts spikes in December–January, after the burning peak; the month-wise label (Section 9.3) answers "
        "this only in part.",
        "**Uneven false alarms by city** (Section 10.4), and observed rather than forecast weather on day *t*."])
    p("**Milestone 4 roadmap.**")
    bullets([
        "**Advanced models:** random forest and gradient boosting on the same purged folds, with per-horizon tuning for *t* + 2 and *t* + 3.",
        "**Probability calibration** (reliability curves, isotonic or Platt scaling), so that alert probabilities can be read at face value.",
        "**Fairness audit:** error-rate parity by city and by country, per-group thresholds, and the cost each group bears; an ethical review of who "
        "carries false alarms and missed warnings.",
        "**Remaining hypotheses:** H1 (cone vs radius), H3 (fire × stagnation) and H4 (cross-border) with city-clustered regressions.",
        "**Data:** surface pressure re-exported for the same coordinates; a check of the ozone weight in the index.",
        "**Week 14:** retrain with 2024 H1 added and test out of time on 2024 H2, with every setting kept as saved."])


if M3:
    M3_REFS = [
        "Environment Protection Department, Government of the Punjab (n.d.). Smog Commission reports, including the Policy and Action Plan for Control, "
        "Mitigation, Advisory, and Protective Measures in Extreme Weather Conditions of Dense Smog in Punjab and the Standing Instructions for "
        "Management of Episodes of Poor Air Quality (2018). https://epd.punjab.gov.pk/smog_commission_reports",
        "Pandey, A., Brauer, M., Cropper, M. L., et al. (2021). Health and economic impact of air pollution in the states of India: the Global Burden of "
        "Disease Study 2019. The Lancet Planetary Health, 5(1), e25–e38. https://doi.org/10.1016/S2542-5196(20)30298-9",
        "Pedregosa, F., Varoquaux, G., Gramfort, A., et al. (2011). Scikit-learn: Machine learning in Python. Journal of Machine Learning Research, "
        "12(85), 2825–2830.",
        "Roberts, D. R., Bahn, V., Ciuti, S., et al. (2017). Cross-validation strategies for data with temporal, spatial, hierarchical, or phylogenetic "
        "structure. Ecography, 40(8), 913–929. https://doi.org/10.1111/ecog.02881",
        "Saito, T., & Rehmsmeier, M. (2015). The precision-recall plot is more informative than the ROC plot when evaluating binary classifiers on "
        "imbalanced datasets. PLoS ONE, 10(3), e0118432. https://doi.org/10.1371/journal.pone.0118432",
        "Seabold, S., & Perktold, J. (2010). Statsmodels: Econometric and statistical modeling with Python. Proceedings of the 9th Python in Science "
        "Conference, 92–96. https://doi.org/10.25080/Majora-92bf1922-011",
        "Tribune News Service (2024, December 15). GRAP rules revised: Nod to hybrid learning till Class V in severe AQI. The Tribune. "
        "https://www.tribuneindia.com/news/delhi/grap-rules-revised-nod-to-hybrid-learning-till-class-v-in-severe-aqi/",
        "Waqar, A., & Gabol, I. (2024, November 12). Punjab govt orders closure of all schools as province tackles hazardous air quality. Dawn. "
        "https://www.dawn.com/news/1871888"]

# =====================================================================
# Front matter
# =====================================================================
if M3:
    blocks.append({"t": "title", "text": "Crop Fires, Weather Traps and Smog across Punjab: Data, Exploratory Analysis and Baseline Forecasts"})
    blocks.append({"t": "subtitle", "text": "Trans-Boundary Smog Prediction: Milestone 03, Baseline Models, Leakage-Free Validation and Error-Cost Analysis"})
else:
    blocks.append({"t": "title", "text": "Crop Fires, Weather Traps and Smog across Punjab: Data Preparation and Exploratory Analysis"})
    blocks.append({"t": "subtitle", "text": "Trans-Boundary Smog Prediction: Milestone 02, Draft Sections II and III, Merged Master Dataset"})
blocks.append({"t": "authors", "text": "Munir Tariq (10067)  |  Ismail Nooruddin (09958)  |  Bilal Ayub (09716)  |  "
                                         "Data Science for Social Good, Habib University  |  October 2026"})

h2("Abstract")
p("Every winter, smoke from crop-residue burning and city emissions is trapped over the Punjab plain shared by Pakistan and India. "
  "This report describes how three independent data streams were cleaned and merged into one master dataset, and what the first analysis of that dataset shows. "
  "Hourly Open-Meteo air quality (CAMS model output), hourly Open-Meteo weather and 1.28 million NASA VIIRS fire detections were aligned to one UTC+5 clock "
  "and joined one-to-one into a table of 5,665 city-days (11 cities, 4 August 2022 to 31 December 2023) and 287 columns, with no missing predictor value. "
  "The target is a Composite Smog Index built from six standardised pollutants, with a city-specific spike label. "
  "On the training period, four results stand out. First, fires inside a ±45° upwind cone within 300 km track next-day smog "
  "(median Spearman ρ = 0.23 over the Pakistani cities in the harvest season), while a plain 300 km circle (−0.06) and a downwind placebo cone (0.01) do not. "
  "Second, the association is strongest one day after the fires. Third, stagnant and humid days roughly triple the next-day spike rate, and no rain day was followed by a spike. "
  "Fourth, spikes occur mainly in December and January, after the October–November burning peak, so fires alone do not make a spike: the weather must trap the smoke. "
  "Five formal hypotheses, mapped to columns of the master dataset, set up the modelling in Milestone 3."
  + (M3_ABSTRACT if M3 else ""))

# =====================================================================
# 1. Project alignment
# =====================================================================
h1("1. Project Alignment and Master Dataset Overview")
p("The project predicts hazardous smog spikes in Pakistani Punjab cities one to three days in advance from upwind crop-fire detections and from weather "
  "conditions that trap pollution. **Research question:** which fire and weather predictors, available on day *t*, explain Composite Smog Index spikes "
  "on days *t* + 1 to *t* + 3, and how much better than a persistence baseline and a weather-only baseline can they forecast those spikes? "
  "The work supports SDG 3 (targets 3.9 and 3.d: illness from air pollution and early warning), SDG 11 (target 11.6: urban air quality) and SDG 13 "
  "(regional climate action); the cross-border analysis also relates to SDG 17 (cooperation between countries). "
  "Following the instructor's feedback, the proposal's fixed target score (ROC-AUC above 0.88) has been dropped: the aim is to identify sound predictors and report the best honest performance.")
table("Team members, disciplinary background and Milestone 2 roles.",
      ["Member", "ID", "Background", "Role 1 (own data stream)", "Role 2 (merged data)"],
      [["Munir Tariq", "10067", "Computer Science (minor: Social Development and Policy)", "Person B: weather and wind",
        "Leads the merge; master overview, summary tables, correlations, weather traps"],
       ["Ismail Nooruddin", "09958", "Computer Science", "Person A: air quality and target",
        "Group-by and contingency tables, index figure, index weight check"],
       ["Bilal Ayub", "09716", "Computer Science", "Person C: NASA VIIRS fire",
        "Cone and radius sensitivity, cross-border check"]],
      [1500, 650, 2400, 2000, 3242])
table("Overview of the master analytical dataset (Dataset/clean/master_daily.parquet; first sheet of the submitted workbook).",
      ["Item", "Description"],
      [["Size", f"{ov['Rows (observations)']} rows × {ov['Columns (variables)']} columns; no missing value in any predictor"],
       ["Observational unit", "1 row = 1 city on 1 local (UTC+5) day; keys: city, country, date"],
       ["Cities (11)", "Pakistan: Lahore, Faisalabad, Multan, Rawalpindi, Sialkot, Rahim Yar Khan, Islamabad. Indian Punjab: Amritsar, Ferozepur, Ludhiana, Jalandhar"],
       ["Period and split", f"{ov['Period']}. Training 4 Aug 2022 to 31 Aug 2023 ({sp.loc['train', 'rows']:,} city-days); "
                            f"3-day gap; validation 4 Sep to 31 Dec 2023 ({sp.loc['validation', 'rows']:,} city-days)"],
       ["Sources (3)", "Open-Meteo Air Quality API, hourly, CAMS model output (Person A); Open-Meteo Historical Weather API, hourly, reanalysis-based (Person B); "
                       "NASA FIRMS archive, VIIRS 375 m active fires from NOAA-20, point detections (Person C)"],
       ["Columns by origin", "Air quality 52; weather 58; fire 128; keys, targets, lags, baselines, dummies and split built in the merge 49"],
       ["Targets", "Composite Smog Index and spike label on days t+1, t+2 and t+3 (target_index_h1..h3, target_spike_h1..h3)"],
       ["Sealed data", "All 2024 files, kept for the final out-of-time test and never read in this milestone"]],
      [2200, 7592])

# =====================================================================
# 2. Data and preprocessing
# =====================================================================
h1("2. Data and Preprocessing (Draft Section II)")
h2("2.1 Collection audit")
p("Each stream was collected and cleaned by one team member in its own notebook, then handed over as a clean daily table with its saved settings (Table 3). "
  "Air quality and weather were exported per city centre from Open-Meteo as hourly files in GMT. Both are gridded model estimates rather than station readings, "
  "so they suit comparisons between days and cities. Fire detections were downloaded from the NASA FIRMS archive as one file per country and year.")
table("Raw data collected for each stream and the main audit findings.",
      ["Stream", "Collection", "Raw records", "Audit findings"],
      [["Air quality (A)", "Open-Meteo Air Quality API; 11 city files (10 CSV, Ludhiana XLSX), hourly, GMT; CAMS model output on a grid of about 0.4°",
        "453,192 hourly rows", "No duplicate or skipped hours. No pollutant value before 4 Aug 2022 in any city. Islamabad and Rawalpindi identical (same grid cell)."],
       ["Weather (B)", "Open-Meteo Historical Weather API; 11 city files (10 CSV, Ludhiana XLSX), hourly, GMT",
        "433,728 hourly rows", "No missing value, duplicate or skipped hour. No surface-pressure column in the export."],
       ["Fire (C)", "NASA FIRMS archive; VIIRS 375 m (NOAA-20); 4 files (India and Pakistan, 2022 and 2023); 2024 files sealed",
        "1,284,773 detections", "No duplicates; one satellite; times in UTC; acquisition time read as text to keep leading zeros."]],
      [1300, 3500, 1500, 3492])

h2("2.2 Alignment, reshaping and merge")
p("All raw times are in GMT. Each stream added 5 hours to the full timestamp **before** taking the calendar date, so that evening hours fall on the correct local day "
  "(26,626 fire detections moved to the next date). The same UTC+5 clock was used for the Indian cities so that all streams share day boundaries. "
  "The reshaping steps were: stacking the 11 city files of each stream (concat); aggregating hourly rows to one row per city-day (group-by with mean, maximum, total and "
  "vector-mean rules); building a long table of fire counts for every city, cone, radius and origin (602,250 rows) and pivoting the chosen settings into columns; "
  "and joining the three streams. City names come from one shared dictionary, so the keys are spelled identically in every table.")
p("The merge started from an empty calendar of 11 cities × 515 days (5,665 rows), so that a missing day in any stream would remain visible. "
  "Air quality, weather and fire were then left-joined on city, country and date with a one-to-one check; the row count stayed at 5,665 after every join and every row "
  "found a partner. Lags of 1 to 3 days and the targets for days t+1 to t+3 were computed **within each city**, so that the last days of one city cannot leak into the "
  "first days of the next. Table 4 traces every row from the raw files to the master table.")
table("Row bookkeeping from the raw files to the master table (each step is logged in the workbook sheet Decisions_Log).",
      ["Stream", "Steps and row counts"],
      [["Air quality", "453,192 hourly rows → 191,153 in 2022–2023 → 135,905 after removing the empty Jan–Aug 2022 block → 5,665 city-days (each with ≥ 18 valid hours)"],
       ["Weather", "433,728 hourly rows → 188,393 in 2022–2023 → 7,852 city-days → 5,665 in the modelling window"],
       ["Fire", "1,284,773 detections → 287,323 in the study box (26–37°N, 68–79°E) → 279,968 vegetation fires → 238,796 with nominal or high confidence "
                "→ 238,756 on 2022–2023 local dates → 8,030 city-days (days without fires = 0) → 5,665 in the window"],
       ["Master", "calendar 5,665 → air-quality join 5,665 → weather join 5,665 → fire join 5,665 (all rows matched); 287 columns"]],
      [1300, 8492])

h2("2.3 Missing data and selection bias")
mis = tab("master_missing_all_columns", index_col=0)
complete = int((mis["missing_count"] == 0).sum())
table("Missing values by stage (counts and percentages for all 287 columns are in the workbook sheet Missing_All_Columns).",
      ["Where", "What is missing", "Count (%)", "Decision"],
      [["Air quality, raw 2022–2023", "All pollutants, one continuous block from 6 Jan to 4 Aug 2022, same hours in every city", "55,248 of 191,153 hourly rows (28.9%)",
        "Not imputed; the modelling window starts on 4 Aug 2022 for all streams"],
       ["Weather, raw", "Any variable", "0 of 433,728 rows", "Nothing to impute"],
       ["Fire, daily grid", "Days without any detection", "–", "Coded 0 (a real zero), never missing"],
       ["Master, predictors", f"Any of the {complete} key, predictor and dummy columns", "0", "–"],
       ["Master, targets and lags", "Targets for days t+1 to t+3; index lags 1 to 3", "11 / 22 / 33 rows (0.19% / 0.39% / 0.58%)",
        "Target day in sealed 2024, or lag day before 4 Aug 2022: left missing and excluded per horizon"]],
      [1700, 3000, 2000, 3092])
p("**Why no imputation.** The air-quality gap is not random: the source has no pollutant values before August 2022 in any city. Filling seven months by interpolation "
  "would invent the seasonal pattern the model must learn, so those rows were removed from every stream (listwise deletion of the block). "
  f"In total {complete} of the 287 master columns have no missing value.")
p("**Selection bias.** (i) The training period contains only **one** harvest season (October–December 2022), so every seasonal estimate rests on one winter; the final "
  "test therefore retrains with the first half of 2024 and tests on the second half. (ii) On 13–16 December 2022 every pollutant is near zero in all cities at once, a likely "
  "source error. These 44 city-days are flagged (suspect_day = 1) and kept as rows: removing them would break each city's unbroken daily calendar, which the lags and targets "
  "rely on, and the flag lets Milestone 3 drop them in one step. They are already left out of the air-quality scaling and the spike thresholds. Their effect is reported: "
  "the index has a skewness of −1.15 on training days with them and +0.26 without them. (iii) The satellite cannot see fires under thick cloud or fog, which is common on "
  "the worst smog days, so fire–smog associations are likely underestimated. (iv) Islamabad and Rawalpindi share one air-quality series, so there are 10 independent "
  "air-quality series, not 11.")

h2("2.4 Transformations, scaling and the target")
p("Variables with strong right skew were transformed with log(1 + x), which keeps zero values at zero (Table 6, Figure 1).")
table("Skewness before and after log(1 + x), training period. Air-quality rows leave out the 44 flagged days, so they differ slightly from Table 9 (PM2.5 1.91, CO 3.17 with them).",
      ["Variable", "Skew, raw", "Skew, log(1 + x)", "Note"],
      [["PM2.5 daily mean (µg/m³)", "1.95", "0.37", "10 of 13 air-quality columns had skew > 1 and were logged"],
       ["CO daily mean (µg/m³)", "3.18", "0.37", ""],
       ["Rain total (mm)", "6.46", "1.79", "61% of days have 0 mm, so the skew stays above 1"],
       ["Fires in the upwind cone, 300 km", f(fs.loc['fire_cnt_up45_r300_all', 'skew_raw']), f(fs.loc['fire_cnt_up45_r300_all', 'skew_log1p']),
        f"{f(fs.loc['fire_cnt_up45_r300_all', 'share_zero_days_pct'], 1)}% zero days"],
       ["India-origin fires in the cone", f(fs.loc['fire_cnt_up45_r300_in', 'skew_raw']), f(fs.loc['fire_cnt_up45_r300_in', 'skew_log1p']),
        f"{f(fs.loc['fire_cnt_up45_r300_in', 'share_zero_days_pct'], 1)}% zero days"]],
      [3000, 1300, 1600, 3892])
figure("figures/fig_a1_pm25_log_transform.png",
       "Daily mean PM2.5 across the 11 cities on training days, (a) before and (b) after the log(1 + x) transform; dashed line = mean, solid line = median. "
       "The long right tail disappears after the transform. Produced by air_quality.ipynb (flagged December days left out).", 5.0)
p("**Standardisation.** Continuous predictors and pollutants were converted to z-scores, z = (x − mean)/SD, after the log transform where applied, using the mean and SD of the "
  "**training period only**. One set of parameters per variable is used for all cities, so real differences between cities remain, and the parameters are saved for reuse "
  "on 2024. Min-Max scaling was not used: a few extreme fire and rain days would squeeze almost every other day towards 0.")
p("**Target.** Composite Smog Index = 0.40·z(PM2.5) + 0.12·[z(PM10) + z(NO2) + z(SO2) + z(O3) + z(CO)], computed from daily means. A **spike** is a day whose index is at or "
  "above the 90th percentile of that city's training October–March days. The thresholds run from 0.36 (Rahim Yar Khan) to 2.18 (Lahore) and give 297 spike city-days "
  "(5.2%) in the window.")

h2("2.5 Categorical encoding")
p("Nominal variables were converted into 0/1 dummy columns, with one category dropped as the reference so that a regression with an intercept stays identifiable (Table 7). "
  "A numeric code (for example 0 to 7 for wind sectors) would impose a false order. The notebook confirms that every row belongs to exactly one category of each variable "
  "and that the eight wind-sector dummies are all 0 on exactly the 631 stagnant city-days. The workbook sheet Encoding_Example shows real rows next to their dummies.")
table("Nominal variables converted to 0/1 dummy columns.",
      ["Variable", "Dummy columns", "Reference category"],
      [["City (11 categories)", "city_faisalabad … city_jalandhar (10)", "Lahore"],
       ["Country; border group", "is_india; near_border (Lahore, Sialkot)", "Pakistan; other cities"],
       ["Month (12 categories)", "month_02 … month_12 (11); harvest_season (Oct–Dec) for group summaries", "January"],
       ["Wind-from sector (8 + calm)", "wind_from_n, _ne, _e, _se, _s, _sw, _w, _nw (8)", "Calm (stagnant) days"],
       ["Already binary", "stagnant, rain_day, smog_spike, suspect_day, outlier flags", "–"]],
      [2400, 4900, 2492])

h2("2.6 Spatial fire features")
p("For each city, the great-circle distance and the compass bearing to every fire within 300 km were computed. A fire is **upwind** when its bearing lies within the cone "
  "half-angle (±30°, ±45° or ±60°) of the direction the daily wind comes from; a ±45° **downwind** cone is kept as a placebo. On stagnant days (daily vector-mean wind "
  "below 2 km/h, 10.9% of training city-days) the wind direction is unreliable, so the cone keeps every fire in the radius. Every count is split by origin (fires detected "
  "in India or in Pakistan), which makes the cross-border question testable (Figure 2). Automatic tests confirm that a north wind keeps fires to the north and that no cone "
  "holds more fires than its circle. The default setting, the ±45° upwind cone at 300 km, was chosen on the training harvest season only (Section 3.3).")
figure("figures/fig_fire_study_area.png",
       "Crop-fire detections (NASA VIIRS NOAA-20, vegetation fires, nominal or high confidence) around the 11 study cities, October–November 2023. Blue = India-origin, "
       "orange = Pakistan-origin. The circle is the 150 km radius around Lahore; the wedges are the ±30°, ±45° and ±60° upwind cones for Lahore's wind on 29 October 2023. "
       "Produced by fire.ipynb.", 4.1)

h2("2.7 Summary of preprocessing decisions")
table("Preprocessing decisions, alternatives considered and justification.",
      ["Decision", "Alternative", "Justification"],
      [["Add 5 h (UTC+5) before taking the date, for all cities", "Keep GMT dates; +5:30 for India", "Day boundaries must match across streams; one clock keeps the cross-border design consistent"],
       ["Modelling window from 4 Aug 2022", "Impute the empty air-quality block", "Seven months of invented pollution would create the pattern the model must learn"],
       ["Lags and targets within each city", "Shift the whole table", "Prevents one city's last days leaking into the next city's first days"],
       ["log(1 + x) for skewed variables", "No transform", "Removes the long right tail and keeps zeros at zero"],
       ["Z-scores from the training period, one set for all cities", "Fit on all data; one set per city", "Prevents leakage from validation and test data; keeps real city differences"],
       ["Keep outliers and add flags", "Delete, cap or winsorise", "Extreme days are the smog episodes and fire outbreaks the project studies"],
       ["Dummy columns with a reference category", "Numeric codes", "Categories are nominal; codes would imply a false order"],
       ["Upwind cone ±45° at 300 km", "Plain radius; 150 km", "Highest median correlation with next-day smog on training data; the plain circle carries no signal"]],
      [2900, 2300, 4592])

# =====================================================================
# 3. EDA
# =====================================================================
h1("3. Exploratory Data Analysis (Draft Section III)")
p(f"Unless stated otherwise, statistics use the {sp.loc['train', 'rows']:,} training city-days ({sp.loc['train', 'oct_dec_rows']:,} in October–December 2022). "
  "The validation period is not analysed until Milestone 3, and 2024 is never used. All figures have a title, axes labelled with units, a legend where several series "
  "are shown, and a colour-blind-safe palette.")

h2("3.1 Univariate analysis")
KEEP = ["Composite Smog Index (z units)", "PM2.5 daily mean (µg/m³)", "CO daily mean (µg/m³)",
        "Temperature range (°C)", "Relative humidity (%)", "Rain total (mm)", "Vector-mean wind (km/h)",
        "Fires in upwind cone, 300 km (count)", "India-origin fires in cone (count)", "Fires within 300 km, no cone (count)"]
table(f"Summary statistics of the key variables, training period (n = {sp.loc['train', 'rows']:,} city-days).",
      ["Variable (unit)", "Mean", "Median", "SD", "IQR", "Skew", "Zero days (%)"],
      [[v, f(s.loc[v, 'mean']), f(s.loc[v, 'median']), f(s.loc[v, 'sd']), f(s.loc[v, 'iqr']), f(s.loc[v, 'skew']), f(s.loc[v, 'share_zero_pct'], 1)] for v in KEEP],
      [3300, 1050, 1050, 1050, 1050, 1000, 1292])
p("**Resistant and non-resistant measures.** The weather variables are nearly symmetric (temperature range: mean 11.26 °C, median 11.30 °C, skew 0.02), so the mean and SD "
  "describe them well. The pollutants are moderately right-skewed (PM2.5 mean 54.4 µg/m³ against a median of 46.1 µg/m³). Fire counts and rain are zero-inflated and extremely skewed: "
  "fires in the cone have a mean of 43.3 but a median of 4, India-origin fires reach the cone on only 39% of days, and rain has a median of 0 mm against a mean of 2.2 mm. "
  "For these variables the median and IQR describe a typical day, while the mean describes the total load; the SD (4 to 51 times the IQR for the fire counts) is driven by a "
  "handful of days. Daily mean PM2.5 is above the WHO 24-hour guideline of 15 µg/m³ on 99.4% of training city-days outside the flagged days; as these are model estimates, "
  "this is an indication rather than an official exceedance count.")

h2("3.2 Outlier diagnostic")
table("Outliers by the z-score rule (|z| > 3) and the quartile rule (beyond Q1 − 1.5·IQR or Q3 + 1.5·IQR), training period. Masked = extra points the z-rule finds "
      "once the first-pass z-outliers are removed. SD inflation = SD of all days relative to the SD without the IQR outliers.",
      ["Variable (unit)", "z-rule", "IQR rule", "IQR (%)", "Masked", "SD, all", "SD w/o IQR outliers", "SD inflation (%)"],
      [[v, int(o.loc[v, 'z_outliers']), int(o.loc[v, 'iqr_outliers']), f(o.loc[v, 'iqr_pct'], 1), int(o.loc[v, 'z_new_after_removal (masking)']),
        f(o.loc[v, 'sd_all']), f(o.loc[v, 'sd_without_iqr_outliers']), f(o.loc[v, 'sd_inflation_pct'], 0)] for v in KEEP],
      [3000, 800, 900, 850, 850, 1000, 1250, 1142])
p("**Masking.** The quartile rule flags far more days than the z-rule in every skewed variable (rain 823 against 89; fires in the cone 534 against 63; PM2.5 292 against 96). "
  "Extreme days inflate the SD, which widens the 3-SD limit and hides other extreme days: removing the first-pass z-outliers and applying the rule again finds 144 more rain days, "
  "101 more fire days and 63 more PM2.5 days. **Variance inflation.** Without the quartile-rule outliers, the SD of rain falls from 6.26 to 0.43 mm and that of fires in the cone "
  "from 177 to 14.6, so for zero-inflated variables the SD consists mostly of the outliers. On the log scale, fires in the cone have no quartile-rule outliers at all. "
  "**Decision.** No outlier was deleted, capped or winsorised: they are real smog episodes, storms and fire outbreaks, the events the project predicts. Each stream carries "
  "0/1 flag columns instead.")

h2("3.3 Bivariate and multivariate analysis")
se = tab("groupby_season", index_col=0)
st = tab("groupby_stagnant", index_col=0)
ra = tab("groupby_rain", index_col=0)
co = tab("groupby_country", index_col=0)
rows = []
for name, t in [("Season", se), ("Wind", st), ("Rain", ra), ("Country", co)]:
    for k, r in t.iterrows():
        rows.append([name, k, f"{int(r['city_days']):,}", f(r['mean_index']), f(r['median_index']), f(r['spike_share_pct'], 1)])
p("**When do spikes happen?** Table 11 groups the training days by season, wind, rain and country. By month, spikes are concentrated in "
  f"**December ({f(mo.loc[12, 'spike_share_pct'], 1)}% of city-days) and January ({f(mo.loc[1, 'spike_share_pct'], 1)}%)**, against "
  f"{f(mo.loc[10, 'spike_share_pct'], 1)}% in October and {f(mo.loc[11, 'spike_share_pct'], 1)}% in November, while fires in the cone peak in October and November "
  "(57,087 and 50,062 detections). The wheat-burning season of May 2023 (30,235 cone detections) produced **no** spike. Fires alone therefore do not make a spike: the smoke "
  "must be trapped by winter weather (Figure 3).")
table("Mean Composite Smog Index and share of spike days by group, training period.",
      ["Grouping", "Group", "City-days", "Mean index", "Median index", "Spike days (%)"], rows, [1300, 2700, 1300, 1400, 1500, 1592])
figure("figures/fig_a3_index_over_time.png",
       "Composite Smog Index over time (7-day centred average; no unit, 0 = average training day) for Lahore, Faisalabad, Rahim Yar Khan and Amritsar, "
       "4 August 2022 to 31 December 2023. Grey bands mark October–December; dashed and dotted lines mark the end of training and the start of validation. "
       "The break in December 2022 is the flagged suspect days. Produced by air_quality.ipynb.", 5.6)
p(f"**Contingency tables.** On the training harvest days, {f(cs.loc['stagnant today', 'spike_rate_pct'], 1)}% of days after a stagnant day were spikes, against "
  f"{f(cs.loc['ventilated today', 'spike_rate_pct'], 1)}% after a ventilated day (χ² = 24.4, odds ratio 3.61, 95% CI 2.15–6.06). After a day with at least one fire in the "
  "cone, 12.0% of next days were spikes, against 2.6% after a day with none (χ² = 8.3, odds ratio 5.11, 95% CI 1.60–16.37). Consecutive days of a city are not independent, "
  "so these p-values (< 0.01) overstate certainty and the tables describe association only.")
figure("figures/fig_m2_correlation_harvest.png",
       "Spearman rank correlations between the next-day Composite Smog Index, today's index, fire counts (±45° upwind cone at 300 km, by origin, and the plain 300 km circle) "
       "and daily weather, 1,012 training harvest city-days. Temperature range = daily max − min (°C); rain = daily total (mm); vector-mean wind = length of the averaged "
       "wind vector (km/h). Diverging scale centred on 0. Produced by merge_analysis.ipynb.", 3.9)
p("**Correlations (Figure 4).** Today's index is by far the strongest correlate of tomorrow's (ρ = 0.82), which makes persistence the baseline every model must beat. "
  "Among the predictors, wind speed (−0.38), fires in the upwind cone (0.34), humidity (0.32), vector-mean wind (−0.31), temperature range (0.30) and rain (−0.29) relate to "
  "the next-day index, while the plain 300 km circle is weaker (0.19). Wind speed and vector-mean wind are nearly redundant (0.85), as are mean, minimum and maximum "
  "temperature (r = 0.91–0.98), so models will use one of each pair.")
p("**Fire cone and radius (Figure 5).** In the harvest season the cone matters more than the circle. At 300 km the ±45° upwind cone gives a median ρ of "
  f"{f(cvr.loc[(HEAD, 'All Pakistani (7)'), 'upwind cone (up45, 300 km)'])} (positive in all 7 Pakistani cities), the plain circle "
  f"{f(cvr.loc[(HEAD, 'All Pakistani (7)'), 'no cone (300 km)'])} and the downwind placebo {f(cvr.loc[(HEAD, 'All Pakistani (7)'), 'downwind placebo (down45, 300 km)'])}: "
  "a large circle counts as many fires downwind as upwind and so carries no signal. Inside the cone, ρ grows with the radius, so the smoke that matters is regional. "
  "The ±30° and ±60° cones give similar values; with 92 days per city a correlation has a standard error of about 0.10, so ±45° was kept as the middle setting. "
  "Over the full training year every 300 km setting looks good (0.16–0.35), **including the placebo**, because fires and smog share a seasonal cycle; this is why the "
  "selection used the harvest season only. The cone count is most related to smog **one day later** "
  f"(median ρ = {f(up_lag[1])}, against {f(up_lag[0])} on the same day, {f(up_lag[2])} after two days and {f(up_lag[3])} after three; the window here is set on the smog day, "
  "hence the small difference from 0.23). At the median vector-mean wind of about 5 km/h, smoke travels roughly 120 km a day, consistent with a one-to-two-day delay.")
figure("figures/fig_m1_cone_radius_sensitivity.png",
       "Median Spearman correlation between the fire count on day t and the Composite Smog Index on day t + 1, for every cone and radius, computed within each city. "
       "Top: training harvest season (92 days per city), used to choose the setting (black box). Bottom: full training year (393 days per city), where the shared seasonal "
       "cycle inflates every setting, including the placebo. Near border = Lahore, Sialkot; Far = Multan, Rahim Yar Khan, Islamabad, Rawalpindi. Produced by merge_analysis.ipynb.", 5.7)
p(f"**Weather traps (Figure 6).** Stagnant days are followed by a spike {f(tr.iloc[0]['spike_rate_with_pct'], 1)}% of the time "
  f"({f(tr.iloc[0]['spike_rate_without_pct'], 1)}% otherwise) and humid days {f(tr.iloc[1]['spike_rate_with_pct'], 1)}% "
  f"({f(tr.iloc[1]['spike_rate_without_pct'], 1)}%). No rain day was followed by a spike (0 of {int(tr.iloc[2]['days_without'])}). When stagnation, no rain and high humidity coincide, "
  f"{f(tr.iloc[5]['spike_rate_with_pct'], 0)}% of next days are spikes (9 of 20, risk ratio {f(tr.iloc[5]['risk_ratio'], 1)}). "
  "The temperature-range proxy points the other way from the work plan: none of the 61 small-range days was followed by a spike, while large-range days (> 13.6 °C) were "
  f"followed by {f(tr.iloc[3]['spike_rate_with_pct'], 1)}% (risk ratio {f(tr.iloc[3]['risk_ratio'])}). A small day–night range signals cloud or rain, which mix and wash the air, "
  "whereas surface inversions form on clear, calm nights with strong cooling, so a **large** range is used as the inversion proxy.")
figure("figures/fig_m6_weather_trap.png",
       "Share of next days that are smog spikes when today has each weather condition (filled circles, 95% Wilson intervals) and on all other days (hollow diamonds), "
       "training harvest season. Dashed line: rate over all harvest days (11.0%); n = city-days with the condition. Produced by merge_analysis.ipynb.", 5.4)
lah, sia, fai = xb.loc["Lahore"], xb.loc["Sialkot"], xb.loc["Faisalabad"]
p(f"**Cross-border check.** Only Lahore ({int(lah['IN_fire_days'])} days with India-origin fires in the cone), Sialkot ({int(sia['IN_fire_days'])}) and Faisalabad "
  f"({int(fai['IN_fire_days'])}) receive India-origin fires often enough to test the cross-border claim; in Multan, Rahim Yar Khan, Islamabad and Rawalpindi this happens on 1 to 18 days only. "
  f"In Sialkot, India-origin fires go with higher next-day smog (ρ = {f(sia['rho_IN_next_day'])}, against {f(sia['rho_PK_next_day'])} for Pakistan-origin fires); "
  f"in Lahore it is the other way round ({f(lah['rho_IN_next_day'])} against {f(lah['rho_PK_next_day'])}), although {f(lah['IN_share_pct'], 0)}% of the fires in Lahore's cone are Indian. "
  "The cross-border signal is therefore mixed and rests on one season; hypothesis H4 tests it with controls.")
p(f"**Robustness of the index weights.** Rebuilding the index with equal weights, without ozone or without PM10 ranks the days almost identically (Spearman ρ ≥ "
  f"{f(w['spearman_with_main'].min(), 3)}). Dropping ozone changes the most spike labels ({int(w.loc['without ozone', 'labels_changed'])} city-days, "
  f"against {int(w.iloc[0]['spike_days'])} training spikes in the main index), because winter ozone moves opposite to NO2. The main weights are kept and the ozone sensitivity is listed as a limitation.")

# =====================================================================
# 4. Hypotheses
# =====================================================================
h1("4. Hypotheses and Analytical Plan")
p("Each hypothesis starts from a pattern in Section 3 and is mapped to columns of the master dataset (Table 12). The response is always measured on day t + 1 "
  "(t + 1 to t + 3 for H5) and uses only information known on day t. The full mapping, with the planned test for each hypothesis, is in the workbook sheet Hypothesis_Mapping.")
H = [("H1 Cone vs radius (C)", "**H0:** adding the upwind-cone fire count to a model with the plain 300 km count and the controls does not improve the explanation of the next-day index (β_cone = 0). "
      "**H1:** the cone count is positively associated with the next-day index beyond the plain count (β_cone > 0).", "11.6, 13"),
     ("H2 Weather trap (B)", "**H0:** stagnation, humidity, absence of rain and a large temperature range do not change the odds of a next-day spike (OR = 1). "
      "**H1:** each raises the odds (OR > 1).", "3.9, 11.6"),
     ("H3 Fire × stagnation (A)", "**H0:** the fire effect on the next-day index is the same on stagnant and ventilated days (β_fire×stagnant = 0). "
      "**H1:** it is stronger on stagnant days (β_fire×stagnant > 0).", "3.9, 13.1"),
     ("H4 Cross-border (C)", "**H0:** in Pakistani cities, India-origin upwind fires are not associated with the next-day index once Pakistan-origin fires and weather are "
      "controlled, and the association is the same near the border and far from it (β_IN = 0, β_IN×near = 0). **H1:** India-origin fires raise next-day smog, more in "
      "Lahore and Sialkot than in far cities (β_IN×near > 0).", "13, 17, 11.6"),
     ("H5 Forecast value (A)", "**H0:** a model with the fire and weather features does not beat persistence or a weather-only model on validation (ΔPR-AUC ≤ 0, ΔMAE ≥ 0). "
      "**H1:** it beats both for at least one horizon of 1 to 3 days.", "3.d, 3.9")]
# The shared control set C is written once; the table shows what each hypothesis adds to it (full lists: hypothesis_mapping.csv)
CTRL = "month_02..month_12, city_* (10), temp_mean_c, temp_range_c, rh_mean_pct, precip_sum_mm, vec_len_kmh (those not used as X)"
assert hm.loc["H1", "controls"] == CTRL and hm.loc["H3", "controls"] == CTRL
assert hm.loc["H4", "controls"] == "fire_cnt_up45_r300_pk_log1p_z, " + CTRL.replace("city_* (10)", "city_* (6 Pakistani)")
short = {"H1": "C", "H2": hm.loc["H2", "controls"], "H3": "C",
         "H4": "C with city_* for the 6 Pakistani cities, plus fire_cnt_up45_r300_pk_log1p_z", "H5": hm.loc["H5", "controls"]}
table("Formal hypotheses with variable mapping (Y = response, X = main predictors) and the SDG targets they inform. Owners in brackets.",
      ["ID", "Hypotheses", "Response (Y)", "Predictors (X)", "Controls", "SDG"],
      [[hid, txt, hm.loc[hid.split()[0], "Y"], hm.loc[hid.split()[0], "X"], short[hid.split()[0]], sdg] for hid, txt, sdg in H],
      [1050, 3250, 1250, 2000, 1550, 692],
      note=f"C = {CTRL.replace(' (those not used as X)', '')}, excluding any column already used as X.", font=7)
p("**Analytical plan.** Consecutive days of a city are correlated, and Islamabad and Rawalpindi share air-quality values, so H1–H4 use regressions with city-clustered "
  "standard errors or a block bootstrap: logistic regression for the spike label and linear regression for the index, with interaction terms for H3 and H4. "
  "Non-linear effects will be checked with gradient-boosted trees and permutation importance. For H5, models are compared on the validation season (1,309 city-days, "
  "1,012 of them in October–December 2023) against persistence (persist_index, persist_spike) and a weather-only model. Because spikes are rare (5.2%), results are "
  "reported as PR-AUC, recall and precision as well as ROC-AUC and the Brier score, and as MAE for the index. Because the spike label falls mainly in December–January, "
  "after the burning peak, Milestone 3 will also report results for the continuous index and compare a label with month-specific thresholds.")
if M3:
    p(M3_SECTION4_CLOSE)

# =====================================================================
# 5. Limitations and 6. Reproducibility
# =====================================================================
h1("5. Limitations")
bullets(["**Model-based air quality.** Open-Meteo air quality is CAMS model output on a coarse grid, not monitor data; neighbouring cities can share values (Islamabad = Rawalpindi).",
         "**One training winter.** Every learned threshold, scaling parameter and the cone choice rest on one harvest season (92 days per city); differences in ρ of about 0.1 are within noise.",
         "**No pressure and no direct inversion measure.** Surface pressure was not in the exported files; temperature range and stagnation are proxies.",
         "**Satellite fire detection.** VIIRS misses fires under thick cloud or fog and between its overpasses; counts are detections, not fires.",
         "**Simplifications.** Each city is one point, the cone uses one daily wind direction, one UTC+5 clock is used for India (IST is UTC+5:30), and observed weather stands in for forecast weather.",
         "**Dependence.** City-days are not independent (multi-day episodes, shared regional weather), so group comparisons and contingency p-values are descriptive."])
h1("6. Reproducibility and Deliverables")
p("The notebooks air_quality.ipynb (A), weather.ipynb (B), fire.ipynb (C) and merge_analysis.ipynb (Role 2) run top to bottom with Restart and Run All, in this order, "
  "from the project root, and keep all their printed outputs and figures. They share one settings file (src/config.py: cities, coordinates, dates, file names) and helper "
  "modules for the merge, the EDA and one figure style. Every setting is learned on the training period and saved, so the final run on 2024 only changes the dates in the "
  "settings file. The last cell of merge_analysis.ipynb writes the workbook Milestone2_Final_Master_and_EDA.xlsx: its first sheet is the master table (5,665 × 287), and "
  "its Contents sheet lists the other sheets (data dictionary, missing values for every column, decisions log, saved parameters, encoding example, the final table of each "
  "stream, and every EDA table of this report) together with the table or figure that uses each one.")
if M3:
    m3_reproducibility()
    m3_sections()

h2("References")
refs = ["Hersbach, H., et al. (2020). The ERA5 global reanalysis. Quarterly Journal of the Royal Meteorological Society, 146(730), 1999–2049.",
        "Inness, A., et al. (2019). The CAMS reanalysis of atmospheric composition. Atmospheric Chemistry and Physics, 19, 3515–3556.",
        "NASA (2024). Fire Information for Resource Management System (FIRMS), VIIRS 375 m active fire product. https://firms.modaps.eosdis.nasa.gov",
        "Schroeder, W., Oliva, P., Giglio, L., & Csiszar, I. A. (2014). The New VIIRS 375 m active fire detection data product: Algorithm description and initial assessment. Remote Sensing of Environment, 143, 85–96.",
        "Tukey, J. W. (1977). Exploratory Data Analysis. Addison-Wesley.",
        "Wickham, H. (2010). A layered grammar of graphics. Journal of Computational and Graphical Statistics, 19(1), 3–28.",
        "Wilson, E. B. (1927). Probable inference, the law of succession, and statistical inference. Journal of the American Statistical Association, 22(158), 209–212.",
        "World Health Organization (2021). WHO global air quality guidelines: particulate matter (PM2.5 and PM10), ozone, nitrogen dioxide, sulfur dioxide and carbon monoxide. Geneva: WHO.",
        "Zippenfenig, P. (2023). Open-Meteo.com Weather API [Computer software]. Zenodo. https://doi.org/10.5281/zenodo.7970649"]
if M3:
    refs = sorted(refs + M3_REFS, key=lambda r: r.lower())
blocks.append({"t": "refs", "items": refs})

OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps({"blocks": blocks}, ensure_ascii=False, indent=1), encoding="utf-8")
print(f"{OUT}: {len(blocks)} blocks, {counters['table']} tables, {counters['figure']} figures")
