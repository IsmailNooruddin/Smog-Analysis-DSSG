"""Builds the Milestone 4 manuscript as one research paper (JSON content model).

The Milestone 3 report appended new sections to the Milestone 2 report. This builder writes one paper
instead: introduction and related work, data, exploratory findings and hypotheses, methods, results,
fairness audit and mitigation, discussion (FATEN, living lab, policy), limitations, conclusion, APA
references and appendices. Every number comes from docs/tables/*.csv (merge_analysis.ipynb,
modeling.ipynb and advanced_modeling.ipynb write them) or from Dataset/clean/m4_params.json.

Run from the repository root, after advanced_modeling.ipynb:
    python docs/manuscript/build_manuscript_m4.py
    node docs/manuscript/render_docx.js 4
"""
import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
T = ROOT / "docs" / "tables"
OUT = ROOT / "docs" / "manuscript" / "manuscript_m4.json"

blocks = []
counters = {"table": 0, "figure": 0}


# ---------------------------------------------------------------------
# Block helpers (same content model as build_manuscript.py)
# ---------------------------------------------------------------------
def tab(name, **kw):
    return pd.read_csv(T / f"{name}.csv", **kw)


def h1(text):
    blocks.append({"t": "h1", "text": text})


def h2(text):
    blocks.append({"t": "h2", "text": text})


def p(text):
    blocks.append({"t": "p", "text": text})


def bullets(items):
    blocks.append({"t": "bullets", "items": items})


def table(caption, header, rows, widths, note=None, font=8):
    counters["table"] += 1
    blocks.append({"t": "table", "caption": f"**Table {counters['table']}.** {caption}", "header": header,
                   "rows": [[str(c) for c in r] for r in rows], "widths": widths, "note": note, "font": font})
    return counters["table"]


def figure(path, caption, width_in=6.3):
    counters["figure"] += 1
    blocks.append({"t": "figure", "path": str(ROOT / path), "caption": f"**Figure {counters['figure']}.** {caption}",
                   "width_in": width_in})
    return counters["figure"]


def f(x, d=2):
    """Number with thousands separators and a true minus sign; no '-0.00'."""
    out = f"{x:,.{d}f}"
    if out.startswith("-") and float(out.replace(",", "")) == 0:
        out = out[1:]
    return out.replace("-", "−")


def pct(x, d=1):
    return f(100 * x, d)


def ci(est, lo, hi, d=3):
    return f"{f(est, d)} [{f(lo, d)}, {f(hi, d)}]"


def pv(x):
    return "< 0.001" if x < 0.001 else f(x, 3)


# ---------------------------------------------------------------------
# Inputs
# ---------------------------------------------------------------------
m4 = json.loads((ROOT / "Dataset" / "clean" / "m4_params.json").read_text(encoding="utf-8"))
mv = tab("m4_metrics_validation").set_index(["model", "metric"])
mcv = tab("m4_metrics_cv", index_col=0)
cnt = tab("m4_validation_counts", index_col=0)
dl = tab("m4_deltas").set_index(["comparison", "metric"])
cc = tab("m4_cost_curve")
cw = cc.pivot(index="ratio", columns="model", values="cost_per_1000")
imp = tab("m4_importance").set_index(["model", "group"])
hyp = tab("m4_hypotheses").set_index(["hypothesis", "spec", "term"])
fg = tab("m4_fair_groups")
fd = tab("m4_fair_disparity").set_index(["model", "data", "grouping", "metric"])
mit = tab("m4_mitigation")
mitg = tab("m4_mitigation_groups")
par = tab("m4_pareto")
thc = tab("m4_threshold_curves")
grp = tab("m4_groups")
tun = {"rf": tab("m4_tuning_rf"), "hgb": tab("m4_tuning_hgb")}
leak = tab("m3_leakage_check").set_index(["model", "scheme"])
h2t = tab("m3_h2_logit", index_col=0)
hz = tab("m3_horizons").set_index(["horizon", "model"])
reg = tab("m3_index_regression").set_index(["name", "metric"])
cvf = tab("m3_cv_folds")
onset = tab("m3_errors_onset").set_index(["model", "outcome", "day_type"])["count"]
cvr = tab("cone_vs_radius", index_col=[0, 1])
lag = tab("lagged_fire_correlation")
wtr = tab("weather_trap_harvest")
mo = tab("groupby_month", index_col=0)
up_lag = lag[lag["setting"].str.startswith("Upwind")].set_index("lag_days")["median_rho"]
HEAD = "Training Oct-Dec (headline)"

LAB = {"lr_full": "LR full", "dt_full": "DT full", "rf_full": "RF full", "hgb_full": "HGB full"}
FINAL, BEST = LAB[m4["final_model"]], LAB[m4["best_ensemble"]]
OTHER = "HGB full" if BEST == "RF full" else "RF full"
T1, T2, T3 = "Tier 1 metro (≥ 3 M)", "Tier 2 large (1–3 M)", "Tier 3 small (< 1 M)"
TIERS = [T1, T2, T3]
TSHORT = {T1: "Tier 1 (metro)", T2: "Tier 2 (large)", T3: "Tier 3 (small)"}
VAL, OOF = "validation", "training OOF"
SPEC_A, SPEC_B = "A: Milestone 2 spec", "B: + today's index"
CONE, RAD, DOWN = "fire_cnt_up45_r300_all_log1p_z", "fire_cnt_r300_all_log1p_z", "fire_cnt_down45_r300_all_log1p_z"
IN, PKF = "fire_cnt_up45_r300_in_log1p_z", "fire_cnt_up45_r300_pk_log1p_z"
EPS = m4["fairness"]["eps_headline"]
PT = "threshold per tier, cost-optimal"


def V(model, metric, col="estimate"):
    return mv.loc[(model, metric), col]


def VCI(model, metric, d=3):
    return ci(V(model, metric), V(model, metric, "ci_low"), V(model, metric, "ci_high"), d)


def CV(model, metric):
    return mcv.loc[model, f"{metric}_mean"]


def D(comp, metric, col="validation_diff"):
    return dl.loc[(comp, metric), col]


def DCI(comp, metric, d=3):
    return ci(D(comp, metric), D(comp, metric, "ci_low"), D(comp, metric, "ci_high"), d)


def FG(model, data, grouping, group, metric):
    r = fg[(fg.model == model) & (fg.data == data) & (fg.grouping == grouping) & (fg.group == group)]
    return float(r[metric].iloc[0])


def FD(model, data, grouping, metric, col="estimate"):
    return float(fd.loc[(model, data, grouping, metric), col])


def FDCI(model, data, grouping, metric, d=3):
    return ci(FD(model, data, grouping, metric), FD(model, data, grouping, metric, "ci_low"),
              FD(model, data, grouping, metric, "ci_high"), d)


def MIT(model, method, data, metric):
    r = mit[(mit.model == model) & (mit.method.str.startswith(method)) & (mit.data == data)]
    return r[metric].iloc[0]


def MG(model, method, data, group, metric):
    r = mitg[(mitg.model == model) & (mitg.method.str.startswith(method)) & (mitg.data == data) & (mitg.group == group)]
    return float(r[metric].iloc[0])


def H(hid, spec, term, col):
    return float(hyp.loc[(hid, spec, term), col])


def be_ratio(model):
    cheaper = cw[model] < cw["Persistence"]
    return int(cheaper.idxmax()), int(cheaper.sum())


def best_row(fam, s="full"):
    t = tun[fam]
    return t[(t.feature_set == s) & (t["rank"] == 1)].iloc[0]


def rf_setting(s="full"):
    b = best_row("rf", s)
    depth = "no depth limit" if str(b.max_depth) == "none" else f"depth {int(float(b.max_depth))}"
    mf = "√p" if str(b.max_features) == "sqrt" else f"{float(b.max_features):g} of the columns"
    return f"{int(b.n_estimators)} trees, {depth}, min. leaf {int(b.min_samples_leaf)}, {mf} per split, class weight {b.class_weight}"


def hgb_setting(s="full"):
    b = best_row("hgb", s)
    depth = "no depth limit" if str(b.max_depth) == "none" else f"depth {int(float(b.max_depth))}"
    return (f"learning rate {f(float(b.learning_rate), 3)}, {int(b.max_iter)} rounds, {int(b.max_leaf_nodes)} leaves, {depth}, "
            f"min. leaf {int(b.min_samples_leaf)}, L2 {f(float(b.l2_regularization), 3)}, class weight {b.class_weight}")


# Frequently used numbers
be_lr, n_lr = be_ratio("LR full")
be_best, n_best = be_ratio(BEST)
fpr_lr = {t: FG("LR full", VAL, "city-size tier", t, "fpr") for t in TIERS}
fpr_pt = {t: MG("LR full", PT, VAL, t, "fpr") for t in TIERS}
tpr_lr = {t: FG("LR full", VAL, "city-size tier", t, "tpr") for t in TIERS}
base_v = {t: FG("LR full", VAL, "city-size tier", t, "base_rate") for t in TIERS}
cost_single_v, cost_pt_v = MIT("LR full", "none", VAL, "cost_per_1000"), MIT("LR full", PT, VAL, "cost_per_1000")
ens_better = (V(BEST, "pr_auc") > V("LR full", "pr_auc"))
h1_p = H("H1", SPEC_A, CONE, "p_one_sided_city")
h3_b = H("H3", SPEC_A, "cone_x_stagnant", "coef")
h4_p = H("H4", SPEC_A, IN, "p_one_sided_city")
assert FINAL == "LR full", "the text below assumes LR full is the final model; rewrite Sections 6–7 otherwise"
assert not ens_better, "the text below assumes the ensembles do not beat LR full on validation PR-AUC"


# =====================================================================
# Front matter
# =====================================================================
blocks.append({"t": "title", "text": "Forecasting Trans-Boundary Smog Spikes in Punjab: Crop Fires, Weather Traps and a Geographic Fairness Audit"})
blocks.append({"t": "authors", "text": "Munir Tariq (10067)  |  Ismail Nooruddin (09958)  |  Bilal Ayub (09716)  |  "
                                         "Data Science for Social Good, Habib University  |  November 2026"})
blocks.append({"t": "abstract", "items": [
    "**Background.** Each winter, crop-fire smoke and city emissions collect over the Punjab plain shared by Pakistan and India. "
    "We ask whether upwind fires and weather traps forecast next-day smog spikes in 11 cities, and whether the alert treats large and small cities alike.",
    "**Data and methods.** We merged CAMS air quality, weather and 1.28 million VIIRS fire detections into 5,665 city-days (August 2022 to December 2023). "
    "A spike is a day above the city's 90th percentile of a Composite Smog Index. We compared persistence, logistic regression (LR), a decision tree, a random forest and gradient boosting. "
    "We tuned every model on purged, week-grouped cross-validation and tested it on September–December 2023. "
    "We audited the alerts by country, city and census city-size tier, and tested reweighing and tier-specific thresholds.",
    f"**Results.** A sparse LR on today's index margin and temperature ranks spikes as well as persistence (PR-AUC {f(V('LR full', 'pr_auc'), 3)} against "
    f"{f(V('Persistence', 'pr_auc'), 3)}). The ensembles do not improve on it (random forest {f(V('RF full', 'pr_auc'), 3)}, gradient boosting {f(V('HGB full', 'pr_auc'), 3)}). "
    f"The LR alert is cheaper than persistence whenever a missed spike costs at least {be_lr} false alarms. "
    "Upwind-cone fires track next-day smog but add no forecast skill once today's smog is known.",
    f"**Fairness.** Error rates are similar in Pakistan and India. Small cities bear more false alarms: {pct(fpr_lr[T3])}% of their clean days against {pct(fpr_lr[T1])}% in metros. "
    f"Tier-specific thresholds, chosen on training data, cut that rate to {pct(fpr_pt[T3])}% and the cost per 1,000 city-days from {f(cost_single_v, 1)} to {f(cost_pt_v, 1)}.",
    "**Conclusion.** A transparent next-day alert is feasible, with tier-specific thresholds, human review and a pilot first.",
]})
blocks.append({"t": "keywords", "text": "air pollution; early warning; crop-residue burning; cross-validation; asymmetric costs; algorithmic fairness; Punjab"})

# =====================================================================
# 1. Introduction
# =====================================================================
h1("1. Introduction")
p("Every October and November, farmers in Indian and Pakistani Punjab burn rice stubble to clear fields for wheat. "
  "The smoke joins city emissions under cold, still winter air. Fine-particle levels in Lahore, Faisalabad and the Indian Punjab cities then rise far above the "
  "WHO 24-hour guideline of 15 µg/m³ (World Health Organization, 2021). "
  "Governments respond with school closures, traffic limits and kiln bans (Environment Protection Department, n.d.; Waqar & Gabol, 2024). "
  "These measures need warning, and the warning must be right.")
p("Two features of the problem shape this study. First, smoke crosses the border, so a city's air depends on fires it does not control. "
  "Second, an alert has two kinds of error with unequal costs. A missed spike leaves children, the elderly and outdoor workers exposed. "
  "A false alarm closes schools and stops daily-wage work for nothing. Both costs fall on people, and they may fall unevenly across places.")
p("**Research questions.**")
bullets(["**RQ1.** Which fire and weather predictors, known on day *t*, explain smog spikes on day *t* + 1?",
         "**RQ2.** How much better than persistence (\"tomorrow repeats today\") can baseline and ensemble models forecast those spikes, at what error cost?",
         "**RQ3.** Does the alert treat countries, cities and city-size tiers fairly, and what does mitigation cost?"])
p("**Contributions.**")
bullets(["A merged, audited city-day dataset of air quality, weather and wind-aware fire counts for 11 cities on both sides of the border (Section 3).",
         "A leakage-free evaluation: purged, week-grouped, stratified cross-validation and an out-of-time test season (Section 5).",
         "A comparison of six models against persistence on ranking, calibration and asymmetric cost (Section 6).",
         "Tests of five hypotheses on fires, weather traps and cross-border smoke (Section 6.4).",
         "A geographic fairness audit with census city-size tiers, bias mitigation and a fairness–accuracy Pareto frontier (Sections 6.5–6.6).",
         "A FATEN evaluation and a living-lab deployment plan for Punjab's smog response (Section 7)."])
p("The work serves SDG 3 (targets 3.9 and 3.d: illness from air pollution and early warning), SDG 11 (target 11.6: urban air quality) and SDG 13 (climate action). "
  "The cross-border question also relates to SDG 17 (cooperation between countries).")

# =====================================================================
# 2. Related work
# =====================================================================
h1("2. Related Work")
p("**Crop burning and Punjab smog.** Satellite studies link post-monsoon residue fires in northwest India to winter air pollution downwind. "
  "Cusworth et al. (2018) used an atmospheric model to attribute part of Delhi's particulate pollution to agricultural fires in Punjab and Haryana. "
  "Jethva et al. (2019) connected rising crop productivity, residue fires and aerosol loads over northern India. "
  "Tariq et al. (2015) described the optical properties of aerosols over Lahore during a residue-burning episode. "
  "These studies explain where smoke comes from. They do not test whether fire counts add skill to a city-level, next-day alert beyond today's air quality.")
p("**Machine-learning forecasts of air quality.** Rybarczyk and Zalakeviciute (2018) reviewed machine-learning models of outdoor air quality and found ensembles and neural networks common. "
  "Many such studies score models with random splits. Roberts et al. (2017) showed that random splits of temporally structured data overstate skill. "
  "They recommended blocked cross-validation instead. "
  "For rare events, the precision–recall curve is more informative than the ROC curve (Saito & Rehmsmeier, 2015). "
  "We follow both recommendations and benchmark every model against persistence.")
p("**Fairness of predictive alerts.** Group-fairness criteria compare error rates or positive rates across groups. "
  "Feldman et al. (2015) formalised the disparate impact ratio and the 80% rule. Hardt et al. (2016) defined equalized odds and equal opportunity. "
  "They also showed how group-specific thresholds can enforce them after training. "
  "Kamiran and Calders (2012) proposed reweighing as a pre-processing step. "
  "Chouldechova (2017) showed that calibration and equal error rates cannot all hold when base rates differ. "
  "Mehrabi et al. (2021) survey these definitions. Most fairness audits study people grouped by gender or race. "
  "We apply the same criteria to places, where the sensitive attribute is geography and city size.")

# =====================================================================
# 3. Data
# =====================================================================
h1("3. Study Area and Data")
h2("3.1 Sources, alignment and merge")
p("The study covers 11 cities: Lahore, Faisalabad, Multan, Rawalpindi, Sialkot, Rahim Yar Khan and Islamabad in Pakistan, and Amritsar, Ferozepur, Ludhiana and Jalandhar in India (Figure 1). "
  "Each team member collected and cleaned one data stream (Table 1). "
  "Air quality comes from the CAMS model (Inness et al., 2019) through the Open-Meteo API (Zippenfenig, 2023), which also supplies the weather. "
  "Fire detections come from the VIIRS 375 m product (Schroeder et al., 2014) through NASA FIRMS (NASA, 2024). "
  "Air quality and weather are gridded model estimates, not monitor readings. They suit comparisons between days and cities.")
table("Data streams, from raw records to the master table. Full row bookkeeping and preprocessing decisions are in Appendix A.",
      ["Stream", "Source", "Raw records", "Main processing", "Daily output"],
      [["Air quality", "Open-Meteo Air Quality API (CAMS model output, about 0.4° grid), hourly", "453,192 hourly rows",
        "Kept 2022–2023; no pollutant values before 4 Aug 2022, so that block was not imputed; days with ≥ 18 valid hours", "5,665 city-days"],
       ["Weather", "Open-Meteo Historical Weather API, hourly", "433,728 hourly rows",
        "Daily mean, total, range and vector-mean wind; stagnant = vector wind < 2 km/h; rain day ≥ 1 mm", "7,852 city-days"],
       ["Fire", "NASA FIRMS, VIIRS 375 m (NOAA-20), point detections", "1,284,773 detections",
        "Study box, vegetation fires, nominal or high confidence: 238,756 detections; counts by cone, radius and country of origin", "8,030 city-days"],
       ["Master", "Left joins on city, country and date", "–",
        "Calendar of 11 cities × 515 days; lags and targets within each city; 2024 sealed for a later out-of-time test", "5,665 × 287"]],
      [1050, 2200, 1250, 4000, 1292])
p("All raw times are in GMT. Each stream added five hours before taking the date, so evening hours fall on the correct local day. "
  "The same UTC+5 clock was used for the Indian cities, so all streams share day boundaries. "
  "The merge started from an empty calendar, and every join kept all 5,665 rows. "
  "The window runs from 4 August 2022 to 31 December 2023, because the air-quality source has no earlier values.")
figure("figures/fig_fire_study_area.png",
       "Study area and crop-fire detections (VIIRS NOAA-20, vegetation fires, nominal or high confidence), October–November 2023. "
       "Blue = India-origin, orange = Pakistan-origin. The circle is the 150 km radius around Lahore. The wedges are the ±30°, ±45° and ±60° upwind cones for Lahore's wind on 29 October 2023.", 4.1)
h2("3.2 Target: the Composite Smog Index and the spike label")
p("The **Composite Smog Index** combines six pollutants: 0.40·z(PM2.5) + 0.12·[z(PM10) + z(NO2) + z(SO2) + z(O3) + z(CO)]. "
  "Skewed pollutants enter after log(1 + x). The z-scores use the training period only. "
  "A **spike** is a day whose index reaches the 90th percentile of that city's training October–March days. "
  "The city thresholds run from 0.36 (Rahim Yar Khan) to 2.18 (Lahore). The window holds 297 spike city-days (5.2%). "
  "Because each city has its own threshold, every city has about the same spike rate in the training winter by design.")
h2("3.3 Predictors")
bullets(["**AQ history:** today's index and the two previous days, entered as the **margin** over the city threshold (index − threshold). A margin of 0 or more means a spike day.",
         "**Upwind fires:** detections inside a ±45° cone around the direction the daily wind comes from, within 300 km, on day *t* and lags 1–3. "
         "The setting was chosen on the training harvest season only. Counts are split by country of origin.",
         "**Weather:** stagnant air today and yesterday, humidity, rain day, temperature range, vector-mean wind, mean temperature and 7 wind sectors.",
         "**Calendar and place:** 11 month dummies (January reference) and 10 city dummies (Lahore reference)."])
p("The **full** feature set has 42 columns. The **no-fire** set drops the four fire columns (38). The **weather-only** set also drops AQ history (35). "
  "Comparing the sets tests whether fires add skill.")

# =====================================================================
# 4. Exploratory findings and hypotheses
# =====================================================================
h1("4. Exploratory Findings and Hypotheses")
p(f"Spikes cluster in December ({f(mo.loc[12, 'spike_share_pct'], 1)}% of training city-days) and January ({f(mo.loc[1, 'spike_share_pct'], 1)}%). "
  f"October and November have {f(mo.loc[10, 'spike_share_pct'], 1)}% and {f(mo.loc[11, 'spike_share_pct'], 1)}%, although fires peak then (Figure 2). "
  "The wheat-burning season of May 2023 produced no spike. Fires alone therefore do not make a spike. Winter weather must trap the smoke.")
figure("figures/fig_a3_index_over_time.png",
       "Composite Smog Index over time (7-day centred average; 0 = average training day) for Lahore, Faisalabad, Rahim Yar Khan and Amritsar. "
       "Grey bands mark October–December. Dashed and dotted lines mark the end of training and the start of validation. "
       "The break in December 2022 is four flagged days with near-zero pollutants in every city.", 5.6)
hv = cvr.loc[(HEAD, "All Pakistani (7)")]
p(f"**Fires.** In the training harvest season, fires in the ±45° upwind cone at 300 km correlate with next-day smog (median Spearman ρ = {f(hv['upwind cone (up45, 300 km)'])} over the Pakistani cities). "
  f"The plain 300 km circle gives {f(hv['no cone (300 km)'])} and a downwind placebo cone {f(hv['downwind placebo (down45, 300 km)'])}. "
  f"The association peaks one day after the fires (ρ = {f(up_lag[1])}, against {f(up_lag[0])} on the same day).")
st, hu, rf_, comb = wtr.iloc[0], wtr.iloc[1], wtr.iloc[2], wtr.iloc[5]
p(f"**Weather traps.** In the training harvest season, {f(st['spike_rate_with_pct'], 1)}% of days after a stagnant day were spikes, against {f(st['spike_rate_without_pct'], 1)}% otherwise (Figure 3). "
  f"Humid days gave {f(hu['spike_rate_with_pct'], 1)}% against {f(hu['spike_rate_without_pct'], 1)}%. No rain day was followed by a spike (0 of {int(rf_['days_without'])}). "
  f"When stagnation, humidity and no rain coincided, {f(comb['spike_rate_with_pct'], 0)}% of next days were spikes. "
  "A large day–night temperature range marks the clear, calm nights on which surface inversions form.")
figure("figures/fig_m6_weather_trap.png",
       "Share of next days that are smog spikes when today has each weather condition (filled circles, 95% Wilson intervals) and on all other days (hollow diamonds), "
       "training harvest season. Dashed line: rate over all harvest days.", 5.2)
p("These patterns led to five hypotheses (Table 2). Each uses only information known on day *t*.")
table("Hypotheses and their tests. Index = Composite Smog Index on day t + 1. Controls: month and city dummies, mean temperature, temperature range, humidity, rain total and vector-mean wind.",
      ["ID", "Hypothesis (H1 form)", "Test"],
      [["H1 Cone vs radius", "Fires in the upwind cone raise the next-day index beyond the plain 300 km count (β_cone > 0).", "OLS with controls, city-clustered SE; downwind placebo"],
       ["H2 Weather trap", "Stagnation, humidity, no rain and a large temperature range each raise the odds of a spike (OR > 1).", "Logit on rain-free Sep–Feb days, city-clustered SE; Fisher exact test for rain"],
       ["H3 Fire × stagnation", "The fire effect is stronger on stagnant days (β_fire×stagnant > 0).", "OLS with an interaction term"],
       ["H4 Cross-border", "In Pakistani cities, India-origin fires raise the next-day index, more near the border (β_IN > 0, β_IN×near > 0).", "OLS on the 7 Pakistani cities with Pakistan-origin fires as a control"],
       ["H5 Forecast value", "A model with fire and weather features beats persistence and a weather-only model.", "Validation PR-AUC and cost; paired week-block bootstrap"]],
      [1700, 4900, 3192])

# =====================================================================
# 5. Methods
# =====================================================================
h1("5. Methods")
h2("5.1 Split and leakage-free validation")
p("The outer split is chronological. Training runs from 6 August 2022 to 31 August 2023 (4,246 city-days, 204 spikes, 4.80%). "
  "After a three-day gap, validation runs from 4 September to 30 December 2023 (1,298 city-days, 89 spikes, 6.86%). "
  "We dropped 55 training rows whose feature or target day falls on the four flagged days. "
  "Validation is an out-of-time test: we fit, tune, weight and threshold nothing on it. The 2024 data stay sealed for a later test.")
p(f"Inside training we use purged, repeated **StratifiedGroupKFold**: 5 folds × 5 repeats = 25 folds. "
  "The group is the calendar week shared by all cities, so a week never sits on both sides of a split. "
  "Stratification gives each fold its share of spikes. "
  "The **purge** drops fit rows whose target day is held out. The **embargo** drops fit rows up to three days after a held-out day, because their AQ history contains that day's index. "
  f"Each fold holds out {int(cvf['test rows'].min())}–{int(cvf['test rows'].max())} city-days, and the purge and embargo remove {int(cvf['purged/embargoed rows'].min())}–{int(cvf['purged/embargoed rows'].max())} fit rows. "
  f"The test-fold spike rate averages {f(cvf['test spike rate (%)'].mean())}% (range {f(cvf['test spike rate (%)'].min())}–{f(cvf['test spike rate (%)'].max())}%). Figure 11 (Appendix B) shows the fold layout.")
la = leak.loc[("LR full", "(a) random stratified 80/20 split"), "pr_auc_mean"]
lb = leak.loc[("LR full", "(b) StratifiedKFold(5, shuffle), no groups"), "pr_auc_mean"]
ld = leak.loc[("LR full", "(d) purged + embargoed 5 × 5 StratifiedGroupKFold (ours)"), "pr_auc_mean"]
da = leak.loc[("DT full", "(a) random stratified 80/20 split"), "pr_auc_mean"]
dd = leak.loc[("DT full", "(d) purged + embargoed 5 × 5 StratifiedGroupKFold (ours)"), "pr_auc_mean"]
p(f"A leakage check shows why this design matters. On the same training rows, a random stratified 80/20 split scores LR at PR-AUC {f(la, 3)}, plain stratified K-fold at {f(lb, 3)}, and our design at {f(ld, 3)}. "
  f"For the decision tree the gap is larger ({f(da, 3)} against {f(dd, 3)}). Random splits put near-copies of neighbouring days on both sides and overstate skill.")
h2("5.2 Models and hyperparameter search")
p("Table 3 lists the models. The majority class and persistence are naive benchmarks. "
  "Logistic regression (LR) and a decision tree (DT) are the Milestone 3 baselines, reloaded unchanged. "
  "The random forest (RF; Breiman, 2001) and histogram gradient boosting (HGB; Friedman, 2001; Ke et al., 2017) are the advanced models. "
  "Both ensembles capture interactions, such as fire × stagnation, that an additive LR cannot.")
p("LR and DT were tuned by grid search. RF and HGB were tuned by random search with 60 draws per feature set (Bergstra & Bengio, 2012). "
  "Every search used the same 25 purged folds and scored PR-AUC. Every transform sits inside the pipeline, so each fold re-learns it. "
  "We used scikit-learn (Pedregosa et al., 2011) for the models and statsmodels (Seabold & Perktold, 2010) for the regressions. "
  "HGB's built-in early stopping holds out a random 10% of rows, which would leak neighbouring days. We switched it off and tuned the number of rounds instead. "
  "The final model was fixed before validation: the highest CV PR-AUC among the full-feature models, with ties within 0.005 going to the simpler model.")
table("Models, search spaces and selected settings (full feature set). CV PR-AUC = mean over the 25 purged folds.",
      ["Model", "Role", "Search space", "Selected setting", "CV PR-AUC"],
      [["Majority class", "Floor", "–", "Always \"no spike\"", "–"],
       ["Persistence", "Benchmark", "–", "Alert when today is a spike", f(CV("Persistence", "pr_auc"), 3)],
       ["Logistic regression (LR)", "Baseline", "C 0.001–100 (8 values), L1 or L2, class weight none/balanced; grid (32)", "C = 0.027, L1, no class weight", f(CV("LR full", "pr_auc"), 3)],
       ["Decision tree (DT)", "Baseline", "Depth 2–8, min. leaf 10/25/50/100, class weight; grid (56)", "Depth 4, min. leaf 50, no class weight", f(CV("DT full", "pr_auc"), 3)],
       ["Random forest (RF)", "Advanced", "Trees 300/500, depth 3–12 or none, min. leaf 5–100, features per split √p–1.0, class weight; random (60)", rf_setting(), f(CV("RF full", "pr_auc"), 3)],
       ["Gradient boosting (HGB)", "Advanced", "Learning rate 0.01–0.3, rounds 100–600, leaves 7–63, depth, min. leaf 10–100, L2 0.001–10, class weight; random (60)", hgb_setting(), f(CV("HGB full", "pr_auc"), 3)]],
      [1600, 900, 3300, 2992, 1000])
h2("5.3 Metrics and asymmetric costs")
p("We report accuracy, precision, recall, specificity, F1, ROC-AUC, PR-AUC and the Brier score. "
  "Validation CIs come from a block bootstrap that resamples whole weeks (1,000 resamples). Paired differences use the same resampled weeks.")
p("A missed spike leaves people unprotected. A false alarm costs a day of closures and erodes trust. "
  "We weight a missed spike as five false alarms (FN:FP = 5:1). This ratio is a stated policy assumption, not an estimate. "
  "Air pollution caused 1.67 million deaths in India in 2019 and cost 1.36% of GDP (Pandey et al., 2021), so the health side is heavy. "
  "Each model's alert threshold minimises 5·FN + FP on its out-of-fold training predictions. "
  "Because the ratio is uncertain, we also report the **break-even ratio**: the smallest ratio at which a model alert is cheaper than persistence.")
h2("5.4 Fairness audit design")
p("Our units are places, not people. The sensitive attribute is therefore **geography**, as agreed with the course instructor. We use three groupings:")
bullets(["**Country:** Pakistan (7 cities) against India (4 cities). The border is the political divide that cross-border smoke crosses.",
         "**City-size tier,** a socio-economic proxy from census population (city including cantonments): Tier 1 metro ≥ 3 million, Tier 2 large 1–3 million, Tier 3 small < 1 million (Table 4). "
         "Small cities have fewer monitors, less media attention and less administrative capacity.",
         "**City (11):** reported descriptively, because each city has 0–22 validation spikes."])
grp_sorted = grp.sort_values(["tier", "population"], ascending=[True, False])
table("Sensitive groups: census population and city-size tier. Pakistan: 2023 census (Pakistan Bureau of Statistics, 2025). India: 2011 census, the latest held. Spikes = spike days in training and validation.",
      ["City", "Country", "Census", "Population", "Tier", "Spike threshold", "Training spikes", "Validation spikes"],
      [[r.city, "Pakistan" if r.country == "PK" else "India", int(r.census_year), f"{int(r.population):,}", TSHORT[r.tier],
        f(r.spike_threshold), int(r.train_spikes), int(r.val_spikes)] for r in grp_sorted.itertuples()],
      [1500, 900, 800, 1300, 1500, 1200, 1200, 1392],
      note="Tier rule fixed before any fairness result. Jalandhar (0.92 million in 2011) has probably passed 1 million since. "
           "Islamabad and Rawalpindi share one air-quality grid cell but fall in different tiers.")
p("The positive prediction is an **alert**. For each group we compute the alert (selection) rate, the true-positive rate (TPR, recall) and the false-positive rate (FPR, false alarms on clean days). From these we derive:")
bullets(["**Disparate impact ratio (DIR):** a group's alert rate divided by the reference group's. The reference groups are Pakistan, Tier 1 metros and Lahore. "
         "We read the 80% rule two-sided (0.8–1.25), because an alert both protects and costs.",
         "**Equal opportunity:** the largest TPR gap between groups.",
         "**Predictive equality:** the largest FPR gap between groups.",
         "**Equalized odds difference:** the larger of the two gaps.",
         "**Demographic parity difference:** the largest gap in alert rates."])
p("We audit twice. Validation (89 spikes) is the honest test. The out-of-fold training predictions (204 spikes, same thresholds) give a second, larger sample. "
  "Gap CIs come from the week-block bootstrap.")
h2("5.5 Bias mitigation")
p(f"Mitigation targets the city-size tier. Every choice uses out-of-fold training predictions only.")
bullets(["**Pre-processing, reweighing** (Kamiran & Calders, 2012): each training row gets the weight P(tier)·P(label)/P(tier, label), computed inside each fold from its fit rows.",
         "**Post-processing, per-tier cost-optimal thresholds:** each tier gets its own 5:1 threshold. This is asymmetric threshold tuning per group.",
         f"**Post-processing, predictive-equality thresholds:** tier thresholds that minimise total cost while every tier's FPR stays within ±ε/2 of a common value (headline ε = {f(EPS)}).",
         "**Post-processing, equalized-odds thresholds** (Hardt et al., 2016): the same band on both FPR and TPR."])
p("To map the fairness–accuracy trade-off, we sweep ε from 0.01 to 0.20 and the reweighing strength α from 0 to 1. "
  "A rule is **Pareto-efficient** when no other rule is both cheaper and fairer.")
h2("5.6 Hypothesis tests")
p("H1, H3 and H4 use OLS regressions of the next-day index on training rows, with city-clustered standard errors and a week-clustered check. "
  "Specification A follows the Milestone 2 plan. Specification B adds today's index, so it asks whether fires matter beyond today's smog. "
  "H2 uses a Logit of the spike label on rain-free September–February days, because no rain day and no March–August day preceded a spike. "
  "Rain is tested with Fisher's exact test. H5 compares forecasts on validation.")

# =====================================================================
# 6. Results
# =====================================================================
h1("6. Results")
h2("6.1 Advanced models against the baselines")
SHOWM = ["Majority class", "Persistence", "LR full", "DT full", "RF full", "HGB full"]
rows = []
for m in SHOWM:
    rows.append([m, f(V(m, "accuracy"), 3), "–" if pd.isna(V(m, "precision")) else f(V(m, "precision"), 3), f(V(m, "recall"), 3),
                 f(V(m, "specificity"), 3), f(V(m, "f1"), 3), "–" if pd.isna(V(m, "roc_auc")) else f(V(m, "roc_auc"), 3),
                 "–" if pd.isna(V(m, "pr_auc")) else VCI(m, "pr_auc"), "–" if pd.isna(V(m, "brier")) else f(V(m, "brier"), 3),
                 f(V(m, "cost_per_1000"), 1), "–" if pd.isna(CV(m, "pr_auc")) else f(CV(m, "pr_auc"), 3)])
table("Validation metrics (Sep–Dec 2023, 1,298 city-days, 89 spikes) at each model's 5:1 threshold, and cross-validated PR-AUC. "
      "PR-AUC with a 95% week-block bootstrap CI. Cost = (5·FN + FP) per 1,000 city-days. All model variants are in Appendix B.",
      ["Model", "Accuracy", "Precision", "Recall", "Specificity", "F1", "ROC-AUC", "PR-AUC [95% CI]", "Brier", "Cost", "CV PR-AUC"],
      rows, [1250, 750, 800, 700, 850, 650, 750, 1500, 650, 650, 842], font=7)
p(f"**The ensembles do not beat logistic regression.** {BEST} reaches a validation PR-AUC of {f(V(BEST, 'pr_auc'), 3)} and {OTHER} {f(V(OTHER, 'pr_auc'), 3)}, "
  f"against {f(V('LR full', 'pr_auc'), 3)} for LR full (Table 5). "
  f"The paired difference {BEST} − LR full is {DCI(f'{BEST} − LR full', 'pr_auc')}, and {BEST} beats LR in {int(D(f'{BEST} − LR full', 'pr_auc', 'cv_folds_a_better'))} of 25 CV folds. "
  f"Both ensembles do beat the decision tree on CV PR-AUC ({f(CV('RF full', 'pr_auc'), 3)} and {f(CV('HGB full', 'pr_auc'), 3)} against {f(CV('DT full', 'pr_auc'), 3)}). "
  f"Under the pre-registered rule, LR full stays the final model.")
p(f"**Accuracy misleads.** The majority class scores {pct(V('Majority class', 'accuracy'))}% accuracy and catches no spike. "
  f"**Persistence is hard to beat.** LR full ranks spikes slightly better (ΔROC-AUC {DCI('LR full − Persistence', 'roc_auc', 4)}), "
  f"but its PR-AUC gain ({DCI('LR full − Persistence', 'pr_auc')}) has a CI that includes 0. "
  f"The gain sits in the alert: LR full warns of {int(cnt.loc['LR full', 'tp'])} of 89 spikes, against {int(cnt.loc['Persistence', 'tp'])} for persistence. "
  f"It catches {int(onset.loc[('LR full', 'TP', 'onset')])} of the {int(onset.loc[('Persistence', 'FN', 'onset')])} onset days, the first day of an episode, which persistence misses by construction.")
p(f"**Calibration.** LR and RF have similar Brier scores ({f(V('LR full', 'brier'), 3)} and {f(V('RF full', 'brier'), 3)}). "
  f"HGB scores worse ({f(V('HGB full', 'brier'), 3)}). Its search chose balanced class weights, which push every predicted probability upwards "
  f"(its 5:1 threshold is {f(m4['models']['hgb_full']['threshold'], 3)}, against {f(m4['models']['rf_full']['threshold'], 3)} for RF). "
  "Figure 4C shows the reliability curves. "
  "Thresholds come from out-of-fold predictions, so calibration does not change the alerts. It matters only if officials read a probability at face value.")
figure("figures/fig_m04_2_roc_pr_calibration.png",
       "Validation ROC (A), precision–recall (B) and reliability (C) curves for persistence and the four full-feature models. "
       "Dots mark the operating points at the 5:1 thresholds. Numbers in the legends are ROC-AUC, PR-AUC and Brier score.", 6.6)
h2("6.2 Asymmetric costs")
p(f"At 5:1, never alerting costs {f(V('Majority class', 'cost_per_1000'), 1)} per 1,000 city-days. "
  f"Persistence costs {f(cw.loc[5, 'Persistence'], 1)}, LR full {f(cw.loc[5, 'LR full'], 1)}, {BEST} {f(cw.loc[5, BEST], 1)} and DT full {f(cw.loc[5, 'DT full'], 1)} (Figure 5). "
  f"LR full is cheaper than persistence at {n_lr} of the 20 ratios, from {be_lr}:1 upwards. {BEST} breaks even at {be_best}:1. "
  f"At 20:1 the gap widens: LR full costs {f(cw.loc[20, 'LR full'], 1)} against {f(cw.loc[20, 'Persistence'], 1)} for persistence. "
  f"The price is more false alarms: {pct(cnt.loc['LR full', 'fp'] / (cnt.loc['LR full', 'fp'] + cnt.loc['LR full', 'tn']))}% of clean days for LR full, "
  f"against {pct(cnt.loc['Persistence', 'fp'] / (cnt.loc['Persistence', 'fp'] + cnt.loc['Persistence', 'tn']))}% for persistence.")
figure("figures/fig_m04_3_cost_curve.png",
       "Expected validation cost per 1,000 city-days against the FN:FP cost ratio. Thresholds are re-chosen on out-of-fold training predictions at each ratio. "
       "Dotted grey: never alert. Dashed vertical line: the 5:1 headline.", 4.8)
h2("6.3 Drivers and the fire question")
aq = {m: imp.loc[(m, "AQ history (today, lags 1–2)"), "mean"] for m in ["LR full", "RF full", "HGB full"]}
fire_imp = {m: imp.loc[(m, "Upwind fires (t, lags 1–3)"), "mean"] for m in ["LR full", "RF full", "HGB full"]}
tm = {m: imp.loc[(m, "Mean temperature"), "mean"] for m in ["LR full", "RF full", "HGB full"]}
p(f"**AQ history drives every model** (Figure 6). Shuffling it costs {f(aq['LR full'], 3)} of validation PR-AUC for LR, {f(aq['RF full'], 3)} for RF and {f(aq['HGB full'], 3)} for HGB. "
  f"Mean temperature comes second for LR ({f(tm['LR full'], 3)}). Shuffling the fire columns costs at most {f(max(fire_imp.values()), 3)}. "
  "The L1 penalty of LR full keeps only two of 42 columns. Today's margin has an odds ratio of 10.9 per SD. "
  "Mean temperature has 0.70 per SD, so colder days raise the risk.")
p(f"**Fires add no consistent next-day skill, even to the ensembles.** RF full − RF no-fire gives ΔPR-AUC {DCI('RF full − RF no-fire', 'pr_auc')} on validation, "
  f"but the full model wins only {int(D('RF full − RF no-fire', 'pr_auc', 'cv_folds_a_better'))} of 25 CV folds. "
  f"HGB full − HGB no-fire gives {DCI('HGB full − HGB no-fire', 'pr_auc')} and wins {int(D('HGB full − HGB no-fire', 'pr_auc', 'cv_folds_a_better'))} folds. "
  f"The fire columns do lower the 5:1 validation cost of both ensembles (RF {ci(D('RF full − RF no-fire', 'cost'), D('RF full − RF no-fire', 'cost', 'ci_low'), D('RF full − RF no-fire', 'cost', 'ci_high'), 1)}, "
  f"HGB {ci(D('HGB full − HGB no-fire', 'cost'), D('HGB full − HGB no-fire', 'cost', 'ci_low'), D('HGB full − HGB no-fire', 'cost', 'ci_high'), 1)}). "
  f"For RF this means {int(cnt.loc['RF no-fire', 'fp'] - cnt.loc['RF full', 'fp'])} fewer false alarms in one season, and CV does not confirm a ranking gain. "
  f"AQ history matters instead: RF no-fire − RF weather-only gives {DCI('RF no-fire − RF weather-only', 'pr_auc')}, better in all 25 folds. "
  "This does not mean fires do not cause smog. Whatever smoke they add is already in today's index.")
figure("figures/fig_m04_4_importance.png",
       "Grouped permutation importance on validation: drop in PR-AUC when all columns of a group are shuffled together (±1 SD over 30 repeats), for LR, RF and HGB on the full feature set.", 5.4)
h2("6.4 Hypotheses")
fisher_p = h2t.loc["rain_day (Fisher exact, all train rows)", "p_one_sided_city"]
rows = [
    ["H1 Cone vs radius", f"β_cone = {f(H('H1', SPEC_A, CONE, 'coef'), 3)} [{f(H('H1', SPEC_A, CONE, 'ci_low_city'), 3)}, {f(H('H1', SPEC_A, CONE, 'ci_high_city'), 3)}], one-sided p = {pv(h1_p)}; "
     f"with today's index {f(H('H1', SPEC_B, CONE, 'coef'), 3)}, p = {pv(H('H1', SPEC_B, CONE, 'p_one_sided_city'))}. Placebo cone {f(H('H1 placebo', SPEC_A, DOWN, 'coef'), 3)}, p = {pv(H('H1 placebo', SPEC_A, DOWN, 'p_one_sided_city'))}",
     "Supported" if h1_p < 0.05 else "Not supported"],
    ["H2 Weather trap", f"Stagnant OR {f(h2t.loc['stagnant', 'odds_ratio'])} [{f(h2t.loc['stagnant', 'or_ci_low_city'])}, {f(h2t.loc['stagnant', 'or_ci_high_city'])}]; "
     f"humidity {f(h2t.loc['rh_mean_pct_sd', 'odds_ratio'])} per SD; temperature range {f(h2t.loc['temp_range_c_sd', 'odds_ratio'])} per SD; rain: 0 of 1,057 rain days preceded a spike (Fisher p {'< 0.001' if fisher_p < 0.001 else f(fisher_p, 3)})",
     "Supported"],
    ["H3 Fire × stagnation", f"β_interaction = {f(h3_b, 3)} [{f(H('H3', SPEC_A, 'cone_x_stagnant', 'ci_low_city'), 3)}, {f(H('H3', SPEC_A, 'cone_x_stagnant', 'ci_high_city'), 3)}]; "
     f"with today's index {f(H('H3', SPEC_B, 'cone_x_stagnant', 'coef'), 3)}", "Not supported" if H("H3", SPEC_A, "cone_x_stagnant", "p_one_sided_city") >= 0.05 else "Supported"],
    ["H4 Cross-border", f"β_IN = {f(H('H4', SPEC_A, IN, 'coef'), 3)}, p = {pv(h4_p)}; β_IN×near = {f(H('H4', SPEC_A, 'in_x_near', 'coef'), 3)}, p = {pv(H('H4', SPEC_A, 'in_x_near', 'p_one_sided_city'))}; "
     f"Pakistan-origin fires {f(H('H4', SPEC_A, PKF, 'coef'), 3)} [{f(H('H4', SPEC_A, PKF, 'ci_low_city'), 3)}, {f(H('H4', SPEC_A, PKF, 'ci_high_city'), 3)}]",
     "Not supported" if h4_p >= 0.05 else "Supported"],
    ["H5 Forecast value", f"LR full − persistence: ΔPR-AUC {DCI('LR full − Persistence', 'pr_auc')}, ΔROC-AUC {DCI('LR full − Persistence', 'roc_auc', 4)}; cheaper from {be_lr}:1; "
     f"index MAE {f(reg.loc[('Ridge full', 'mae'), 'validation'], 3)} against {f(reg.loc[('Persistence (index)', 'mae'), 'validation'], 3)} for persistence",
     "Partly: better alerts, not better ranking"],
]
table("Hypothesis results. H1, H3 and H4: OLS on 4,246 training city-days (H4: 2,702 Pakistani city-days), city-clustered 95% CIs and one-sided p-values; fire terms per SD of log(1 + count). "
      "H2: Logit on 1,706 rain-free September–February days (204 spikes). H5: validation.",
      ["Hypothesis", "Evidence", "Verdict"], rows, [1600, 6500, 1692])
p(f"**H1 is supported.** Fires in the upwind cone raise the next-day index beyond the plain radius count, and the effect survives the control for today's index. "
  "The downwind placebo shows no such effect. Wind direction therefore matters for how fire smoke reaches a city.")
p("**H2 is supported** on every component. Stagnant air, humidity and a large temperature range each raise the odds of a spike, and rain is a strong all-clear signal.")
p(f"**H3 is not supported.** The fire × stagnation term is negative ({f(h3_b, 3)}). "
  "On stagnant days the wind direction is undefined, so the cone count equals the plain radius count by construction. "
  "The interaction therefore compares two different fire measures. The negative sign may reflect that design, not a weaker fire effect.")
p(f"**H4 is not supported.** India-origin fires in the cone show no association with the next-day index in Pakistani cities ({f(H('H4', SPEC_A, IN, 'coef'), 3)}), near the border or far from it. "
  f"Pakistan-origin fires do ({f(H('H4', SPEC_A, PKF, 'coef'), 3)}). With only 7 city clusters these CIs are approximate. "
  "The result does not show that cross-border smoke is absent. It shows that daily India-origin counts do not track Pakistani smog once local fires and weather are known.")
p(f"**H5 is partly supported.** The models beat persistence at the alert decision, not at ranking. "
  f"Skill also fades with lead time. Validation PR-AUC for LR full falls from {f(hz.loc[(1, 'LR full'), 'val_pr_auc'], 3)} at one day to {f(hz.loc[(3, 'LR full'), 'val_pr_auc'], 3)} at three days, "
  f"against {f(hz.loc[(1, 'Persistence'), 'val_pr_auc'], 3)} and {f(hz.loc[(3, 'Persistence'), 'val_pr_auc'], 3)} for persistence.")

# ---- Fairness audit
h2("6.5 Fairness audit")
rows = []
for m in ["Persistence", "LR full", BEST]:
    for data in [VAL, OOF]:
        for g in ["Pakistan", "India"] + TIERS:
            gg = "country" if g in ("Pakistan", "India") else "city-size tier"
            rows.append([m, "Validation" if data == VAL else "Training OOF", TSHORT.get(g, g), int(FG(m, data, gg, g, "spikes")),
                         pct(FG(m, data, gg, g, "base_rate")), pct(FG(m, data, gg, g, "selection_rate")), f(FG(m, data, gg, g, "tpr"), 3),
                         pct(FG(m, data, gg, g, "fpr")), f(FG(m, data, gg, g, "precision"), 3)])
table("Error rates by country and city-size tier at the 5:1 threshold. Base rate = spike share (%). Alert rate = share of city-days with an alert (%). "
      "TPR = share of spikes warned. FPR = share of clean days alerted (%). Training OOF = out-of-fold predictions on training rows.",
      ["Model", "Data", "Group", "Spikes", "Base rate", "Alert rate", "TPR", "FPR", "Precision"],
      rows, [1200, 1200, 1500, 800, 950, 1000, 900, 900, 1342], font=7)
base_c = {g: FG("LR full", VAL, "country", g, "base_rate") for g in ["Pakistan", "India"]}
p(f"**Error rates are similar across countries.** On validation, LR full warns of {pct(FG('LR full', VAL, 'country', 'Pakistan', 'tpr'))}% of Pakistani and {pct(FG('LR full', VAL, 'country', 'India', 'tpr'))}% of Indian spikes. "
  f"Its false-alarm rates are {pct(FG('LR full', VAL, 'country', 'Pakistan', 'fpr'))}% and {pct(FG('LR full', VAL, 'country', 'India', 'fpr'))}%. "
  f"The equalized-odds gap is {FDCI('LR full', VAL, 'country', 'eo_diff')}. On the training out-of-fold predictions the gap is {FDCI('LR full', OOF, 'country', 'eo_diff')}. "
  f"Indian cities did receive more alerts on validation (DIR {f(FD('LR full', VAL, 'country', 'dir_vs_priv_max'))}), but they also had more spikes "
  f"({pct(base_c['India'])}% against {pct(base_c['Pakistan'])}%).")
p(f"**Small cities bear more false alarms.** On validation, LR full raises false alarms on {pct(fpr_lr[T3])}% of clean days in Tier 3 cities, "
  f"{pct(fpr_lr[T2])}% in Tier 2 and {pct(fpr_lr[T1])}% in Tier 1 metros (Figure 7). "
  f"The predictive-equality gap is {FDCI('LR full', VAL, 'city-size tier', 'pe_diff')}. "
  f"Persistence shows the same direction at a lower level ({pct(FG('Persistence', VAL, 'city-size tier', T3, 'fpr'))}% against {pct(FG('Persistence', VAL, 'city-size tier', T1, 'fpr'))}%). "
  f"The season may explain part of the gap: Tier 3 cities had {pct(base_v[T3])}% spike days on validation, against {pct(base_v[T1])}% in metros. "
  f"In training, where the tiers have nearly equal base rates by design, the FPR gap is only {FDCI('LR full', OOF, 'city-size tier', 'pe_diff')}.")
dir_max = FD("LR full", VAL, "city-size tier", "dir_vs_priv_max")
p(f"**The 80% rule.** On training out-of-fold predictions, every tier's alert rate lies within 0.8–1.25 of the metros' for LR full "
  f"(DIR {f(FD('LR full', OOF, 'city-size tier', 'dir_vs_priv_min'))}–{f(FD('LR full', OOF, 'city-size tier', 'dir_vs_priv_max'))}). "
  f"On validation the ratio reaches {f(dir_max)} for {TSHORT[T3]}, so the alert fails the two-sided rule. "
  f"This failure follows the base rates. Small cities had {f(base_v[T3] / base_v[T1])} times the metros' spike rate, so a perfect alert would fail the rule by more. "
  "Demographic parity is therefore the wrong target here. Equalized odds and predictive equality fit the problem better.")
city_v = fg[(fg.model == "LR full") & (fg.data == VAL) & (fg.grouping == "city")].set_index("group")
top3 = city_v["fpr"].sort_values(ascending=False).head(3)
no_spike = city_v.index[city_v["spikes"] == 0].tolist()
p(f"**Equal opportunity.** Recall is high everywhere: {f(tpr_lr[T1], 3)} (metros), {f(tpr_lr[T2], 3)} (large) and {f(tpr_lr[T3], 3)} (small) for LR full on validation. "
  f"The metro figure rests on only {int(FG('LR full', VAL, 'city-size tier', T1, 'spikes'))} spikes, so its CI is wide. "
  f"At city level (Appendix C), the highest false-alarm rate is in {top3.index[0]} ({TSHORT[grp.set_index('city').loc[top3.index[0], 'tier']]}, {pct(top3.iloc[0])}%). "
  f"The tier pattern is not strict, though: {top3.index[1]} ({TSHORT[grp.set_index('city').loc[top3.index[1], 'tier']]}, {pct(top3.iloc[1])}%) "
  f"and {top3.index[2]} ({TSHORT[grp.set_index('city').loc[top3.index[2], 'tier']]}, {pct(top3.iloc[2])}%) come next. "
  f"{' and '.join(no_spike)} had no validation spike and the lowest rates.")
figure("figures/fig_m04_5_group_rates.png",
       "Recall (A) and false-alarm rate (B) by country and city-size tier on validation, at each model's 5:1 threshold, with 95% week-block bootstrap CIs.", 6.4)
rows = []
for m in ["Persistence", "LR full", BEST]:
    for data in [VAL, OOF]:
        for g in ["country", "city-size tier"]:
            rows.append([m, "Validation" if data == VAL else "Training OOF", g.capitalize(),
                         f"{f(FD(m, data, g, 'dir_vs_priv_min'))}–{f(FD(m, data, g, 'dir_vs_priv_max'))}",
                         "Yes" if FD(m, data, g, "passes_80_rule") == 1 else "No",
                         FDCI(m, data, g, "eop_diff"), FDCI(m, data, g, "pe_diff"), FDCI(m, data, g, "eo_diff")])
table("Disparity measures with 95% week-block bootstrap CIs. DIR = alert rate relative to the reference group (Pakistan; Tier 1 metros). "
      "ΔTPR, ΔFPR = largest gap between groups. EO = equalized-odds difference.",
      ["Model", "Data", "Grouping", "DIR range", "80% rule", "ΔTPR (equal opportunity)", "ΔFPR (predictive equality)", "EO difference"],
      rows, [1100, 1100, 1200, 1000, 700, 1600, 1600, 1492], font=7)

# ---- Mitigation
h2("6.6 Bias mitigation and the fairness–accuracy trade-off")
meths = ["none (single threshold)", "reweighing (pre-processing)", PT, f"predictive equality, ε = {EPS}", f"equalized odds, ε = {EPS}"]
mlabel = {"none (single threshold)": "None (single threshold)", "reweighing (pre-processing)": "Reweighing (pre)",
          PT: "Threshold per tier (post)", f"predictive equality, ε = {EPS}": f"Predictive equality, ε = {f(EPS)} (post)",
          f"equalized odds, ε = {EPS}": f"Equalized odds, ε = {f(EPS)} (post)"}
rows = []
for m in dict.fromkeys(["LR full", BEST]):
    for meth in meths:
        rows.append([m, mlabel[meth], f(MIT(m, meth, OOF, "cost_per_1000"), 1), f(MIT(m, meth, OOF, "eo_diff"), 3),
                     f(MIT(m, meth, VAL, "cost_per_1000"), 1), f(MIT(m, meth, VAL, "recall"), 3), f(MIT(m, meth, VAL, "precision"), 3),
                     f"{pct(MG(m, meth, VAL, T1, 'fpr'))} / {pct(MG(m, meth, VAL, T3, 'fpr'))}",
                     f(MIT(m, meth, VAL, "pe_diff"), 3), f(MIT(m, meth, VAL, "eo_diff"), 3)])
table("Bias mitigation across city-size tiers. All thresholds and weights were chosen on training out-of-fold (OOF) predictions; validation only reports. "
      "Cost per 1,000 city-days at 5:1. FPR T1 / T3 = false-alarm rate (%) in metros and small cities.",
      ["Model", "Method", "OOF cost", "OOF EO gap", "Val. cost", "Val. recall", "Val. precision", "Val. FPR T1 / T3", "Val. ΔFPR", "Val. EO gap"],
      rows, [850, 2100, 750, 800, 750, 800, 850, 1150, 750, 992], font=7)
thr_pt = json.loads(mit[(mit.model == "LR full") & (mit.method == PT) & (mit.data == VAL)]["thresholds"].iloc[0])
thr_one = json.loads(mit[(mit.model == "LR full") & (mit.method.str.startswith("none")) & (mit.data == VAL)]["thresholds"].iloc[0])[T1]
fp_t3 = {k: MG("LR full", k, VAL, T3, "fp") for k in ["none", PT]}
n_metro = int(FG("LR full", VAL, "city-size tier", T1, "spikes"))
same_val = all(MIT("LR full", k, VAL, "cost_per_1000") == cost_pt_v for k in [f"predictive equality, ε = {EPS}", f"equalized odds, ε = {EPS}"])
assert same_val, "the text assumes the three post-processing rules end at the same validation result for LR full"
assert 0.4 <= MIT("LR full", PT, VAL, "pe_diff") / MIT("LR full", "none", VAL, "pe_diff") <= 0.6, "the text says per-tier thresholds halve the FPR gap"
assert set(no_spike) == set(city_v["fpr"].nsmallest(len(no_spike)).index), "the text says the no-spike cities have the lowest FPR"
p(f"**Per-tier thresholds halve the false-alarm gap.** For LR full they raise the small-city threshold from {f(thr_one, 3)} to {f(thr_pt[T3], 3)}. "
  f"The metro and large-city thresholds stay close to the single value ({f(thr_pt[T1], 3)} and {f(thr_pt[T2], 3)}). "
  f"On validation the small-city false-alarm rate falls from {pct(fpr_lr[T3])}% to {pct(fpr_pt[T3])}% ({int(fp_t3['none'])} to {int(fp_t3[PT])} false alarms). "
  f"The predictive-equality gap falls from {f(MIT('LR full', 'none', VAL, 'pe_diff'), 3)} to {f(MIT('LR full', PT, VAL, 'pe_diff'), 3)}. "
  f"The total cost falls from {f(cost_single_v, 1)} to {f(cost_pt_v, 1)} per 1,000 city-days, while recall drops from {f(MIT('LR full', 'none', VAL, 'recall'), 3)} to {f(MIT('LR full', PT, VAL, 'recall'), 3)}. "
  "Here fairness and cost point the same way, because one shared threshold over-alerts the small cities. "
  f"The gain does not carry over to {BEST}: its per-tier thresholds raise the validation cost from {f(MIT(BEST, 'none', VAL, 'cost_per_1000'), 1)} to {f(MIT(BEST, PT, VAL, 'cost_per_1000'), 1)}.")
p(f"At ε = {f(EPS)}, the predictive-equality and equalized-odds rules give LR full the same validation result as the per-tier thresholds. "
  f"The equalized-odds thresholds narrow the OOF gap from {f(MIT('LR full', 'none', OOF, 'eo_diff'), 3)} to {f(MIT('LR full', 'equalized odds', OOF, 'eo_diff'), 3)}. "
  f"On validation the gap stays at {f(MIT('LR full', 'equalized odds', VAL, 'eo_diff'), 3)}. "
  f"The metro recall rests on {n_metro} spikes, so one spike moves it by {f(1 / n_metro, 3)}.")
p(f"**Reweighing changes little.** The tiers have nearly equal training base rates by design, so the Kamiran–Calders weights stay close to 1. "
  f"The LR full validation cost stays at {f(MIT('LR full', 'reweighing', VAL, 'cost_per_1000'), 1)}. "
  f"For {BEST} it moves from {f(MIT(BEST, 'none', VAL, 'cost_per_1000'), 1)} to {f(MIT(BEST, 'reweighing', VAL, 'cost_per_1000'), 1)}, and its equalized-odds gap does not change "
  f"({f(MIT(BEST, 'none', VAL, 'eo_diff'), 3)}).")
po = par[(par.model == "LR full") & (par.data == OOF) & (par.method == "equalized odds")].set_index("knob")
pv_ = par[(par.model == "LR full") & (par.data == VAL)]
cheap = pv_.loc[pv_["cost_per_1000"].idxmin()]
p(f"**Strict equalized odds has a price** (Figure 8). On training data, tightening the band from ε = 0.05 to 0.02 lowers the LR gap from {f(po.loc[0.05, 'eo_diff'], 3)} to {f(po.loc[0.02, 'eo_diff'], 3)}. "
  f"The cost rises only from {f(po.loc[0.05, 'cost_per_1000'], 1)} to {f(po.loc[0.02, 'cost_per_1000'], 1)}. "
  f"At ε = 0.01 the cost jumps to {f(po.loc[0.01, 'cost_per_1000'], 1)}, because recall falls to {f(po.loc[0.01, 'recall'], 3)}. "
  f"On validation the cheapest LR rule is {cheap['method']} at ε = {f(cheap['knob'])} ({f(cheap['cost_per_1000'], 1)} per 1,000). "
  "We did not pick it, because the choice must come from training data.")
figure("figures/fig_m04_6_pareto.png",
       "Fairness–accuracy trade-off across city-size tiers: cost per 1,000 city-days against the equalized-odds gap, for every threshold rule and reweighing strength, "
       "on training out-of-fold predictions (A) and on validation (B). Lines join the Pareto-efficient points of each model.", 6.6)
t20 = thc[(thc.ratio == 20) & (thc.rule == "per tier")].set_index("tier")["threshold"]
t1r = thc[(thc.ratio == 1) & (thc.rule == "per tier")].set_index("tier")["threshold"]
p(f"**Thresholds by tier and cost ratio** (Figure 9). In every tier, the cost-optimal threshold falls or stays level as the cost ratio rises. "
  f"For small cities it falls from {f(t1r[T3], 3)} at 1:1 to {f(t20[T3], 3)} at 20:1. "
  "Officials can therefore read their own threshold off these curves once they set their own cost ratio.")
figure("figures/fig_m04_7_thresholds.png",
       f"Asymmetric threshold tuning by city-size tier for {FINAL}. (A) TPR (solid) and FPR (dashed) against the threshold on training OOF predictions; dotted lines mark the 5:1 tier thresholds. "
       "(B) Cost-optimal threshold by tier for FN:FP ratios 1–20. (C) Validation cost by tier with tier thresholds (solid) and the single threshold (dashed).", 6.6)

# =====================================================================
# 7. Discussion
# =====================================================================
h1("7. Discussion")
h2("7.1 What the results mean")
p("Today's smog is the best guide to tomorrow's. Both ensembles found the same structure as the sparse LR: today's margin far ahead, then temperature (and rain for HGB), with fires near zero. "
  "Their extra flexibility did not pay. One winter of training data holds only 204 spikes, and the strongest signal is probably close to linear. "
  "The value of a model therefore lies in the alert decision. It catches the first day of an episode, which persistence cannot.")
p("Fires matter for smog levels, not for next-day forecasts. H1 shows that upwind fires track next-day smog, and Milestone 2 found the same with correlations. "
  "Yet their smoke is already in today's index by the time an alert is issued. Fire control is therefore a source-reduction policy, not a forecasting input.")
h2("7.2 FATEN evaluation")
table("The final alert (LR full with per-tier thresholds) against the FATEN principles.",
      ["Principle", "Evidence from this study", "Remaining risk", "Safeguard"],
      [["Fairness", f"Similar error rates by country (EO gap {f(FD('LR full', VAL, 'country', 'eo_diff'), 3)}). Per-tier thresholds cut the small-city FPR from {pct(fpr_lr[T3])}% to {pct(fpr_pt[T3])}%.",
        "Metro recall rests on few spikes. Tier boundaries use a 2011 census for India.", "Re-audit by tier and city every season; publish the group error rates."],
       ["Autonomy", "The model advises. Officials set the cost ratio and read the threshold off the cost curve.", "An automatic trigger would remove local judgement.",
        "Keep a human decision for closures; allow a city to override with a recorded reason."],
       ["Trust", "Two inputs with readable odds ratios; out-of-fold thresholds; leakage-free evaluation; open code and decision log.",
        f"{int(cnt.loc['LR full', 'fp'])} false alarms in one season can erode trust.", "Publish the alert record and its errors; explain each alert by today's margin and temperature."],
       ["Equity", "The burden of false alarms falls on small cities with fewer monitors and less capacity.", "Repeated needless closures hurt daily-wage workers most.",
        "Pair alerts with support (outdoor-work rules, school meal continuity) in small cities."],
       ["Non-maleficence", f"Recall {pct(MIT('LR full', PT, VAL, 'recall'))}% on validation. All {int(onset.loc[('LR full', 'FN', 'onset')])} spikes missed at the single threshold were onset days.", "Missed onsets leave people exposed without warning.",
        "Keep existing advisories; treat the model as an addition, never a replacement."]],
      [1300, 3200, 2600, 2692], font=7)
h2("7.3 Living-lab deployment")
p("A living lab tests an innovation with its users in a real setting, as a partnership between researchers, public bodies and citizens (Leminen et al., 2012). "
  "We propose a one-season pilot with the Environment Protection Department of Punjab in two cities per tier. "
  "The model would issue an advisory each evening. Officials would record their own decision next to it. Schools and clinics would report what happened.")
table("Failure modes in a living-lab pilot and governance safeguards.",
      ["Failure mode", "Why it can happen", "Safeguard"],
      [["Data outage", "The CAMS feed or the weather API is late or down; Islamabad and Rawalpindi share one grid cell.", "Fall back to persistence; flag the alert as degraded."],
       ["Model drift", "One training winter; burning practice, emissions and weather change between years.", "Re-train each season on the newest winter; track recall and FPR by tier monthly."],
       ["Sudden onsets", "Missed spikes are days whose smog jumps without warning signs today.", "Add forecast weather (not observed) and test 2024 out of time before use."],
       ["Alert fatigue", f"False alarms on {pct(fpr_pt[T3])}–{pct(fpr_lr[T3])}% of clean days in small cities on validation.", "Per-tier thresholds; a two-level alert (advisory, closure)."],
       ["Digital marginalisation", "Small cities have fewer monitors, so model data stand in for missing measurements.", "Install low-cost sensors in Tier 3 cities; weight their feedback in the review."],
       ["Cross-border blame", "Fire maps invite blame across the border.", "Report fire origin as context only; H4 found no daily India-origin effect."]],
      [1700, 4200, 3892], font=7)
p("**Governance.** A review board with officials from both tiers, a public-health expert and a community representative would meet monthly. "
  "It would review the fairness table, the cost ratio and every missed spike. The decision log, the code and the alert record would stay public.")
h2("7.4 Policy recommendations")
bullets([f"**Issue a next-day, city-level advisory** from today's index margin and temperature. It beats persistence whenever a missed spike costs at least {be_lr} false alarms.",
         "**Set thresholds per city-size tier, not one for all.** One shared threshold over-alerts small cities.",
         "**Use rain as an all-clear signal.** No training rain day was followed by a spike.",
         "**Treat fire control as source reduction.** Fires raise smog levels, but they add no next-day forecast skill once today's smog is known.",
         "**Share one alert method across the border.** The alert has similar error rates in Pakistan and India, and India's GRAP already acts on daily air-quality levels (Tribune News Service, 2024)."])

# =====================================================================
# 8. Limitations, 9. Conclusion
# =====================================================================
h1("8. Limitations")
bullets(["**One training winter.** Every threshold and hyperparameter rests on one harvest season. The validation season has 18 weeks, so every CI is wide.",
         "**Model-based air quality.** CAMS estimates on a coarse grid stand in for monitors. Islamabad and Rawalpindi share one series.",
         "**Observed weather.** The models use observed weather on day t. A real alert would use forecast weather, which adds error.",
         "**Coarse fairness groups.** Tiers use city population only. They miss income, health access and within-city inequality. The Indian census dates from 2011.",
         "**Few spikes per group.** Metros had 12 validation spikes, so their recall is uncertain. City-level results are descriptive.",
         "**2024 still sealed.** The out-of-time test on 2024 is the next step and may change the conclusions."])
h1("9. Conclusion")
p(f"A transparent next-day smog alert for Punjab is feasible with today's data. A two-input logistic regression catches {int(cnt.loc['LR full', 'tp'])} of 89 validation spikes. "
  f"It is cheaper than persistence for any cost ratio from {be_lr}:1 upwards. Random forests and gradient boosting do not improve on it. "
  "Upwind fires shape smog levels, as the cone-versus-radius test shows, but they add no next-day skill. "
  "The fairness audit found similar error rates in Pakistan and India, but a higher false-alarm burden on small cities. "
  "Tier-specific thresholds halve that gap and lower the total cost. "
  "Before deployment, the alert needs the 2024 out-of-time test, forecast weather inputs and a supervised living-lab pilot.")
p("**Contributions and reproducibility.** Munir Tariq led the weather stream and the merge. Ismail Nooruddin led the air-quality stream and the target. Bilal Ayub led the fire stream. "
  "All three shared the modelling, the fairness audit and the writing. "
  "The notebooks (merge_analysis.ipynb, modeling.ipynb, advanced_modeling.ipynb), the modules in src/, the saved models and the decision log (DECISIONS.md) reproduce every number in this paper.")

# =====================================================================
# References (APA 7, alphabetical)
# =====================================================================
h1("References")
refs = [
    "Bergstra, J., & Bengio, Y. (2012). Random search for hyper-parameter optimization. *Journal of Machine Learning Research, 13*, 281–305. https://www.jmlr.org/papers/v13/bergstra12a.html",
    "Breiman, L. (2001). Random forests. *Machine Learning, 45*(1), 5–32. https://doi.org/10.1023/A:1010933404324",
    "Chouldechova, A. (2017). Fair prediction with disparate impact: A study of bias in recidivism prediction instruments. *Big Data, 5*(2), 153–163. https://doi.org/10.1089/big.2016.0047",
    "Cusworth, D. H., Mickley, L. J., Sulprizio, M. P., Liu, T., Marlier, M. E., DeFries, R. S., Guttikunda, S. K., & Gupta, P. (2018). Quantifying the influence of agricultural fires in northwest India on urban air pollution in Delhi, India. *Environmental Research Letters, 13*(4), 044018. https://doi.org/10.1088/1748-9326/aab303",
    "Environment Protection Department, Government of the Punjab. (n.d.). *Smog Commission reports*. https://epd.punjab.gov.pk/smog_commission_reports",
    "Feldman, M., Friedler, S. A., Moeller, J., Scheidegger, C., & Venkatasubramanian, S. (2015). Certifying and removing disparate impact. In *Proceedings of the 21st ACM SIGKDD International Conference on Knowledge Discovery and Data Mining* (pp. 259–268). https://doi.org/10.1145/2783258.2783311",
    "Friedman, J. H. (2001). Greedy function approximation: A gradient boosting machine. *The Annals of Statistics, 29*(5), 1189–1232. https://doi.org/10.1214/aos/1013203451",
    "Hardt, M., Price, E., & Srebro, N. (2016). Equality of opportunity in supervised learning. In *Advances in Neural Information Processing Systems 29*. https://arxiv.org/abs/1610.02413",
    "Inness, A., et al. (2019). The CAMS reanalysis of atmospheric composition. *Atmospheric Chemistry and Physics, 19*(6), 3515–3556. https://doi.org/10.5194/acp-19-3515-2019",
    "Jethva, H., Torres, O., Field, R. D., Lyapustin, A., Gautam, R., & Kayetha, V. (2019). Connecting crop productivity, residue fires, and air quality over northern India. *Scientific Reports, 9*, 16594. https://doi.org/10.1038/s41598-019-52799-x",
    "Kamiran, F., & Calders, T. (2012). Data preprocessing techniques for classification without discrimination. *Knowledge and Information Systems, 33*(1), 1–33. https://doi.org/10.1007/s10115-011-0463-8",
    "Ke, G., Meng, Q., Finley, T., Wang, T., Chen, W., Ma, W., Ye, Q., & Liu, T.-Y. (2017). LightGBM: A highly efficient gradient boosting decision tree. In *Advances in Neural Information Processing Systems 30*. https://papers.nips.cc/paper_files/paper/2017/hash/6449f44a102fde848669bdd9eb6b76fa-Abstract.html",
    "Leminen, S., Westerlund, M., & Nyström, A.-G. (2012). Living labs as open-innovation networks. *Technology Innovation Management Review, 2*(9), 6–11. https://doi.org/10.22215/timreview/602",
    "Mehrabi, N., Morstatter, F., Saxena, N., Lerman, K., & Galstyan, A. (2021). A survey on bias and fairness in machine learning. *ACM Computing Surveys, 54*(6), 1–35. https://doi.org/10.1145/3457607",
    "NASA. (2024). *Fire Information for Resource Management System (FIRMS): VIIRS 375 m active fire product*. https://firms.modaps.eosdis.nasa.gov",
    "Pakistan Bureau of Statistics. (2025). *7th Population and Housing Census 2023: National census report*. https://www.pbs.gov.pk/wp-content/uploads/2020/07/National-Census-Report-2023.pdf",
    "Pandey, A., Brauer, M., Cropper, M. L., et al. (2021). Health and economic impact of air pollution in the states of India: The Global Burden of Disease Study 2019. *The Lancet Planetary Health, 5*(1), e25–e38. https://doi.org/10.1016/S2542-5196(20)30298-9",
    "Pedregosa, F., Varoquaux, G., Gramfort, A., et al. (2011). Scikit-learn: Machine learning in Python. *Journal of Machine Learning Research, 12*(85), 2825–2830. https://www.jmlr.org/papers/v12/pedregosa11a.html",
    "Roberts, D. R., Bahn, V., Ciuti, S., et al. (2017). Cross-validation strategies for data with temporal, spatial, hierarchical, or phylogenetic structure. *Ecography, 40*(8), 913–929. https://doi.org/10.1111/ecog.02881",
    "Rybarczyk, Y., & Zalakeviciute, R. (2018). Machine learning approaches for outdoor air quality modelling: A systematic review. *Applied Sciences, 8*(12), 2570. https://doi.org/10.3390/app8122570",
    "Saito, T., & Rehmsmeier, M. (2015). The precision-recall plot is more informative than the ROC plot when evaluating binary classifiers on imbalanced datasets. *PLoS ONE, 10*(3), e0118432. https://doi.org/10.1371/journal.pone.0118432",
    "Schroeder, W., Oliva, P., Giglio, L., & Csiszar, I. A. (2014). The New VIIRS 375 m active fire detection data product: Algorithm description and initial assessment. *Remote Sensing of Environment, 143*, 85–96. https://doi.org/10.1016/j.rse.2013.12.008",
    "Seabold, S., & Perktold, J. (2010). Statsmodels: Econometric and statistical modeling with Python. In *Proceedings of the 9th Python in Science Conference* (pp. 92–96). https://doi.org/10.25080/Majora-92bf1922-011",
    "Tariq, S., ul-Haq, Z., & Ali, M. (2015). Analysis of optical and physical properties of aerosols during crop residue burning event of October 2010 over Lahore, Pakistan. *Atmospheric Pollution Research, 6*(6), 969–978. https://doi.org/10.1016/j.apr.2015.05.002",
    "Tribune News Service. (2024, December 15). GRAP rules revised: Nod to hybrid learning till Class V in severe AQI. *The Tribune*. https://www.tribuneindia.com/news/delhi/grap-rules-revised-nod-to-hybrid-learning-till-class-v-in-severe-aqi/",
    "Waqar, A., & Gabol, I. (2024, November 12). Punjab govt orders closure of all schools as province tackles hazardous air quality. *Dawn*. https://www.dawn.com/news/1871888",
    "World Health Organization. (2021). *WHO global air quality guidelines: Particulate matter (PM2.5 and PM10), ozone, nitrogen dioxide, sulfur dioxide and carbon monoxide*. WHO.",
    "Zippenfenig, P. (2023). *Open-Meteo.com Weather API* [Computer software]. Zenodo. https://doi.org/10.5281/zenodo.7970649",
]
blocks.append({"t": "apa", "items": sorted(refs, key=lambda r: r.lower())})

# =====================================================================
# Appendices
# =====================================================================
blocks.append({"t": "pagebreak"})
h1("Appendix A. Data Audit")
table("Row bookkeeping from the raw files to the master table.",
      ["Stream", "Steps and row counts"],
      [["Air quality", "453,192 hourly rows → 191,153 in 2022–2023 → 135,905 after removing the empty Jan–Aug 2022 block → 5,665 city-days (each with ≥ 18 valid hours)"],
       ["Weather", "433,728 hourly rows → 188,393 in 2022–2023 → 7,852 city-days → 5,665 in the modelling window"],
       ["Fire", "1,284,773 detections → 287,323 in the study box (26–37°N, 68–79°E) → 279,968 vegetation fires → 238,796 with nominal or high confidence "
                "→ 238,756 on 2022–2023 local dates → 8,030 city-days (days without fires = 0) → 5,665 in the window"],
       ["Master", "Calendar 5,665 → air-quality join 5,665 → weather join 5,665 → fire join 5,665 (all rows matched); 287 columns"],
       ["Modelling (h = 1)", "5,665 → 5,544: 33 gap rows, 11 rows without a target (31 Dec 2023), 22 rows without index lag 2, 55 rows whose feature or target day is a flagged day"]],
      [1500, 8292])
table("Preprocessing decisions, alternatives and reasons.",
      ["Decision", "Alternative", "Reason"],
      [["Add 5 h (UTC+5) before taking the date, for all cities", "Keep GMT dates; +5:30 for India", "Day boundaries must match across streams"],
       ["Modelling window from 4 Aug 2022", "Impute the empty air-quality block", "Seven months of invented pollution would create the pattern the model must learn"],
       ["Lags and targets within each city", "Shift the whole table", "Prevents one city's last days leaking into the next city's first days"],
       ["log(1 + x) for skewed variables; z-scores from training only", "No transform; fit on all data", "Removes the long right tail; prevents leakage"],
       ["Keep outliers and add flags", "Delete, cap or winsorise", "Extreme days are the smog episodes the project studies"],
       ["Flag 13–16 Dec 2022 and drop them from fitting", "Delete the rows", "Near-zero pollutants in every city at once; the calendar must stay unbroken for lags"],
       ["AQ history as the margin over the city threshold", "Raw pooled index", "Each city's label uses its own threshold; the raw index made city dummies act as threshold corrections"],
       ["Upwind cone ±45° at 300 km", "Plain radius; 150 km", "Highest median correlation with next-day smog on training harvest days"],
       ["NW as the wind reference sector", "Calm as reference", "Calm is identical to the stagnant flag (631 of 631 days)"]],
      [3200, 2400, 4192])
figure("figures/fig_m1_cone_radius_sensitivity.png",
       "Median Spearman correlation between the fire count on day t and the index on day t + 1, for every cone and radius. Top: training harvest season, used to choose the setting (black box). "
       "Bottom: full training year, where the shared seasonal cycle inflates every setting, including the placebo.", 5.6)

h1("Appendix B. Model Details")
figure("figures/fig_m3_1_cv_folds.png",
       "Purged, grouped 5 × 5 cross-validation. (A) Fold layout of the first repeat: fit part, rows removed by the purge and embargo, held-out weeks and dropped days. "
       "(B) Spike rate of each of the 25 test folds against the rate over all training rows.", 6.4)
figure("figures/fig_m04_1_tuning.png",
       "Random search for the random forest (A, B) and gradient boosting (C): cross-validated PR-AUC of every draw, by feature set; circles mark the best draw. "
       "Dashed line: LR full from Milestone 3.", 6.6)
ALL = ["Persistence"] + [f"{a} {b}" for a in ["LR", "DT", "RF", "HGB"] for b in ["full", "no-fire", "weather-only"]]
rows = [[m, f(V(m, "pr_auc"), 3), f(V(m, "roc_auc"), 3), f(V(m, "recall"), 3), f(V(m, "precision"), 3), f(V(m, "f1"), 3),
         "–" if pd.isna(V(m, "brier")) else f(V(m, "brier"), 3), f(V(m, "cost_per_1000"), 1), f(CV(m, "pr_auc"), 3), f(CV(m, "cost_per_1000"), 1)] for m in ALL]
table("All model variants: validation metrics at the 5:1 threshold and cross-validated PR-AUC and cost (mean of 25 folds).",
      ["Model", "Val. PR-AUC", "Val. ROC-AUC", "Recall", "Precision", "F1", "Brier", "Val. cost", "CV PR-AUC", "CV cost"],
      rows, [1500, 900, 950, 800, 850, 750, 750, 850, 900, 942], font=7)
comps = [f"{BEST} − LR full", f"{OTHER} − LR full", "RF full − DT full", "HGB full − DT full", "RF full − Persistence", "HGB full − Persistence",
         "LR full − Persistence", "RF full − RF no-fire", "HGB full − HGB no-fire", "RF no-fire − RF weather-only", "HGB no-fire − HGB weather-only"]
rows = [[c, DCI(c, "pr_auc"), DCI(c, "roc_auc", 4), ci(D(c, "cost"), D(c, "cost", "ci_low"), D(c, "cost", "ci_high"), 1),
         f(D(c, "pr_auc", "cv_diff_mean"), 3), int(D(c, "pr_auc", "cv_folds_a_better"))] for c in comps]
table("Paired comparisons on validation (difference with 95% week-block bootstrap CI) and in the 25 CV folds (mean PR-AUC difference; folds where the first model is better).",
      ["Comparison", "ΔPR-AUC", "ΔROC-AUC", "ΔCost per 1,000", "CV ΔPR-AUC", "CV folds better"],
      rows, [2500, 1700, 1800, 1700, 1000, 1092], font=7)

h1("Appendix C. Fairness by City")
rows = []
cities = grp_sorted["city"].tolist()
for c in cities:
    r = [c, TSHORT[grp.set_index("city").loc[c, "tier"]]]
    for data in [VAL, OOF]:
        r += [int(FG("LR full", data, "city", c, "spikes")),
              "–" if pd.isna(FG("LR full", data, "city", c, "tpr")) else f(FG("LR full", data, "city", c, "tpr"), 3),
              pct(FG("LR full", data, "city", c, "fpr")), pct(FG("LR full", data, "city", c, "selection_rate"))]
    rows.append(r)
table("LR full error rates by city at the single 5:1 threshold. FPR and alert rate in %. City results rest on few spikes and are descriptive.",
      ["City", "Tier", "Val. spikes", "Val. TPR", "Val. FPR", "Val. alert rate", "OOF spikes", "OOF TPR", "OOF FPR", "OOF alert rate"],
      rows, [1300, 1200, 800, 800, 800, 950, 850, 850, 850, 1192], font=7)

OUT.write_text(json.dumps({"blocks": blocks}, ensure_ascii=False, indent=1), encoding="utf-8")
print(f"{OUT}: {len(blocks)} blocks, {counters['table']} tables, {counters['figure']} figures")
