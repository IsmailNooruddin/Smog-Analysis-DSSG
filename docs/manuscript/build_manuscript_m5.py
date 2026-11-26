"""Builds the Milestone 5 manuscript: one IEEE-style conference paper over the whole semester.

Structure follows the Milestone 5 brief: Title, Authors, Abstract; I Introduction and problem framing;
II Data curation and master dataset inventory; III Exploratory data analysis and drivers; IV Predictive
modelling; V Fairness and ethics audit; VI Data expansion, drift and re-training; VII Policy
recommendations; VIII Limitations and conclusion; numbered IEEE references; one-column appendix.

Every number comes from docs/tables/*.csv (merge_analysis.ipynb, modeling.ipynb, advanced_modeling.ipynb,
data_extension.ipynb) or from Dataset/clean/m4_params.json and m5_params.json. Figures come from
make_figures_m5.py (column width) and the notebooks.

Run from the repository root, after data_extension.ipynb and make_figures_m5.py:
    python docs/manuscript/build_manuscript_m5.py
    python docs/manuscript/check_numbers_m5.py
    node docs/manuscript/render_docx.js 5
"""
import json
import os
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
T = ROOT / "docs" / "tables"
OUT = ROOT / "docs" / "manuscript" / "manuscript_m5.json"
ROMAN = ["I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X", "XI", "XII", "XIII", "XIV", "XV"]

blocks = []
counters = {"table": 0, "figure": 0, "h1": 0, "h2": 0, "app": 0}


# ---------------------------------------------------------------------
# Block helpers
# ---------------------------------------------------------------------
def tab(name, **kw):
    return pd.read_csv(T / f"{name}.csv", **kw)


def h1(text):
    counters["h1"] += 1
    counters["h2"] = 0
    blocks.append({"t": "h1", "text": f"{ROMAN[counters['h1'] - 1]}. {text}"})


def h1_plain(text):
    counters["h2"] = 0
    blocks.append({"t": "h1", "text": text})


def h2(text):
    counters["h2"] += 1
    blocks.append({"t": "h2", "text": f"{chr(64 + counters['h2'])}. {text}"})


def p(text, noindent=False):
    blocks.append({"t": "p", "text": text, **({"noindent": True} if noindent else {})})


def bullets(items):
    blocks.append({"t": "bullets", "items": items})


def section(layout, newpage=False):
    blocks.append({"t": "section", "layout": layout, "newpage": newpage})


def table(caption, header, rows, widths, note=None, font=7.5, align=None):
    counters["table"] += 1
    n = counters["table"]
    blocks.append({"t": "table", "label": f"TABLE {ROMAN[n - 1]}", "caption": caption, "header": header,
                   "rows": [[str(c) for c in r] for r in rows], "widths": widths, "note": note, "font": font,
                   **({"align": align} if align else {})})
    return f"Table {ROMAN[n - 1]}"


def figure(path, caption, width_in=3.45):
    counters["figure"] += 1
    n = counters["figure"]
    blocks.append({"t": "figure", "path": str(ROOT / path), "caption": f"Fig. {n}. {caption}", "width_in": width_in})
    return f"Fig. {n}"


def next_table():
    return f"Table {ROMAN[counters['table']]}"


def next_fig():
    return f"Fig. {counters['figure'] + 1}"


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
# IEEE references, numbered in order of first citation
# ---------------------------------------------------------------------
REFS = {
    "who21": "World Health Organization, *WHO Global Air Quality Guidelines: Particulate Matter (PM2.5 and PM10), Ozone, Nitrogen Dioxide, Sulfur Dioxide and Carbon Monoxide*. Geneva, Switzerland: WHO, 2021.",
    "epd": "Environment Protection Department, Government of the Punjab, \"Smog Commission reports.\" [Online]. Available: https://epd.punjab.gov.pk/smog_commission_reports",
    "dawn24": "A. Waqar and I. Gabol, \"Punjab govt orders closure of all schools as province tackles hazardous air quality,\" *Dawn*, Nov. 12, 2024. [Online]. Available: https://www.dawn.com/news/1871888",
    "tribune24": "Tribune News Service, \"GRAP rules revised: Nod to hybrid learning till Class V in severe AQI,\" *The Tribune*, Dec. 15, 2024. [Online]. Available: https://www.tribuneindia.com/news/delhi/grap-rules-revised-nod-to-hybrid-learning-till-class-v-in-severe-aqi/",
    "pandey21": "A. Pandey *et al.*, \"Health and economic impact of air pollution in the states of India: The Global Burden of Disease Study 2019,\" *Lancet Planet. Health*, vol. 5, no. 1, pp. e25–e38, 2021, doi: 10.1016/S2542-5196(20)30298-9.",
    "cusworth18": "D. H. Cusworth *et al.*, \"Quantifying the influence of agricultural fires in northwest India on urban air pollution in Delhi, India,\" *Environ. Res. Lett.*, vol. 13, no. 4, Art. no. 044018, 2018, doi: 10.1088/1748-9326/aab303.",
    "jethva19": "H. Jethva, O. Torres, R. D. Field, A. Lyapustin, R. Gautam, and V. Kayetha, \"Connecting crop productivity, residue fires, and air quality over northern India,\" *Sci. Rep.*, vol. 9, Art. no. 16594, 2019, doi: 10.1038/s41598-019-52799-x.",
    "tariq15": "S. Tariq, Z. ul-Haq, and M. Ali, \"Analysis of optical and physical properties of aerosols during crop residue burning event of October 2010 over Lahore, Pakistan,\" *Atmos. Pollut. Res.*, vol. 6, no. 6, pp. 969–978, 2015, doi: 10.1016/j.apr.2015.05.002.",
    "rybarczyk18": "Y. Rybarczyk and R. Zalakeviciute, \"Machine learning approaches for outdoor air quality modelling: A systematic review,\" *Appl. Sci.*, vol. 8, no. 12, Art. no. 2570, 2018, doi: 10.3390/app8122570.",
    "inness19": "A. Inness *et al.*, \"The CAMS reanalysis of atmospheric composition,\" *Atmos. Chem. Phys.*, vol. 19, no. 6, pp. 3515–3556, 2019, doi: 10.5194/acp-19-3515-2019.",
    "zipp23": "P. Zippenfenig, \"Open-Meteo.com Weather API,\" Zenodo, 2023, doi: 10.5281/zenodo.7970649.",
    "schroeder14": "W. Schroeder, P. Oliva, L. Giglio, and I. A. Csiszar, \"The New VIIRS 375 m active fire detection data product: Algorithm description and initial assessment,\" *Remote Sens. Environ.*, vol. 143, pp. 85–96, 2014, doi: 10.1016/j.rse.2013.12.008.",
    "firms": "NASA, \"Fire Information for Resource Management System (FIRMS): VIIRS 375 m active fire product,\" 2024. [Online]. Available: https://firms.modaps.eosdis.nasa.gov",
    "roberts17": "D. R. Roberts *et al.*, \"Cross-validation strategies for data with temporal, spatial, hierarchical, or phylogenetic structure,\" *Ecography*, vol. 40, no. 8, pp. 913–929, 2017, doi: 10.1111/ecog.02881.",
    "saito15": "T. Saito and M. Rehmsmeier, \"The precision-recall plot is more informative than the ROC plot when evaluating binary classifiers on imbalanced datasets,\" *PLoS ONE*, vol. 10, no. 3, Art. no. e0118432, 2015, doi: 10.1371/journal.pone.0118432.",
    "breiman01": "L. Breiman, \"Random forests,\" *Mach. Learn.*, vol. 45, no. 1, pp. 5–32, 2001, doi: 10.1023/A:1010933404324.",
    "friedman01": "J. H. Friedman, \"Greedy function approximation: A gradient boosting machine,\" *Ann. Statist.*, vol. 29, no. 5, pp. 1189–1232, 2001, doi: 10.1214/aos/1013203451.",
    "ke17": "G. Ke *et al.*, \"LightGBM: A highly efficient gradient boosting decision tree,\" in *Adv. Neural Inf. Process. Syst. 30*, 2017.",
    "bergstra12": "J. Bergstra and Y. Bengio, \"Random search for hyper-parameter optimization,\" *J. Mach. Learn. Res.*, vol. 13, pp. 281–305, 2012.",
    "pedregosa11": "F. Pedregosa *et al.*, \"Scikit-learn: Machine learning in Python,\" *J. Mach. Learn. Res.*, vol. 12, no. 85, pp. 2825–2830, 2011.",
    "seabold10": "S. Seabold and J. Perktold, \"Statsmodels: Econometric and statistical modeling with Python,\" in *Proc. 9th Python Sci. Conf.*, 2010, pp. 92–96, doi: 10.25080/Majora-92bf1922-011.",
    "pbs25": "Pakistan Bureau of Statistics, \"7th Population and Housing Census 2023: National census report,\" 2025. [Online]. Available: https://www.pbs.gov.pk/wp-content/uploads/2020/07/National-Census-Report-2023.pdf",
    "feldman15": "M. Feldman, S. A. Friedler, J. Moeller, C. Scheidegger, and S. Venkatasubramanian, \"Certifying and removing disparate impact,\" in *Proc. 21st ACM SIGKDD Int. Conf. Knowl. Discov. Data Min.*, 2015, pp. 259–268, doi: 10.1145/2783258.2783311.",
    "hardt16": "M. Hardt, E. Price, and N. Srebro, \"Equality of opportunity in supervised learning,\" in *Adv. Neural Inf. Process. Syst. 29*, 2016.",
    "chouldechova17": "A. Chouldechova, \"Fair prediction with disparate impact: A study of bias in recidivism prediction instruments,\" *Big Data*, vol. 5, no. 2, pp. 153–163, 2017, doi: 10.1089/big.2016.0047.",
    "kamiran12": "F. Kamiran and T. Calders, \"Data preprocessing techniques for classification without discrimination,\" *Knowl. Inf. Syst.*, vol. 33, no. 1, pp. 1–33, 2012, doi: 10.1007/s10115-011-0463-8.",
    "mehrabi21": "N. Mehrabi, F. Morstatter, N. Saxena, K. Lerman, and A. Galstyan, \"A survey on bias and fairness in machine learning,\" *ACM Comput. Surv.*, vol. 54, no. 6, pp. 1–35, 2021, doi: 10.1145/3457607.",
    "morenotorres12": "J. G. Moreno-Torres, T. Raeder, R. Alaiz-Rodríguez, N. V. Chawla, and F. Herrera, \"A unifying view on dataset shift in classification,\" *Pattern Recognit.*, vol. 45, no. 1, pp. 521–530, 2012, doi: 10.1016/j.patcog.2011.06.019.",
    "gama14": "J. Gama, I. Žliobaitė, A. Bifet, M. Pechenizkiy, and A. Bouchachia, \"A survey on concept drift adaptation,\" *ACM Comput. Surv.*, vol. 46, no. 4, pp. 1–37, 2014, doi: 10.1145/2523813.",
    "massey51": "F. J. Massey, \"The Kolmogorov-Smirnov test for goodness of fit,\" *J. Amer. Statist. Assoc.*, vol. 46, no. 253, pp. 68–78, 1951, doi: 10.1080/01621459.1951.10500769.",
    "yurdakul20": "B. Yurdakul and J. Naranjo, \"Statistical properties of the population stability index,\" *J. Risk Model Validation*, 2020, doi: 10.21314/JRMV.2020.227.",
    "bh95": "Y. Benjamini and Y. Hochberg, \"Controlling the false discovery rate: A practical and powerful approach to multiple testing,\" *J. Roy. Statist. Soc. Ser. B*, vol. 57, no. 1, pp. 289–300, 1995, doi: 10.1111/j.2517-6161.1995.tb02031.x.",
    "rabanser19": "S. Rabanser, S. Günnemann, and Z. C. Lipton, \"Failing loudly: An empirical study of methods for detecting dataset shift,\" arXiv:1810.11953, 2019.",
    "leminen12": "S. Leminen, M. Westerlund, and A.-G. Nyström, \"Living labs as open-innovation networks,\" *Technol. Innov. Manage. Rev.*, vol. 2, no. 9, pp. 6–11, 2012, doi: 10.22215/timreview/602.",
}
order = []


def cite(*keys):
    nums = []
    for k in keys:
        assert k in REFS, k
        if k not in order:
            order.append(k)
        nums.append(order.index(k) + 1)
    return ", ".join(f"[{n}]" for n in sorted(nums))


# ---------------------------------------------------------------------
# Inputs: Milestones 2-4
# ---------------------------------------------------------------------
m4 = json.loads((ROOT / "Dataset" / "clean" / "m4_params.json").read_text(encoding="utf-8"))
m5 = json.loads((ROOT / "Dataset" / "clean" / "m5_params.json").read_text(encoding="utf-8"))
assert m5["fast_run"] is False or os.environ.get("M5_ALLOW_FAST") == "1", "the tables come from a FAST debugging run; rerun data_extension.ipynb in full"
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
grp = tab("m4_groups")
leak = tab("m3_leakage_check").set_index(["model", "scheme"])
h2t = tab("m3_h2_logit", index_col=0)
onset = tab("m3_errors_onset").set_index(["model", "outcome", "day_type"])["count"]
cvr = tab("cone_vs_radius", index_col=[0, 1])
wtr = tab("weather_trap_harvest")
mo = tab("groupby_month", index_col=0)
orat = tab("m3_odds_ratios").set_index(["feature_set", "feature"])
HEAD = "Training Oct-Dec (headline)"
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


# ---------------------------------------------------------------------
# Inputs: Milestone 5
# ---------------------------------------------------------------------
dims = tab("m5_dataset_dims").set_index("data")
bal = tab("m5_split_balance").set_index("rows")
qa = tab("m5_quality_audit").set_index("check")
rep = tab("m5_reproduction")
frz = tab("m5_frozen_check")
act = tab("m5_schema_actions")
drift = tab("m5_drift_features")
dmon = tab("m5_drift_monthly")
dtier = tab("m5_drift_tier")
dom = tab("m5_domain_auc").set_index(["comparison", "features"])["cv_roc_auc"]
tsh = tab("m5_target_shift")
con = tab("m5_concept_test").set_index("term")
csum = tab("m5_concept_summary").assign(term=lambda d: d.term.str.replace("JOINT: ", "")).set_index("term")["value"]
cal = tab("m5_calibration")
msk = tab("m5_monthly_skill")
three = tab("m5_three_way")
tc = tab("m5_three_way_counts")
d5 = tab("m5_deltas").set_index(["comparison", "metric"])
gap = tab("m5_fire_gap_sensitivity")
rts = tab("m5_retrain_summary").set_index("model")
fsh = tab("m5_fair_shift")
fgr = tab("m5_fair_groups")
fdl = tab("m5_fair_deltas").set_index(["rule", "grouping", "metric"])
expo = tab("m5_exposure")
rel = tab("m5_label_relearned")
thrr = tab("m5_label_relearned_thresholds").set_index("city")

LAB = {"lr_full": "LR full", "dt_full": "DT full", "rf_full": "RF full", "hgb_full": "HGB full"}
FINAL5, BEST5 = LAB[m5["final_model"]], LAB[m5["best_ensemble"]]
S1 = "(1) initial model, initial data (Sep-Dec 2023)"
S2A = "(2a) initial model, zero-shot, all of 2024"
S2B = "(2b) initial model, zero-shot, Sep-Dec 2024"
S3A = "(3a) re-trained model, Sep-Dec 2024 test"
S3B = "(3b) re-trained model, combined data, purged CV"
SM, WW = "season-matched (Sep-Dec)", "whole wave"


def M3(setting, model, metric, col="estimate"):
    r = three[(three.setting == setting) & (three.model == model) & (three.metric == metric)]
    return float(r[col].iloc[0])


def M3CI(setting, model, metric, d=3):
    return ci(M3(setting, model, metric), M3(setting, model, metric, "ci_low"), M3(setting, model, metric, "ci_high"), d)


def TCN(setting, model, col):
    return tc[(tc.setting == setting) & (tc.model == model)][col].iloc[0]


def DL5(comp, metric, col="test_diff"):
    return float(d5.loc[(comp, metric), col])


def DL5CI(comp, metric, d=3):
    return ci(DL5(comp, metric), DL5(comp, metric, "ci_low"), DL5(comp, metric, "ci_high"), d)


def DR(feature, comp, col):
    return drift[(drift.feature == feature) & (drift.comparison == comp)][col].iloc[0]


def TS(period, grouping, group, col):
    return tsh[(tsh.period == period) & (tsh.grouping == grouping) & (tsh.group == group)][col].iloc[0]


def FS(setting, model, rule, grouping, metric, col="estimate"):
    r = fsh[(fsh.setting == setting) & (fsh.model == model) & (fsh.rule == rule) & (fsh.grouping == grouping) & (fsh.metric == metric)]
    return float(r[col].iloc[0])


def FSCI(setting, model, rule, grouping, metric, d=3):
    return ci(*(FS(setting, model, rule, grouping, metric, c) for c in ["estimate", "ci_low", "ci_high"]), d)


def FGR(setting, model, rule, grouping, group, col):
    r = fgr[(fgr.setting == setting) & (fgr.model == model) & (fgr.rule == rule) & (fgr.grouping == grouping) & (fgr.group == group)]
    return float(r[col].iloc[0])


def FDL(rule, grouping, metric, col="retrained_minus_zero_shot"):
    return float(fdl.loc[(rule, grouping, metric), col])


def EX(setting, group, col):
    return expo[(expo.setting == setting) & (expo.group == group)][col].iloc[0]


FS1, FS2A, FS2B, FS3A = "(1) initial, Sep-Dec 2023", "(2a) zero-shot, all 2024", "(2b) zero-shot, Sep-Dec 2024", "(3a) re-trained, Sep-Dec 2024"
R1, RT, REO = "single threshold", "threshold per tier", f"equalized odds, ε = {EPS}"
CT = "city-size tier"

# Frequently used numbers
be_lr, n_lr = be_ratio("LR full")
fpr_lr = {t: FG("LR full", VAL, CT, t, "fpr") for t in TIERS}
fpr_pt = {t: MG("LR full", PT, VAL, t, "fpr") for t in TIERS}
cost_single_v, cost_pt_v = MIT("LR full", "none", VAL, "cost_per_1000"), MIT("LR full", PT, VAL, "cost_per_1000")
N_I, N_N, N_T = (int(dims.loc[k, "city_days_N"]) for k in ["initial wave", "new wave (2024)", "total"])
P_T = int(dims.loc["total", "master_columns_P"])
rate_ref_all, rate_new_all = TS(WW, "all", "all cities", "rate_ref"), TS(WW, "all", "all cities", "rate_new")
rate_ref_sm, rate_new_sm = TS(SM, "all", "all cities", "rate_ref"), TS(SM, "all", "all cities", "rate_new")
nov = tsh[(tsh.grouping == "month") & (tsh.group.astype(str).str.zfill(2) == "11")].iloc[0]
gap_dates_2024 = [d for d in m5["fire_gap_days"] if d.startswith("2024")]
sig_sm = drift[(drift.comparison == SM) & (drift.significant_q05 == 1)]
n_feat_tested = int((drift.comparison == SM).sum())
psi_mod_sm = drift[(drift.comparison == SM) & (drift.psi >= 0.10)].sort_values("psi", ascending=False)
psi_mod_ww = drift[(drift.comparison == WW) & (drift.psi >= 0.10)].sort_values("psi", ascending=False)
LR_SET = {"lr_p": csum["lr_p"], "wald_p": csum["wald_cluster_p"]}
con_sig = con[(con.p_interaction_cluster < 0.05) & ~con.index.str.startswith("wave")]
cal_v = cal[(cal.bin == "ALL")].set_index("setting")
lr_zs_pr, lr_i_pr, lr_rt_pr = M3(S2B, "LR full", "pr_auc"), M3(S1, "LR full", "pr_auc"), M3(S3A, FINAL5, "pr_auc")
TERM_LABEL = {"persist_margin": "Today's index margin", "temp_mean_c": "Mean temperature", "stagnant": "Stagnant air",
              "rh_mean_pct": "Relative humidity", "temp_range_c": "Temperature range", "vec_len_kmh": "Vector-mean wind",
              "fire_log1p": "Upwind fires (log)"}


N_TEST_SPIKES = int(bal.loc["re-training: test (Sep-Dec 2024)", "spikes"])
assert N_TEST_SPIKES == int(TS(SM, "all", "all cities", "spikes_new"))
# Directional claims in the text, checked against the tables
assert len(psi_mod_sm) < n_feat_tested / 2, "'Most feature shifts were small'"
assert dom[(WW, "all model features (no month, no city)")] < 0.6, "'weakly for the whole wave'"
assert csum["lr_p"] < 0.05 and len(con_sig) > 0, "'the relation changed'"
assert M3(S2B, "LR full", "precision") > M3(S1, "LR full", "precision") and M3(S2B, "LR full", "f1") > M3(S1, "LR full", "f1"), "'Precision and F1 rose'"
assert M3(S2B, "LR full", "cost_per_1000") > M3(S1, "LR full", "cost_per_1000"), "'cost of errors grew'"
assert cal[(cal.bin == "ALL") & (cal.setting == "zero-shot, Sep-Dec 2024")].pipe(lambda d: (d.mean_predicted < d.observed_rate).all()), "'under-predicted'"
assert m5["final_model"] == "lr_full", "text assumes LR full stays the final model"
assert not d5.loc[("LR full (re-trained) − LR full (zero-shot)", "pr_auc"), "ci_excludes_0"], "'did not raise the ranking skill of the final model'"
assert DL5("LR full (zero-shot) − Persistence", "cost", "ci_high") < 0, "'still cheaper than persistence'"
assert all(not fdl.loc[(R1, g, m), "ci_excludes_0"] for g in ["country", CT] for m in ["eo_diff", "pe_diff", "eop_diff", "dp_diff", "dir_vs_priv_max"]), "'single-threshold gaps within uncertainty'"
assert all(TS(SM, "tier", t, "rate_new") > TS(SM, "tier", t, "rate_ref") for t in TIERS), "'Every tier saw more spikes'"
assert DR("fire_cnt_r300_all", SM, "new_mean") < DR("fire_cnt_r300_all", SM, "ref_mean") and DR("fire_cnt_up45_r300_in", SM, "new_mean") < DR("fire_cnt_up45_r300_in", SM, "ref_mean")
assert all(FGR(FS2B, "LR full", R1, CT, t, "fpr") > FGR(FS1, "LR full", R1, CT, t, "fpr") for t in TIERS), "'false-alarm rate rose in every tier'"
mp_t1 = EX(FS2B, T1, "missed_person_days_m") / EX(FS2B, "all cities", "missed_person_days_m")
assert mp_t1 > 0.5, "'most in Pakistani metros' (Tier 1 = Lahore, Faisalabad, Rawalpindi)"
THR4 = m4["mitigation_thresholds"]["LR full"][PT]
THR5 = m5["final_model_thresholds"][RT]
spread4, spread5 = max(THR4.values()) - min(THR4.values()), max(THR5.values()) - min(THR5.values())
assert spread5 < spread4 / 2, "'per-tier thresholds nearly converge'"
assert fdl.loc[(RT, CT, "dir_vs_priv_max"), "ci_excludes_0"], "'tier DIR higher than with the Milestone 4 tier thresholds'"


def updown(a, b, up="rose", down="fell", same="stayed level"):
    return up if b > a else down if b < a else same


# =====================================================================
# Front matter (one column)
# =====================================================================
blocks.append({"t": "title", "text": "Forecasting Trans-Boundary Smog Spikes in Punjab under Data Drift: A Leakage-Free, Fairness-Audited Alert Tested on a 2024 Wave"})
blocks.append({"t": "authors", "text": "Munir Tariq, Ismail Nooruddin, Bilal Ayub"})
blocks.append({"t": "affil", "text": "Data Science for Social Good, Habib University, Karachi, Pakistan"})
blocks.append({"t": "abstract", "items": [
    "Crop-fire smoke and city emissions collect over the Punjab plain each winter, on both sides of the Pakistan–India border. "
    "We built a next-day smog-spike alert for 11 cities and tested whether it stays accurate and fair on a new year of data. "
    f"We merged CAMS air quality, weather and VIIRS fire detections into {N_I:,} city-days (August 2022–December 2023), then ingested a 2024 wave of {N_N:,} city-days with the same automated pipeline. "
    "A spike is a day above the city's 90th percentile of a Composite Smog Index. "
    "We compared persistence, logistic regression (LR), a decision tree, a random forest and gradient boosting under purged, week-grouped cross-validation and a 5:1 cost of a missed spike to a false alarm. "
    "We audited the alerts by country and census city-size tier and tested reweighing and tier-specific thresholds. "
    f"A sparse LR on today's index margin and temperature matched persistence on ranking (PR-AUC {f(lr_i_pr, 3)} against {f(M3(S1, 'Persistence', 'pr_auc'), 3)}) and cost less at every cost ratio from {be_lr}:1. The ensembles did not improve on it. "
    f"In 2024 the next-day spike rate rose from {pct(rate_ref_all)}% to {pct(rate_new_all)}%. Most feature shifts were small, but the relation between stagnation, fires and spikes changed (likelihood-ratio p {pv(LR_SET['lr_p'])}). "
    f"Applied unchanged to September–December 2024, the LR kept a PR-AUC of {f(lr_zs_pr, 3)}. Re-training on the combined data gave {f(lr_rt_pr, 3)}. "
    "The model under-predicted the higher 2024 spike rate, and the cost of errors grew. Under one threshold, the fairness gaps between tiers did not change beyond their uncertainty. "
    "We recommend a monitored, re-calibrated alert with tier thresholds and human review."]})
blocks.append({"t": "indexterms", "text": "Air pollution, early warning, concept drift, dataset shift, algorithmic fairness, cross-validation, crop-residue burning, Punjab."})
section("two")

# =====================================================================
# I. Introduction
# =====================================================================
h1("Introduction")
p("Every October and November, farmers in Indian and Pakistani Punjab burn rice stubble to clear fields for wheat. "
  "The smoke joins city emissions under cold, still winter air. Fine-particle levels in Lahore, Faisalabad and the Indian Punjab cities then rise far above the "
  f"WHO 24-hour guideline of 15 µg/m³ {cite('who21')}. "
  f"Governments respond with school closures, traffic limits and kiln bans {cite('epd', 'dawn24')}. These measures need a warning, and the warning must be right.")
p("Two features shape the problem. First, smoke crosses the border, so a city's air depends on fires it does not control. "
  "Second, an alert has two errors with unequal costs. A missed spike leaves children, the elderly and outdoor workers exposed. "
  "A false alarm closes schools and stops daily-wage work for nothing. Both costs fall on people, and they may fall unevenly across places. "
  "A third feature emerged in our final milestone: the data change from year to year. An alert tuned on one winter must survive the next.")
p("The work serves SDG 3 (targets 3.9 and 3.d: illness from air pollution and early warning), SDG 11 (target 11.6: urban air quality) and SDG 13 (climate action). "
  "The cross-border question also relates to SDG 17.")
p(f"Satellite and transport-model studies link post-monsoon residue fires to winter smog downwind {cite('cusworth18', 'jethva19', 'tariq15')}. "
  f"Machine-learning models of air quality are common {cite('rybarczyk18')}, but they rarely test whether fire counts add next-day skill beyond today's air quality, "
  "whether the alert treats places fairly, or whether it survives a new year of data.")
p("**Research hypotheses.** Each uses only information known on day *t*:", noindent=True)
bullets(["**H1** Fires in the upwind cone raise the next-day smog index beyond the plain radius count.",
         "**H2** Stagnation, humidity, no rain and a large day–night temperature range each raise the odds of a spike.",
         "**H3** The fire effect is stronger on stagnant days.",
         "**H4** India-origin fires raise the next-day index in Pakistani cities, more near the border.",
         "**H5** A model with fire and weather features beats persistence and a weather-only model.",
         "**H6** The learned relation holds on a new year (no concept drift), and the alert keeps its skill and fairness."])
p("**Contributions.** (i) An audited, automated city-day dataset for 11 cross-border cities, extended to a 2024 wave. "
  "(ii) A leakage-free comparison of five model families against persistence under asymmetric costs. "
  "(iii) A geographic fairness audit with bias mitigation and a Pareto analysis. "
  "(iv) Drift tests, zero-shot and re-trained evaluation, and a fairness re-audit on the new wave. "
  "(v) FATEN-based governance recommendations for a living-lab pilot.", noindent=True)

# =====================================================================
# II. Data
# =====================================================================
h1("Data Curation and Master Dataset Inventory")
h2("Sources")
p("The study covers 11 cities: Lahore, Faisalabad, Multan, Rawalpindi, Sialkot, Rahim Yar Khan and Islamabad in Pakistan, and Amritsar, Ferozepur, Ludhiana and Jalandhar in India. "
  f"Air quality comes from the CAMS model {cite('inness19')} through the Open-Meteo API {cite('zipp23')}, which also supplies the weather. "
  f"Fire detections come from the VIIRS 375 m product {cite('schroeder14')} through NASA FIRMS {cite('firms')}. "
  f"Air quality and weather are gridded model estimates, not monitor readings. {next_table()} lists the streams for both waves.")
lud = qa
table("Data streams for the initial wave and the 2024 wave",
      ["Stream", "Source", "Processing", "Initial", "2024"],
      [["Air quality", "Open-Meteo (CAMS), hourly, 7 pollutants", "Negatives to 0; gaps ≤ 6 h interpolated; days with ≥ 18 valid hours; index and spike label",
        f"{int(qa.loc['city-days kept (>= 18 valid hours)', 'initial']):,}", f"{int(qa.loc['city-days kept (>= 18 valid hours)', 'new']):,}"],
       ["Weather", "Open-Meteo, hourly", "Daily means, range, rain total; vector-mean wind; stagnant < 2 km/h",
        f"{N_I:,}", f"{N_N:,}"],
       ["Fire", "NASA FIRMS VIIRS, points", "Study box, vegetation fires, nominal/high confidence; counts by cone, radius, origin",
        f"{N_I:,}", f"{N_N:,}"],
       ["Master", "Joins on city, country, date", f"Lags and targets within city; {P_T} columns", f"{N_I:,}", f"{N_N:,}"]],
      [1000, 1350, 1850, 420, 420], align="left",
      note=f"City-days per wave. Initial: 4 Aug 2022–31 Dec 2023. 2024: 1 Jan–29 Dec 2024. N_total = {N_I:,} + {N_N:,} = {N_T:,}.")
h2("Automated ingestion and schema reconciliation")
lead_ok = int(rep["cells_differing_from_lead_in"].sum()) == 0
_bad = rep[rep.cells_differing_from_lead_in > 0]
assert (_bad.table == "master_daily").all() and all(c.strip().startswith("target_") for cs in _bad.columns_differing for c in cs.split(",")), "only the Dec-2023 next-day targets may differ"
p("One module ports the three per-stream cleaning notebooks into functions that take the date window as an argument. "
  "It reads the raw files, reconciles them and writes the daily tables that the merge reads. "
  "The 2024 rows get the z-scores, log decisions, index weights and spike thresholds learned on the 2022–23 training rows. "
  "Nothing is re-learned, so the label definition stays fixed. "
  f"A rebuild of 2022–23 with the same code reproduced every committed table cell inside the modelling window{' (0 differing cells)' if lead_ok else ''}. "
  "The only exceptions are the next-day targets of 29–31 December 2023, which now point into 2024 instead of being empty. "
  f"Re-learning the frozen parameters on the training rows gave the same values to within {frz['max_abs_diff'].max():.0e}. "
  "The only difference outside the window was one rain-day flag, caused by floating-point summation order.")
p("The reconciliation handled six kinds of difference (Appendix, Table A1): two file formats (.csv and .xlsx), three column orders, "
  "inconsistent file names, GMT and UTC clocks shifted to UTC+5 before taking the date, an early end of one weather file and missing satellite days. "
  f"Columns are renamed by name, never by position. The Ludhiana weather file ends on 29 December 2024, so the window ends there for every stream. "
  f"VIIRS has no detection anywhere in India or Pakistan on {len(gap_dates_2024)} dates of 2024, including 3–5 November in the burning season. "
  "We flag these dates and keep the counts at 0, as in 2022–23, and a sensitivity run drops the affected rows.")
h2("Target and predictors")
p("The **Composite Smog Index** is 0.40·z(PM2.5) + 0.12·[z(PM10) + z(NO2) + z(SO2) + z(O3) + z(CO)], with log(1 + x) on skewed pollutants. "
  "A **spike** is a day whose index reaches the 90th percentile of that city's training October–March days. "
  f"The thresholds run from {f(grp.spike_threshold.min())} to {f(grp.spike_threshold.max())}. "
  "The model predicts the spike label of day *t* + 1 from 42 features of day *t*: "
  "today's index and its two lags as the margin over the city threshold, upwind fires (±45° cone, 300 km, lags 0–3), "
  "14 weather features and 21 month and city dummies. The **no-fire** set drops the 4 fire columns, and the **weather-only** set also drops the 3 index columns.")
p(f"After dropping rows without a target or with flagged days, the expanded data hold {int(dims.loc['total', 'model_rows_after_drops']):,} modelling rows "
  f"({int(dims.loc['initial wave', 'model_rows_after_drops']):,} initial, {int(dims.loc['new wave (2024)', 'model_rows_after_drops']):,} new) "
  f"and {int(dims.loc['total', 'spikes_next_day'])} next-day spikes. P_total = {P_T} master columns.")

# =====================================================================
# III. EDA
# =====================================================================
h1("Exploratory Data Analysis and Driver Analysis")
hv = cvr.loc[(HEAD, "All Pakistani (7)")]
st, hu, rf_ = wtr.iloc[0], wtr.iloc[1], wtr.iloc[2]
p(f"Spikes cluster in December ({f(mo.loc[12, 'spike_share_pct'], 1)}% of training city-days) and January ({f(mo.loc[1, 'spike_share_pct'], 1)}%). "
  f"October and November have {f(mo.loc[10, 'spike_share_pct'], 1)}% and {f(mo.loc[11, 'spike_share_pct'], 1)}%, although fires peak then. "
  "Fires alone therefore do not make a spike. Winter weather must trap the smoke.")
p(f"In the training harvest season, fires in the ±45° upwind cone at 300 km correlate with next-day smog (median Spearman ρ = {f(hv['upwind cone (up45, 300 km)'])} over the Pakistani cities). "
  f"The plain circle gives {f(hv['no cone (300 km)'])} and a downwind placebo cone {f(hv['downwind placebo (down45, 300 km)'])}. "
  f"After a stagnant day, {f(st['spike_rate_with_pct'], 1)}% of next days were spikes, against {f(st['spike_rate_without_pct'], 1)}% otherwise. "
  f"Humid days gave {f(hu['spike_rate_with_pct'], 1)}% against {f(hu['spike_rate_without_pct'], 1)}%. No rain day was followed by a spike (0 of {int(rf_['days_without'])}).")
h1_p, h4_p = H("H1", SPEC_A, CONE, "p_one_sided_city"), H("H4", SPEC_A, IN, "p_one_sided_city")
fisher_p = h2t.loc["rain_day (Fisher exact, all train rows)", "p_one_sided_city"]
table("Hypothesis tests on the training rows",
      ["", "Evidence", "Verdict"],
      [["H1", f"β_cone {f(H('H1', SPEC_A, CONE, 'coef'), 3)}, p {pv(h1_p)}; with today's index p {pv(H('H1', SPEC_B, CONE, 'p_one_sided_city'))}; placebo {f(H('H1 placebo', SPEC_A, DOWN, 'coef'), 3)}", "Supported" if h1_p < 0.05 else "No"],
       ["H2", f"OR stagnant {f(h2t.loc['stagnant', 'odds_ratio'])}, humidity {f(h2t.loc['rh_mean_pct_sd', 'odds_ratio'])}/SD, temp. range {f(h2t.loc['temp_range_c_sd', 'odds_ratio'])}/SD; rain Fisher p {pv(fisher_p)}", "Supported"],
       ["H3", f"β_fire×stagnant {f(H('H3', SPEC_A, 'cone_x_stagnant', 'coef'), 3)}", "Supported" if H("H3", SPEC_A, "cone_x_stagnant", "p_one_sided_city") < 0.05 else "No"],
       ["H4", f"β_IN {f(H('H4', SPEC_A, IN, 'coef'), 3)}, p {pv(h4_p)}; Pakistan-origin {f(H('H4', SPEC_A, PKF, 'coef'), 3)}", "Supported" if h4_p < 0.05 else "No"],
       ["H5", f"LR − persistence ΔPR-AUC {DCI('LR full − Persistence', 'pr_auc')}; cheaper from {be_lr}:1", "Partly"]],
      [300, 3700, 900], align="left",
      note="H1, H3, H4: OLS of the next-day index, city-clustered SE, one-sided p. H2: Logit on rain-free Sep–Feb days. Fire terms per SD of log(1 + count). H5: validation.")
aq_imp = imp.loc[("LR full", "AQ history (today, lags 1–2)"), "mean"]
p(f"**Drivers.** Shuffling the AQ-history columns costs {f(aq_imp, 3)} of validation PR-AUC for LR, and shuffling the fire columns costs at most "
  f"{f(max(imp.loc[(m, 'Upwind fires (t, lags 1–3)'), 'mean'] for m in ['LR full', 'RF full', 'HGB full']), 3)} for any model. "
  f"The L1-penalised LR keeps two of 42 columns: today's margin (OR {f(orat.loc[('full', 'persist_margin'), 'odds_ratio'])} per SD) "
  f"and mean temperature (OR {f(orat.loc[('full', 'temp_mean_c'), 'odds_ratio'])} per SD). "
  "Fires shape smog levels (H1), but their smoke is already in today's index when the alert is issued.")

# =====================================================================
# IV. Modelling
# =====================================================================
h1("Predictive Modeling and Architecture Evaluation")
h2("Leakage-free validation")
la = leak.loc[("LR full", "(a) random stratified 80/20 split"), "pr_auc_mean"]
ld = leak.loc[("LR full", "(d) purged + embargoed 5 × 5 StratifiedGroupKFold (ours)"), "pr_auc_mean"]
p("The outer split is chronological: training 6 August 2022–31 August 2023 (4,246 city-days, 204 spikes), validation 4 September–30 December 2023 (1,298, 89). "
  "Inside training we use purged, repeated StratifiedGroupKFold (5 folds × 5 repeats). The group is the calendar week shared by all cities. "
  "The purge drops fit rows whose target day is held out, and an embargo drops rows whose index lags contain a held-out day. "
  f"On the same rows, a random stratified split scores LR at PR-AUC {f(la, 3)} against {f(ld, 3)} for our design, "
  f"so random splits overstate skill {cite('roberts17')}. We rank models by PR-AUC, which suits rare events {cite('saito15')}.")
h2("Models and hyperparameter search")
p(f"Persistence (\"tomorrow repeats today\") is the benchmark. LR and a decision tree (DT) are the baselines, tuned by grid search. "
  f"A random forest (RF) {cite('breiman01')} and histogram gradient boosting (HGB) {cite('friedman01', 'ke17')} are the advanced models, tuned by random search with 60 draws {cite('bergstra12')}. "
  f"All searches used the same 25 folds and scikit-learn pipelines {cite('pedregosa11')}. The regressions used statsmodels {cite('seabold10')}. HGB early stopping was off, because its random hold-out leaks neighbouring days. "
  "The final-model rule was fixed in advance: the highest CV PR-AUC among the full-feature models, with ties within 0.005 going to the simpler model.")
SHOWM = ["Persistence", "LR full", "DT full", "RF full", "HGB full"]
rows = [[m, f(V(m, "accuracy"), 3), f(V(m, "precision"), 3), f(V(m, "recall"), 3), f(V(m, "f1"), 3), f(V(m, "roc_auc"), 3),
         f(V(m, "pr_auc"), 3), f(V(m, "cost_per_1000"), 1), f(CV(m, "pr_auc"), 3)] for m in SHOWM]
tb_m4 = table("Validation, Sep–Dec 2023, at the 5:1 thresholds", ["Model", "Acc.", "Prec.", "Rec.", "F1", "ROC", "PR", "Cost", "CV PR"],
              rows, [1150, 520, 520, 520, 480, 520, 480, 520, 520],
              note="ROC, PR = ROC-AUC and PR-AUC. Cost = (5·FN + FP) per 1,000 city-days. CV PR = mean PR-AUC over 25 purged folds.")
p(f"**The ensembles do not beat LR** ({tb_m4}). RF reaches a validation PR-AUC of {f(V('RF full', 'pr_auc'), 3)} and HGB {f(V('HGB full', 'pr_auc'), 3)}, "
  f"against {f(V('LR full', 'pr_auc'), 3)} for LR. RF − LR is {DCI('RF full − LR full', 'pr_auc')}, and RF wins {int(D('RF full − LR full', 'pr_auc', 'cv_folds_a_better'))} of 25 CV folds. "
  f"Both ensembles beat the tree on CV PR-AUC. Under the fixed rule, LR full is the final model. "
  f"**Accuracy misleads:** never alerting scores {pct(V('Majority class', 'accuracy'))}% accuracy. "
  f"**Persistence is hard to beat on ranking**, but LR catches {int(onset.loc[('LR full', 'TP', 'onset')])} of the {int(onset.loc[('Persistence', 'FN', 'onset')])} onset days that persistence misses by construction.")
h2("Asymmetric costs")
p(f"We weight a missed spike as five false alarms. This is a stated policy assumption, informed by the health burden of air pollution {cite('pandey21')}. "
  "Each model's threshold minimises 5·FN + FP on its out-of-fold training predictions. "
  f"At 5:1 LR costs {f(cw.loc[5, 'LR full'], 1)} per 1,000 city-days, against {f(cw.loc[5, 'Persistence'], 1)} for persistence and {f(V('Majority class', 'cost_per_1000'), 1)} for never alerting ({next_fig()}). "
  f"LR is cheaper than persistence at {n_lr} of 20 ratios, from {be_lr}:1 upwards.")
figure("figures/fig_m05_paper_7_cost_curve.png", "Validation cost per 1,000 city-days against the FN:FP ratio (Sep–Dec 2023). Thresholds are re-chosen on out-of-fold training predictions at each ratio. Dashed line: the 5:1 headline.")

# =====================================================================
# V. Fairness
# =====================================================================
h1("Algorithmic Bias, Fairness and Ethics Audit")
h2("Sensitive attributes and metrics")
p("Our units are places, so the sensitive attribute is **geography**: country (Pakistan, India) and a city-size tier from census population, a socio-economic proxy. "
  f"Tier 1 metros have ≥ 3 million people (Lahore, Faisalabad, Rawalpindi), Tier 2 1–3 million (Multan, Ludhiana, Amritsar, Islamabad) and Tier 3 < 1 million (Jalandhar, Sialkot, Rahim Yar Khan, Ferozepur) {cite('pbs25')}. "
  "Small cities have fewer monitors and less administrative capacity. "
  f"An alert is the positive prediction. We compute the disparate impact ratio (DIR) with the 80% rule read two-sided (0.8–1.25) {cite('feldman15')}, "
  f"equal opportunity (ΔTPR), predictive equality (ΔFPR) and equalized odds {cite('hardt16')}. "
  f"With unequal base rates, these criteria cannot all hold at once {cite('chouldechova17', 'mehrabi21')}.")
h2("Audit results")
base_v = {t: FG("LR full", VAL, CT, t, "base_rate") for t in TIERS}
p(f"**Error rates are similar across countries:** recall {pct(FG('LR full', VAL, 'country', 'Pakistan', 'tpr'))}% in Pakistan and {pct(FG('LR full', VAL, 'country', 'India', 'tpr'))}% in India, "
  f"false-alarm rates {pct(FG('LR full', VAL, 'country', 'Pakistan', 'fpr'))}% and {pct(FG('LR full', VAL, 'country', 'India', 'fpr'))}%. "
  f"**Small cities bear more false alarms:** {pct(fpr_lr[T3])}% of clean days in Tier 3 against {pct(fpr_lr[T1])}% in metros "
  f"(ΔFPR {ci(FD('LR full', VAL, CT, 'pe_diff'), FD('LR full', VAL, CT, 'pe_diff', 'ci_low'), FD('LR full', VAL, CT, 'pe_diff', 'ci_high'))}). "
  f"The tier DIR of {f(FD('LR full', VAL, CT, 'dir_vs_priv_max'))} fails the 80% rule, but Tier 3 also had {pct(base_v[T3])}% spike days against {pct(base_v[T1])}% in metros. "
  "Demographic parity is the wrong target here. Equalized odds fits the problem better.")
h2("Mitigation and the fairness–accuracy trade-off")
p(f"Reweighing {cite('kamiran12')} barely changes the LR alerts, because each city's own threshold equalises the training base rates by design. "
  f"Per-tier 5:1 thresholds, chosen on out-of-fold predictions, cut the small-city false-alarm rate from {pct(fpr_lr[T3])}% to {pct(fpr_pt[T3])}%. "
  f"They lower the cost from {f(cost_single_v, 1)} to {f(cost_pt_v, 1)} per 1,000 city-days, with recall {f(MIT('LR full', 'none', VAL, 'recall'), 3)} → {f(MIT('LR full', PT, VAL, 'recall'), 3)}. "
  f"Equalized-odds thresholds at ε = {f(EPS)} give the same validation result. "
  f"On training data, tightening ε trades cost for fairness along a Pareto frontier ({next_fig()}). The frontier is flat down to an equalized-odds gap of about 0.02 and then turns steeply up.")
figure("figures/fig_m05_paper_6_pareto.png", "Fairness–accuracy trade-off across city-size tiers (training out-of-fold predictions): cost against the equalized-odds gap for every threshold rule and reweighing strength. Lines join the Pareto-efficient rules.")

# =====================================================================
# VI. Data expansion, drift and re-training
# =====================================================================
h1("Data Expansion, Drift and Model Re-training")
h2("Design")
p(f"Dataset shift can affect the inputs (covariate shift), the label frequency (prior shift) or the relation between them (concept drift) {cite('morenotorres12', 'gama14')}. "
  f"We compare the initial wave with 2024 using two-sample Kolmogorov–Smirnov tests {cite('massey51')} for continuous features, χ² tests for categorical ones "
  f"and the Population Stability Index (PSI) {cite('yurdakul20')} with 10 reference-decile bins. "
  f"P-values get the Benjamini–Hochberg correction {cite('bh95')}. PSI bands: < 0.10 stable, 0.10–0.25 moderate, ≥ 0.25 major. "
  "The initial wave holds two Aug–Dec seasons but one Jan–Jul, so we also compare Sep–Dec only (season-matched). "
  f"A domain classifier tests the joint shift {cite('rabanser19')}. "
  "The concept test is a pooled logit with 2024 × predictor interactions on rain-free Sep–Feb days, with city fixed effects.")
p("**Evaluation settings.** (1) The saved Milestone 4 model on its own validation season, Sep–Dec 2023. "
  "(2) The same model and thresholds on 2024 without re-training (zero-shot): (2a) all of 2024 and (2b) Sep–Dec 2024. "
  f"(3) Models re-trained on {int(bal.loc['re-training: train', 'city_days']):,} rows from 2022-08 to 2024-08 with the same CV and search: "
  f"(3a) on the held-out Sep–Dec 2024 season ({int(bal.loc['re-training: test (Sep-Dec 2024)', 'city_days']):,} city-days, {int(bal.loc['re-training: test (Sep-Dec 2024)', 'spikes'])} spikes) and "
  "(3b) purged CV over the whole combined dataset.")
h2("Covariate shift")
dsm, dww = dom[(SM, "all model features (no month, no city)")], dom[(WW, "all model features (no month, no city)")]
p(f"With thousands of rows per wave, {len(sig_sm)} of {n_feat_tested} features differ significantly in the season-matched comparison (q < 0.05). "
  f"Most shifts are small ({next_fig()}). "
  + (f"The largest season-matched PSI is {f(psi_mod_sm.iloc[0].psi)} for {psi_mod_sm.iloc[0].label.split(' (')[0].lower()}"
     + (f", and {len(psi_mod_sm) - 1} more features reach the moderate band. " if len(psi_mod_sm) > 1 else ". ")
     if len(psi_mod_sm) else "No feature reaches the moderate PSI band. ")
  + f"Fewer fires burned within 300 km in Sep–Dec 2024 (mean {f(DR('fire_cnt_r300_all', SM, 'new_mean'), 1)} against {f(DR('fire_cnt_r300_all', SM, 'ref_mean'), 1)} per city-day). "
  f"India-origin upwind fires fell from {f(DR('fire_cnt_up45_r300_in', SM, 'ref_mean'), 1)} to {f(DR('fire_cnt_up45_r300_in', SM, 'new_mean'), 1)}, and Pakistan-origin ones {updown(DR('fire_cnt_up45_r300_pk', SM, 'ref_mean'), DR('fire_cnt_up45_r300_pk', SM, 'new_mean'))} "
  f"from {f(DR('fire_cnt_up45_r300_pk', SM, 'ref_mean'), 1)} to {f(DR('fire_cnt_up45_r300_pk', SM, 'new_mean'), 1)}. "
  f"Stagnant days {updown(DR('stagnant', SM, 'ref_mean'), DR('stagnant', SM, 'new_mean'))} from {pct(DR('stagnant', SM, 'ref_mean'))}% to {pct(DR('stagnant', SM, 'new_mean'))}%, "
  f"and mean PM2.5 from {f(DR('pm2_5_mean_ugm3', SM, 'ref_mean'), 1)} to {f(DR('pm2_5_mean_ugm3', SM, 'new_mean'), 1)} µg/m³. "
  f"The domain classifier separates the waves weakly over the whole wave (ROC-AUC {f(dww, 3)}) and moderately within Sep–Dec ({f(dsm, 3)}).")
figure("figures/fig_m05_paper_2_psi.png", "Population Stability Index of every feature between the initial wave and 2024, whole wave (grey) and Sep–Dec only (orange). Dashed: 0.10 (moderate); solid: 0.25 (major).")
DRIFT_SHOW = ["composite_smog_index", "pm2_5_mean_ugm3", "temp_mean_c", "rh_mean_pct", "vec_len_kmh", "fire_cnt_up45_r300_all",
              "fire_cnt_r300_all", "fire_cnt_up45_r300_in", "stagnant", "wind_sector"]
SHORTL = {"composite_smog_index": "Smog index", "pm2_5_mean_ugm3": "PM2.5 (µg/m³)", "temp_mean_c": "Mean temp. (°C)",
          "rh_mean_pct": "Humidity (%)", "vec_len_kmh": "Wind (km/h)", "fire_cnt_up45_r300_all": "Upwind fires",
          "fire_cnt_r300_all": "Fires 300 km", "fire_cnt_up45_r300_in": "Upwind IN fires", "stagnant": "Stagnant (share)",
          "wind_sector": "Wind sector"}
rows = []
for ft in DRIFT_SHOW:
    r = drift[(drift.feature == ft) & (drift.comparison == SM)].iloc[0]
    means = "–" if pd.isna(r.ref_mean) else f"{f(r.ref_mean, 2 if r.ref_mean < 10 else 1)} → {f(r.new_mean, 2 if r.ref_mean < 10 else 1)}"
    rows.append([SHORTL[ft], "KS" if r.test == "KS" else "χ²", f(r.statistic, 3), pv(r.q_value_bh), f(r.psi, 3), means])
table("Season-matched drift tests, Sep–Dec 2022–23 vs Sep–Dec 2024", ["Feature", "Test", "Stat.", "q (BH)", "PSI", "Mean"], rows,
      [1250, 450, 600, 700, 550, 1350], note="Stat. = KS distance or χ² statistic. All 20 features are in Appendix Table A4.")
h2("Label shift and concept drift")
p(f"**The label shifted most.** With frozen thresholds, the next-day spike rate rose from {pct(rate_ref_all)}% to {pct(rate_new_all)}% overall "
  f"and from {pct(rate_ref_sm)}% to {pct(rate_new_sm)}% in Sep–Dec ({next_fig()}). "
  f"November alone went from {pct(nov.rate_ref)}% to {pct(nov.rate_new)}% of city-days, the month of the November 2024 school closures {cite('dawn24')}. "
  f"Every tier saw more spikes: Tier 3 went from {pct(TS(SM, 'tier', T3, 'rate_ref'))}% to {pct(TS(SM, 'tier', T3, 'rate_new'))}% in Sep–Dec.")
figure("figures/fig_m05_paper_1_label_shift.png", "Share of city-days followed by a spike, by calendar month, with the frozen 2022–23 thresholds.")
sig_txt = ", ".join(f"{TERM_LABEL[t].lower()} (ratio of odds ratios {f(con.loc[t, 'ratio_of_or_new_vs_ref'])} [{f(con.loc[t, 'ratio_lo'])}, {f(con.loc[t, 'ratio_hi'])}])"
                    for t in con_sig.index)
p(f"**The relation changed as well.** Adding the 2024 interactions improves the pooled logit (likelihood-ratio χ² {f(csum['lr_stat'], 1)}, {int(csum['lr_df'])} df, p {pv(csum['lr_p'])}; "
  f"city-cluster Wald p {pv(csum['wald_cluster_p'])}; n = {int(csum['n']):,}, {int(csum['events'])} spikes). "
  + (f"The terms that changed are {sig_txt}. " if len(con_sig) else "No single term changed significantly. ")
  + f"Today's margin stays the strongest predictor in both waves (OR {f(con.loc['persist_margin', 'or_reference_wave'], 1)} per SD before, {f(con.loc['persist_margin', 'or_new_wave'], 1)} in 2024). "
  f"The 2024 intercept shift has a ratio of {f(con.loc['wave (new vs reference), intercept shift', 'ratio_of_or_new_vs_ref'])}, so spikes became likelier at the same predictor values.")
cz, cv23 = cal_v.loc["zero-shot, Sep-Dec 2024"], cal_v.loc["validation, Sep-Dec 2023"]
p(f"**Calibration decays.** The frozen LR predicted a mean spike probability of {f(cz.mean_predicted, 3)} for Sep–Dec 2024, while {f(cz.observed_rate, 3)} of city-days were followed by a spike. "
  f"For Sep–Dec 2023 the figures were {f(cv23.mean_predicted, 3)} and {f(cv23.observed_rate, 3)}. "
  f"The Brier score {updown(cv23.brier, cz.brier)} from {f(cv23.brier, 3)} to {f(cz.brier, 3)} ({next_fig()}).")
figure("figures/fig_m05_paper_3_calibration_time.png", "Observed next-day spike rate and the mean predicted probability of the frozen LR, by month. All predictions are out of sample: out-of-fold for training months, validation for Sep–Dec 2023, zero-shot for 2024.")
h2("Zero-shot generalization and re-training")
TW = ["Persistence", "LR full", "DT full", "RF full", "HGB full"]
SETS = [(S1, "(1)"), (S2A, "(2a)"), (S2B, "(2b)"), (S3A, "(3a)"), (S3B, "(3b)")]
rows = []
for s, sl in SETS:
    for m in TW:
        rows.append([sl, m] + [f(M3(s, m, k), 3) for k in ["accuracy", "precision", "recall", "f1", "roc_auc", "pr_auc"]]
                    + [f(M3(s, m, "cost_per_1000"), 0)])
tb3 = table("Three-way performance audit at the 5:1 thresholds", ["", "Model", "Acc.", "Prec.", "Rec.", "F1", "ROC", "PR", "Cost"], rows,
            [330, 1000, 500, 500, 500, 480, 500, 480, 500], font=7,
            note="(1) Initial model, initial data (Sep–Dec 2023). (2a) Initial model, all 2024; (2b) Sep–Dec 2024 (zero-shot). "
                 "(3a) Re-trained, held-out Sep–Dec 2024. (3b) Re-trained, purged 25-fold CV over the combined data (mean). Cost per 1,000 city-days. CIs: Appendix Table A5.")
dz = DL5("LR full (re-trained) − LR full (zero-shot)", "pr_auc")
p(f"**The ranking skill held** ({tb3}, {next_fig()}). Zero-shot on Sep–Dec 2024, LR full reached PR-AUC {M3CI(S2B, 'LR full', 'pr_auc')}, "
  f"against {f(lr_i_pr, 3)} on its own validation season, and ROC-AUC {updown(M3(S1, 'LR full', 'roc_auc'), M3(S2B, 'LR full', 'roc_auc'))} from {f(M3(S1, 'LR full', 'roc_auc'), 3)} to {f(M3(S2B, 'LR full', 'roc_auc'), 3)}. "
  f"Precision and F1 rose with the higher spike rate. "
  f"**The cost of errors grew** from {f(M3(S1, 'LR full', 'cost_per_1000'), 1)} to {f(M3(S2B, 'LR full', 'cost_per_1000'), 1)} per 1,000 city-days: "
  f"{int(TCN(S2B, 'LR full', 'fn'))} missed spikes and {int(TCN(S2B, 'LR full', 'fp'))} false alarms on {int(TCN(S2B, 'LR full', 'n')):,} city-days. "
  f"Persistence cost {f(M3(S2B, 'Persistence', 'cost_per_1000'), 1)}, so the model still saved {f(-DL5('LR full (zero-shot) − Persistence', 'cost'), 1)} per 1,000 city-days.")
figure("figures/fig_m05_paper_4_three_way.png", "PR-AUC by evaluation setting with 95% week-block bootstrap CIs. For (3b), bars show ±1 SD over the 25 CV folds.")
hgb_sig = bool(d5.loc[("HGB full (re-trained) − HGB full (zero-shot)", "pr_auc"), "ci_excludes_0"])
p(f"**Re-training did not raise the ranking skill of the final model.** Re-tuned on the combined data, the fixed rule again chose {FINAL5}, with best ensemble {BEST5}. "
  f"The paired test-season difference re-trained − zero-shot for LR is {DL5CI('LR full (re-trained) − LR full (zero-shot)', 'pr_auc')} in PR-AUC "
  f"and {ci(DL5('LR full (re-trained) − LR full (zero-shot)', 'cost'), DL5('LR full (re-trained) − LR full (zero-shot)', 'cost', 'ci_low'), DL5('LR full (re-trained) − LR full (zero-shot)', 'cost', 'ci_high'), 1)} in cost. "
  f"For HGB it is {DL5CI('HGB full (re-trained) − HGB full (zero-shot)', 'pr_auc')}{', the only interval that excludes 0' if hgb_sig else ''}, and for RF {DL5CI('RF full (re-trained) − RF full (zero-shot)', 'pr_auc')}. "
  f"Re-trained, RF − LR is {DL5CI('RF full (re-trained) − LR full (re-trained)', 'pr_auc')} and HGB − LR {DL5CI('HGB full (re-trained) − LR full (re-trained)', 'pr_auc')}. "
  f"The CV PR-AUC of LR rose from {f(rts.loc['LR full', 'cv_pr_auc_initial'], 3)} to {f(rts.loc['LR full', 'cv_pr_auc_retrained'], 3)} with more training winters. "
  f"Fires still added no skill to LR (LR full ≡ LR no-fire), and AQ history still did: LR no-fire − LR weather-only {DL5CI('LR no-fire (re-trained) − LR weather-only (re-trained)', 'pr_auc')}.")
g_all = gap[(gap.subset == "all test rows") & (gap.model == "LR full (re-trained)")].iloc[0]
g_no = gap[(gap.subset == "without fire-gap rows") & (gap.model == "LR full (re-trained)")].iloc[0]
rl_f = rel[(rel.label_rule.str.startswith("frozen")) & (rel.model.str.endswith("(re-trained)"))].iloc[0]
rl_r = rel[(rel.label_rule.str.startswith("re-learned")) & (rel.model.str.endswith("(re-trained)"))].iloc[0]
p(f"**Sensitivity.** Dropping the {int(g_all.n - g_no.n)} test rows that read a VIIRS gap day moves the re-trained LR PR-AUC from {f(g_all.pr_auc, 3)} to {f(g_no.pr_auc, 3)}. "
  f"Re-learning the spike thresholds on the expanded training rows changes them by {f(thrr['change'].min())} to {f(thrr['change'].max())} and lowers the test spike rate to {pct(rl_r.test_spike_rate)}% "
  f"(PR-AUC {f(rl_r.pr_auc, 3)} for LR, {f(rel[(rel.label_rule.str.startswith('re-learned')) & (rel.model == 'Persistence')].pr_auc.iloc[0], 3)} for persistence). "
  "A moving threshold would hide part of the 2024 deterioration, so we keep the frozen label as the headline.")
h2("Fairness shift")
rows = []
for s, sl, model in [(FS1, "(1)", "LR full"), (FS2B, "(2b)", "LR full"), (FS3A, "(3a)", FINAL5)]:
    for rule, rl in [(R1, "single"), (RT, "per tier")]:
        rows.append([sl, rl, f"{f(FS(s, model, rule, CT, 'dir_vs_priv_min'))}–{f(FS(s, model, rule, CT, 'dir_vs_priv_max'))}",
                     f(FS(s, model, rule, CT, "eop_diff"), 3), f(FS(s, model, rule, CT, "pe_diff"), 3), f(FS(s, model, rule, CT, "eo_diff"), 3),
                     f(FS(s, model, rule, "country", "eo_diff"), 3)])
tbf = table("Fairness across city-size tiers before and after the data expansion", ["", "Threshold", "Tier DIR", "ΔTPR", "ΔFPR", "EO", "EO country"], rows,
            [330, 700, 900, 600, 600, 600, 800],
            note="DIR = alert rate relative to Tier 1 metros. ΔTPR, ΔFPR = largest gap between tiers. EO = equalized-odds gap. 95% CIs in Appendix Table A7.")
fz1, fz2, fz3 = (FGR(s, mdl, R1, CT, T3, "fpr") for s, mdl in [(FS1, "LR full"), (FS2B, "LR full"), (FS3A, FINAL5)])
tz1 = (FGR(FS1, "LR full", R1, CT, T1, "fpr"), FGR(FS2B, "LR full", R1, CT, T1, "fpr"), FGR(FS3A, FINAL5, R1, CT, T1, "fpr"))
p(f"**Under one threshold, the tier gaps did not widen beyond their uncertainty** ({tbf}, {next_fig()}). "
  f"Zero-shot, the false-alarm rate rose in every tier: metros {pct(tz1[0])}% → {pct(tz1[1])}%, small cities {pct(fz1)}% → {pct(fz2)}%. "
  f"The predictive-equality gap moved from {f(FS(FS1, 'LR full', R1, CT, 'pe_diff'), 3)} to {FSCI(FS2B, 'LR full', R1, CT, 'pe_diff')}. "
  f"Re-training moved it to {FSCI(FS3A, FINAL5, R1, CT, 'pe_diff')}, a paired change of "
  f"{ci(FDL(R1, CT, 'pe_diff'), FDL(R1, CT, 'pe_diff', 'ci_low'), FDL(R1, CT, 'pe_diff', 'ci_high'))}. "
  f"The tier DIR still fails the 80% rule, but it follows the base rates: Tier 3 had {pct(FGR(FS2B, 'LR full', R1, CT, T3, 'base_rate'))}% spike days in Sep–Dec 2024 against {pct(FGR(FS2B, 'LR full', R1, CT, T1, 'base_rate'))}% in metros. "
  f"Between countries the equalized-odds gap stayed at {f(FS(FS2B, 'LR full', R1, 'country', 'eo_diff'), 3)} zero-shot and {f(FS(FS3A, FINAL5, R1, 'country', 'eo_diff'), 3)} re-trained.")
dir_pt = FDL(RT, CT, "dir_vs_priv_max")
p(f"**The per-tier thresholds lose their small-city adjustment.** In Milestone 4 they ranged from {f(min(THR4.values()), 3)} to {f(max(THR4.values()), 3)}, with the highest for Tier 3. "
  f"Re-chosen on the combined data, they nearly converge ({f(min(THR5.values()), 3)} to {f(max(THR5.values()), 3)}). "
  f"On the test season their tier DIR is higher than with the Milestone 4 tier thresholds by {ci(dir_pt, FDL(RT, CT, 'dir_vs_priv_max', 'ci_low'), FDL(RT, CT, 'dir_vs_priv_max', 'ci_high'))}. "
  f"**Exposure.** Weighting by census population, the {N_TEST_SPIKES} spike days of Sep–Dec 2024 add up to {f(EX(FS2B, 'all cities', 'person_days_exposed_m'), 0)} million person-days. "
  f"The zero-shot alert missed {pct(EX(FS2B, 'all cities', 'share_exposure_missed'))}% of them. "
  f"The three Pakistani metros hold {pct(mp_t1, 0)}% of the missed person-days, since one missed day there affects millions.")
figure("figures/fig_m05_paper_5_fairness_shift.png", "Recall and false-alarm rate by city-size tier (95% week-block CIs): Milestone 4 validation, 2024 zero-shot, and re-trained with the single and per-tier thresholds.")

# =====================================================================
# VII. Policy
# =====================================================================
h1("Policy Recommendations")
h2("FATEN re-evaluation")
table("The alert against the FATEN principles after the 2024 test",
      ["", "Evidence", "Safeguard"],
      [["Fairness", f"Similar error rates by country; tier ΔFPR {f(FS(FS2B, 'LR full', R1, CT, 'pe_diff'), 3)} zero-shot. Per-tier thresholds re-chosen on the combined data nearly converge.",
        "Re-audit tiers each season; re-choose tier thresholds only with a hold-out check."],
       ["Autonomy", "The model advises. Officials set the cost ratio and the threshold.", "Human decision for closures; recorded overrides."],
       ["Trust", f"Two readable inputs; skill held out of time (PR-AUC {f(lr_zs_pr, 3)}); calibration slipped.", "Publish the alert record, its errors and monthly drift scores."],
       ["Equity", "Small cities carry more false alarms; metros carry most missed person-days.", "Support measures with each alert; low-cost sensors in Tier 3 cities."],
       ["Non-maleficence", f"{int(TCN(S2B, 'LR full', 'fn'))} spikes missed in Sep–Dec 2024; the frozen model under-predicted the spike rate.",
        "Keep existing advisories; re-calibrate before each season."]],
      [1080, 2100, 1720], align="left")
h2("Living-lab deployment and failure modes")
p(f"A living lab tests an innovation with its users in a real setting {cite('leminen12')}. "
  "We propose a one-season pilot with the Environment Protection Department of Punjab in two cities per tier. "
  "The model would issue an advisory each evening, and officials would record their own decision next to it. The 2024 test adds four failure modes and safeguards:")
bullets(["**Prior shift:** a worse winter raises the spike rate and the cost. Re-calibrate the intercept on the latest weeks and track observed against predicted rates monthly.",
         "**Concept drift:** the stagnation and fire effects changed. Run the PSI, domain and interaction tests before each season, with fixed alarm levels.",
         "**Satellite gaps:** VIIRS missed 3–5 November 2024. Flag fire inputs as missing, never as zero, and fall back to the no-fire model.",
         "**Threshold transfer:** tier thresholds re-chosen on new data lost the small-city adjustment and raised the tier DIR. Validate any new threshold on held-out weeks before use."])
p("A review board with officials from both tiers, a public-health expert and a community representative would review the fairness table, the drift scores and every missed spike each month. "
  "This guards against digital marginalisation of small cities, which have the fewest monitors.")
h2("Recommendations")
bullets([f"Issue a next-day, city-level advisory from today's index margin and temperature. It stayed cheaper than persistence on 2024.",
         "Re-calibrate and re-audit before every winter. Re-training on more years did not raise skill but keeps the thresholds current.",
         "Use rain as an all-clear signal and treat fire control as source reduction, not a forecast input.",
         f"Share one alert method across the border. Error rates are similar in both countries, and India's GRAP already acts on daily levels {cite('tribune24')}."])

# =====================================================================
# VIII. Limitations and conclusion
# =====================================================================
h1("Limitations and Conclusion")
p("CAMS model estimates on a coarse grid stand in for monitors, and Islamabad and Rawalpindi share one series. The models use observed, not forecast, weather. "
  "The tiers rest on population only, with a 2011 census for India. Each test season has about 18 weeks, so the CIs are wide. "
  "The proposal's 1 km WorldPop exposure map was reduced to census population per city. "
  "Our next-day alert does not replace transport models that attribute smog to its sources.")
p(f"A transparent two-input alert forecast next-day smog spikes in 11 cross-border cities and kept its ranking skill on an unseen 2024 season (PR-AUC {f(lr_zs_pr, 3)}). "
  "The 2024 wave brought far more spikes and a changed stagnation and fire relation. The alert under-predicted risk and cost more. "
  "Re-training on the combined data did not improve ranking, and the ensembles still did not beat logistic regression. "
  "Under one threshold, the fairness gaps between countries and city tiers did not change beyond their uncertainty. "
  "The model is useful when it is re-calibrated each season, audited by tier and kept under human review.")

# =====================================================================
# References
# =====================================================================
h1_plain("References")
blocks.append({"t": "ieee_refs", "items": [REFS[k] for k in order]})
assert set(order) == set(REFS), f"listed but not cited: {set(REFS) - set(order)}"

# =====================================================================
# Appendix (one column)
# =====================================================================
section("one", newpage=True)
h1_plain("Appendix")
counters["table"] = 0
ROMAN_SAVED = ROMAN[:]
ROMAN[:] = [f"A{i}" for i in range(1, 16)]
table("Schema reconciliation of the raw files", ["Issue", "Evidence", "Action"],
      act.values.tolist(), [1500, 4400, 4540], font=7, align="left")
rows = [[r.table, r.run, f"{int(r.rows):,}", int(r.columns_compared), int(r.cells_differing), r.columns_differing, int(r.cells_differing_from_lead_in)] for r in rep.itertuples()]
table("Reproduction check of the automated ingestion against the committed 2022–23 tables", ["Table", "Run", "Rows", "Cols", "Cells differing", "Columns differing", "In window"], rows,
      [1200, 2600, 700, 500, 900, 3640, 900], font=6.5,
      note="'In window' counts differing cells from three days before 4 Aug 2022 (the earliest day the master reads). The master's 2023-12-29 to 31 targets differ because they now point into 2024 instead of being empty.")
qrows = [[r.stream, r.check, f(r.initial, 0), f(r.new, 0)] for r in tab("m5_quality_audit").itertuples()]
table("Data-quality audit by wave", ["Stream", "Check", "Initial", "2024"], qrows, [1000, 6640, 1400, 1400], font=7)
rows = []
for ft in drift[drift.comparison == SM].feature:
    a = drift[(drift.feature == ft) & (drift.comparison == WW)].iloc[0]
    b = drift[(drift.feature == ft) & (drift.comparison == SM)].iloc[0]
    rows.append([a.label, a.test, f(a.statistic, 3), pv(a.q_value_bh), f(a.psi, 3), f(b.statistic, 3), pv(b.q_value_bh), f(b.psi, 3),
                 "–" if pd.isna(b.ref_mean) else f"{f(b.ref_mean, 2)} → {f(b.new_mean, 2)}"])
table("All drift tests (whole wave and season-matched)", ["Feature", "Test", "Stat.", "q", "PSI", "Stat. SM", "q SM", "PSI SM", "Mean SM"], rows,
      [2700, 1200, 700, 800, 700, 800, 800, 800, 1940], font=6.5,
      note=f"SM = season-matched (Sep–Dec). Domain-classifier ROC-AUC, all features: whole wave {f(dww, 3)}, season-matched {f(dsm, 3)}.")
rows = []
for s, sl in SETS[:4]:
    for m in TW:
        rows.append([sl, m, M3CI(s, m, "pr_auc"), M3CI(s, m, "roc_auc"), M3CI(s, m, "recall"), ci(M3(s, m, "cost_per_1000"), M3(s, m, "cost_per_1000", "ci_low"), M3(s, m, "cost_per_1000", "ci_high"), 1)])
table("Three-way audit with 95% week-block bootstrap CIs", ["", "Model", "PR-AUC", "ROC-AUC", "Recall", "Cost per 1,000"], rows,
      [500, 1200, 2200, 2200, 2200, 2140], font=6.5)
rows = [[m, r.best_params_retrained.replace('"', ""), f(r.cv_pr_auc_initial, 3), f(r.cv_pr_auc_retrained, 3), f(r.threshold_initial, 3), f(r.threshold_retrained, 3)]
        for m, r in rts.iterrows()]
table("Re-trained models: selected settings, CV PR-AUC and 5:1 thresholds (initial → re-trained)", ["Model", "Selected setting", "CV PR init.", "CV PR re-tr.", "Thr. init.", "Thr. re-tr."],
      rows, [1300, 5400, 900, 900, 900, 1040], font=6.5)
rows = []
for s, sl, model in [(FS1, "(1)", "LR full"), (FS2A, "(2a)", "LR full"), (FS2B, "(2b)", "LR full"), (FS3A, "(3a)", FINAL5)]:
    for rule in [R1, RT, REO]:
        for g in ["country", CT]:
            rows.append([sl, rule, g, FSCI(s, model, rule, g, "eop_diff"), FSCI(s, model, rule, g, "pe_diff"), FSCI(s, model, rule, g, "dir_vs_priv_max")])
table("Fairness metrics with 95% week-block bootstrap CIs", ["", "Rule", "Grouping", "ΔTPR", "ΔFPR", "DIR (max)"], rows,
      [400, 1800, 1200, 2300, 2300, 2440], font=6.5)
rows = [[r.setting, r.group, f(r.population_m, 2), int(r.spike_days), f(r.person_days_exposed_m, 1), int(r.missed_spike_days), f(r.missed_person_days_m, 1), int(r.false_alarm_days)]
        for r in expo[expo.grouping != "country"].itertuples()]
table("Population exposure (lite Extension 2): census population × spike days", ["Setting", "Group", "Pop. (M)", "Spike days", "Exposed (M p-d)", "Missed days", "Missed (M p-d)", "False alarms"],
      rows, [2700, 1900, 800, 800, 1100, 900, 1100, 1140], font=6.5, note="M p-d = million person-days. Single 5:1 threshold unless the setting says otherwise.")
rows = [[r.label_rule, r.model, pct(r.test_spike_rate), f(r.recall, 3), f(r.precision, 3), f(r.pr_auc, 3), f(r.cost_per_1000, 1), f(r.tier_pe_diff, 3)] for r in rel.itertuples()]
table("Sensitivity: frozen vs re-learned spike thresholds, Sep–Dec 2024 test", ["Label rule", "Model", "Spike rate (%)", "Recall", "Precision", "PR-AUC", "Cost", "Tier ΔFPR"],
      rows, [2300, 2300, 900, 800, 900, 800, 800, 1440], font=6.5)
ROMAN[:] = ROMAN_SAVED

OUT.write_text(json.dumps({"blocks": blocks}, ensure_ascii=False, indent=1), encoding="utf-8")
words = sum(len(b.get("text", "").split()) + sum(len(i.split()) for i in b.get("items", [])) for b in blocks
            if b["t"] in ("p", "bullets", "abstract"))
print(f"wrote {OUT.name}: {len(blocks)} blocks, {counters['figure']} figures, ~{words} words of body text, {len(order)} references")
