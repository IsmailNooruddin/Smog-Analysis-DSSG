# Handoff: Trans-Boundary Smog Prediction (Milestone 5 complete)

This document is for an AI coding agent (any vendor) picking up the project cold. It explains what the project is,
what is finished, where everything lives, which decisions were made and why, what the Milestone 3 and Milestone 4
results are, and what comes next. Read it fully before touching the code. Then read the briefs:
- `context/mielstone 05 New Data Ingestion.md` (the Milestone 5 brief and rubric; the file name has the typo);
- `context/milestone 4.md` (the Milestone 4 brief and rubric);
- `context/milestone3.md`, `context/milestone3_plan.md` and `context/milestone3_finish_plan.md` (Milestone 3).

Last updated: 2026-11-26. State of `main` at writing: see the commit tables in section 2.
Milestone 3 was graded. The grader took 5 points off the manuscript, so the Milestone 4 report is one rewritten paper.

---

## 0. Where we are, in six lines

1. Milestone 2 (data, EDA, hypotheses) is finished and handed in (`submission/`).
2. Milestone 3 is finished and graded: `modeling.ipynb`, `src/modeling.py`, `src/evaluate.py`, `DECISIONS.md` rows
   S1–S19 and the package `submission/milestone3/`.
3. **Milestone 4 is finished** (section 10b): `advanced_modeling.ipynb` (39 cells, 18 tables, 7 figures, 6 new
   models), `src/fairness.py`, census tiers in `Dataset/external/city_population.csv`, `DECISIONS.md` rows P1–P9,
   an 18-page report rewritten as one paper, and the package `submission/milestone4/`.
4. **Milestone 5 is finished** (section 10c): the 2024 wave, drift tests, zero-shot and re-trained audit, fairness
   shift, `data_extension.ipynb`, `src/ingest.py`, `src/drift.py`, `DECISIONS.md` rows N1–N16, a 7-page IEEE paper
   (+3 appendix pages) and the package `submission/milestone5/`.
5. **Next:** nothing is scheduled. Nothing is pushed for Milestones 4 and 5. Push only when the user asks (section 11).
6. One commit per phase, straight to `main`, author `bilal <bilelayub@gmail.com>`, **no** `Co-Authored-By`,
   `Claude-Session` or "Generated with" lines. Push only when the user asks.

---

## 1. Project in one paragraph

A university Data Science for Social Good project at Habib University. The team is Munir Tariq (10067), Ismail
Nooruddin (09958) and Bilal Ayub (09716), all in Computer Science. The goal is to predict hazardous **smog spikes**
in 11 cities of Punjab (7 in Pakistan, 4 in India) **1 to 3 days ahead**. The predictors are:
- **upwind crop fires** from NASA VIIRS satellite detections, split by country of origin to test the cross-border
  claim;
- **weather "traps"**: stagnant wind, humidity, no rain and clear-night inversions.

The target is a **Composite Smog Index** built from six pollutants, plus a per-city spike label. The project is
aligned with SDG 3.9, 11.6 and 13. The course runs in milestones:
- Milestone 1: proposal (done).
- Milestone 2: data preparation, EDA and hypotheses (done).
- Milestone 3: baseline models, leakage-free CV, error-cost analysis (done, graded).
- Milestone 4: advanced models, fairness audit, bias mitigation, ethics (done, not yet pushed).
- **Milestone 5: new data wave (2024), drift, zero-shot and re-training, fairness shift, IEEE paper (done, not yet pushed).**

---

## 2. Environment and git state

- **Machine:** Bilal's Windows 11 laptop. Global **Python 3.14.6** (no venv; `proj_env/` in the repo is an old,
  unused folder, leave it alone), 8 logical CPUs, 16 GB RAM, Node 24, MS Word. Everything runs locally: no Colab,
  no cloud.
- **Installed versions:** numpy 2.5.4, pandas 3.1.0, scikit-learn 1.9.1, statsmodels 0.15.0, joblib 1.6.0,
  docx2pdf (Windows-only, installed but deliberately **not** in `requirements.txt`), npm `docx` 9.14.
- **Repository:** GitHub `IsmailNooruddin/Smog-Analysis-DSSG` (private). **Only `main` exists**, locally and on the
  remote; the cloud session deleted every other branch. Work on `main` directly (decision D10).
- `git config user.name/email` = `bilal` / `bilelayub@gmail.com`. Claude Code commit attribution is already off in
  `~/.claude/settings.json` (`"attribution": {"commit": "", "pr": ""}`).
- **Milestone 3 commits so far:**

| Commit | Message | Content |
|---|---|---|
| `1510aa3` | Milestone 3 plan, brief and project handoff | `context/milestone3*.md`, the earlier version of this file (cloud session) |
| `87261f0` | Milestone 3 setup: modelling dependencies | `requirements.txt` (+ scikit-learn, statsmodels, joblib), `package.json`, `package-lock.json`, `.gitignore` (+ `node_modules/`) |
| `c4b7cd5` | Add modelling and evaluation modules | `src/modeling.py`, `src/evaluate.py` (Phases 1 and 2 share one commit, as in the plan's commit list) |
| `fd1b67d` | Milestone 3 modelling notebook with results, tables and figures | `modeling.ipynb` (executed), solver change in `src/modeling.py`, `Dataset/clean/m3_params.json`, `docs/tables/m3_*.csv` (21), `figures/fig_m3_*.png` (7), `models/*.joblib` (7) |
| `018bfcd` | Update project handoff after Milestone 3 Phases 0–3 | this file |
| `6ae1eb5` | Milestone 3 revisions: threshold-margin features, leakage check, group error rates, index regression | `src/*.py`, `modeling.ipynb` (58 cells), `m3_params.json`, `docs/tables/m3_*.csv` (25), figures, `models/*.joblib` (10), `context/milestone3_finish_plan.md` |
| `f9efad7` | Decision log: Milestone 3 modelling choices | `DECISIONS.md` rows S1–S19 |
| `a897ac1` | Milestone 3 report sections and submission package | `docs/manuscript/*` (builder `--milestone 3`, renderer argument 3, `manuscript_m3.json`), `requirements.txt` (scikit-learn ≥ 1.8), `submission/milestone3/` |
| `9d64111` | Update project handoff after Milestone 3 | this file |

- **Milestone 4 commits** (none pushed when this was written; `git log origin/main..main` lists them):

| Commit | Message | Content |
|---|---|---|
| `70b4db2` | Milestone 3 revised submission and Milestone 4 brief | the team's hand revisions (`modeling.ipynb`, `submission/milestone3/*_revised.*`), `CLAUDE.md`, `context/milestone 4.md` |
| `8223511` | Milestone 4: city census population and size tiers | `Dataset/external/city_population.csv`, `CITY_POP_FILE` in `src/config.py`, `DECISIONS.md` row P1 |
| `abf9d06` | Milestone 4 modules: ensemble pipelines, random search, fairness audit and mitigation | `src/modeling.py` (additions only), `src/fairness.py` (new) |
| `c096c31` | Milestone 4 notebook: tuned RF and HGB, fairness audit, mitigation and Pareto trade-off | `advanced_modeling.ipynb` (executed), `m4_params.json`, `docs/tables/m4_*.csv` (18), `figures/fig_m04_*.png` (7), `models/rf_*`, `models/hgb_*` (6) |
| `1d99b05` | Milestone 4 decisions P2-P9: search spaces, final-model rule, fairness settings | `DECISIONS.md` |
| `6a50d92` | Milestone 4 manuscript: one-paper builder, APA references and number check | `docs/manuscript/build_manuscript_m4.py`, `check_numbers_m4.py`, `manuscript_m4.json`, `render_docx.js` (argument 4) |
| `2ab0611` | Milestone 4 submission package: report, notebooks, code, models and data | `submission/milestone4/` |
| `d9ecc0c` | Update project handoff after Milestone 4 | this file |

- **Milestone 5 commits** (none pushed):

| Commit | Message | Content |
|---|---|---|
| `6b53b2c` | Milestone 5 modules: raw-data ingestion and drift tests | `src/ingest.py`, `src/drift.py` (new); M5 constants in `src/config.py`; `sealed_from` arguments in `src/modeling.py` and `src/merge.py` |
| `1e88b48` | Milestone 5 notebook: 2024 wave ingestion, drift tests, zero-shot and re-trained audit, fairness shift | `data_extension.ipynb` (executed), `docs/tables/m5_*.csv` (37), `figures/fig_m05_1..7`, `models/m5_*` (11), `Dataset/clean/m5/`, `master_daily_m5.parquet`, `master_data_dictionary_m5.csv`, `m5_params.json`, the M5 brief |
| `f7b2d20` | Milestone 5 decisions N1-N16 | `DECISIONS.md` |
| `1614d3b` | Milestone 5 manuscript: IEEE two-column paper, column-width figures and number check | `build_manuscript_m5.py`, `check_numbers_m5.py`, `make_figures_m5.py`, `manuscript_m5.json`, `render_docx.js` (argument 5, IEEE layout), `figures/fig_m05_paper_*` |
| `b324b43` | Milestone 5 submission package | `submission/milestone5/` |
| (this) | Update project handoff after Milestone 5 | this file |

- **Uncommitted on purpose:** `submission/milestone4/advanced_modeling.ipynb` has the user's hand edits (a shorter
  header). The user has not said whether to commit them. Leave the file alone.

Earlier history worth knowing, oldest first: `5306bfe` (Role 1 fixes), `986d7d0` (Role 2 merge and analysis),
`1071958` (manuscript, decision log), `dd2db4e`/`631c3b6` (review fixes), `70faa64` (Excel export, `submission/`),
`67973e9` (10-page Milestone 2 report).

---

## 3. Where everything is

```
air_quality.ipynb      Role 1, Person A (Ismail): AQ cleaning, Composite Smog Index, spike label
weather.ipynb          Role 1, Person B (Munir): weather, vector-mean wind, stagnation flag
fire.ipynb             Role 1, Person C (Bilal): VIIRS filtering, Haversine/bearing, wind cones
merge_analysis.ipynb   Role 2: merge → master table; analysis; hypotheses; Excel export (83 cells)
modeling.ipynb         ★ Milestone 3: 58 cells, sections M3.1–M3.10, executed, ~5 min (reads only the master + role2_params.json)
advanced_modeling.ipynb ◆ Milestone 4: 39 cells, sections M4.1–M4.10 + Summary, executed, 67–82 min (section 10b)
src/fairness.py        ◆ M4: load_city_tiers, add_groups, group_metrics, disparity, reweigh_weights, group_thresholds,
                         constrained_thresholds, pareto_mask
Dataset/external/city_population.csv  ◆ census population, definition and source per city; tiers derive from it
src/config.py          ALL shared settings: cities, files, coordinates, window and split dates, city groups
src/merge.py           Merge functions (every one takes a date window)
src/eda.py             EDA helpers (summary_table, outlier_audit, spearman_by_city, rate_by_condition, contingency)
src/plotting.py        One figure style: Okabe-Ito palette, cividis / RdBu_r, save() at 300 dpi
src/modeling.py        ★ M3: load_model_frame (adds the margins), FEATURE_SETS, AQ_HISTORY(_RAW), FULL_RAW, week_groups,
                         purged_sgkf_splits, make_lr, make_tree, make_ridge, LR/DT/RIDGE_GRID, tune(scoring=),
                         oof_predict(method=), choose_threshold, make_majority, persistence
src/evaluate.py        ★ M3: binary_metrics, group_error_rates, regression_metrics, cv_metrics, block_bootstrap,
                         cost_curve, error_breakdown, save_table
models/                ★ M3: majority, lr_*, dt_*, ridge_* ({full,weather_only,no_fire}).joblib (10 files)
                       ◆ M4: rf_*, hgb_* (6 files). The final model stays lr_full.joblib
submission/milestone3/ ★ M3 package: report DOCX + PDF, modeling.ipynb, src/, models/, Dataset/clean/ (3 files), README
submission/milestone4/ ◆ M4 package: Milestone4_Report.docx/.pdf, both notebooks, src/ (5 modules), models/ (16),
                       Dataset/clean/ (4 files), Dataset/external/city_population.csv,
                       docs/tables/m3_metrics_validation.csv, requirements.txt, README
Dataset/clean/         Role 1/2 outputs + master_daily.parquet (5,665 × 287), master_data_dictionary.csv,
                       aq_params.json, weather/fire z-score params, role2_params.json,
                       ★ m3_params.json (best hyperparameters, OOF thresholds, CV settings, feature sets),
                       ◆ m4_params.json (search settings, best RF/HGB settings, thresholds, final-model rule and
                         choice, fairness settings, per-tier thresholds of every mitigation rule),
                       Milestone2_Final_Master_and_EDA.xlsx
figures/               fig_a*, fig_b*, fig_fire_*, fig_m1..m6 (Milestone 2); ★ fig_m3_1 … fig_m3_7 (Milestone 3);
                       ◆ fig_m04_1 … fig_m04_7 (Milestone 4; the 0 avoids a clash with the Milestone 2 fig_m4_*)
docs/tables/*.csv      Every report table at 4 decimals; ★ 25 files named m3_*.csv; ◆ 18 files named m4_*.csv
data_extension.ipynb   ▲ Milestone 5: 44 cells, sections M5.1–M5.11 + Summary, executed, ~81 min (section 10c)
src/ingest.py          ▲ M5: Role 1 AQ, weather and fire cleaning as functions with frozen parameters; schema_report,
                         compare_frames (reproduction check), write_clean
src/drift.py           ▲ M5: psi, drift_table (KS, χ², PSI, BH q), domain_auc, concept_lr_test, calibration_table
Dataset/clean/m5/      ▲ 2022–2024 daily tables + copies of the frozen params; master_daily_m5.parquet (9,669 × 291);
                         m5_params.json
submission/milestone5/ ▲ M5 package (33 MB, no raw files): report, 3 notebooks, src/ (8 modules), models/ (27),
                         Dataset/clean inputs + m5/, README
docs/manuscript/       build_manuscript.py (CSV → manuscript.json; --milestone 3 → manuscript_m3.json) +
                       render_docx.js (JSON → .docx; argument 3 → submission/milestone3/Milestone3_Report.docx);
                       ◆ build_manuscript_m4.py (→ manuscript_m4.json), render_docx.js argument 4
                       (→ submission/milestone4/Milestone4_Report.docx), check_numbers_m4.py (number check)
submission/            Milestone 2 hand-in package (Milestone2_Report.docx, notebook, Excel, README.md)
DECISIONS.md           Every data removal/change with exact counts: sections F, A, W, M, ★ S (Milestone 3, S1–S19),
                       ◆ P (Milestone 4, P1–P9)
context/               milestone1/2/3.md briefs, Final Proposal.md, milestone3_plan.md, milestone3_finish_plan.md, this file
package.json           npm dependency for render_docx.js (`npm install` restores node_modules/, which is gitignored)
```

★ = new in Milestone 3. ◆ = new in Milestone 4. ▲ = new in Milestone 5 (also `docs/tables/m5_*.csv` (37), `figures/fig_m05_*` and `fig_m05_paper_*`, `build_manuscript_m5.py`, `check_numbers_m5.py`, `make_figures_m5.py`).

---

## 4. How to run

```powershell
python -m pip install -r requirements.txt
python -m pip install docx2pdf            # Windows-only, PDF export via Word
npm install                               # restores node_modules/ for render_docx.js
# from the repository root:
jupyter nbconvert --to notebook --execute --inplace modeling.ipynb     # ~5 min, 8 cores
jupyter nbconvert --to notebook --execute --inplace --ExecutePreprocessor.timeout=7200 advanced_modeling.ipynb   # 67–82 min
jupyter nbconvert --to notebook --execute --inplace --ExecutePreprocessor.timeout=10800 data_extension.ipynb    # ~81 min
```

- `data_extension.ipynb` reads the raw files in `Dataset/Pakistan` and `Dataset/India`, the committed 2022–23 daily
  tables (reproduction check), the Milestone 3/4 models and params, and `m4_metrics_validation.csv`/`m4_mitigation.csv`.
  `M5_FAST=1` gives a short debugging run and writes `"fast_run": true`; the manuscript builder refuses those tables.
- The full run peaks high in memory with 8 joblib workers. One run was killed by Windows for low memory while other
  programs were open. Close other programs first.

- `advanced_modeling.ipynb` reads the master, `role2_params.json`, `m3_params.json`, the Milestone 3 models in
  `models/`, `docs/tables/m3_metrics_validation.csv` and `Dataset/external/city_population.csv`. It asserts that the
  reloaded LR and DT reproduce the Milestone 3 thresholds and validation PR-AUC. Run `modeling.ipynb` first only if
  those models are missing.
- **Milestone 4 determinism is verified:** two runs gave byte-identical `docs/tables/m4_*.csv` (all 18 files).
- The default nbconvert cell timeout is too short for the random searches. Keep `--ExecutePreprocessor.timeout=7200`.

- `modeling.ipynb` reads **only** `Dataset/clean/master_daily.parquet` and `Dataset/clean/role2_params.json`. You do
  **not** need to rerun the Role 1 or merge notebooks for Milestone 3. If you do rerun them by accident,
  `git checkout` the regenerated parquet and PNG files (same data, different bytes).
- **Always run from the repo root.** The notebook puts the root on `sys.path` to import `src`.
- **Determinism is verified:** two consecutive runs gave byte-identical `docs/tables/m3_*.csv` (all 21 files).
  Seeds: CV seeds 0–4, `random_state=42` for models, bootstrap and permutation.
- **Harmless noise at the end of every nbconvert run:** several `KeyError: ...joblib_memmapping_folder...`
  tracebacks from `joblib/externals/loky/backend/resource_tracker.py`. They come from loky's temp-folder cleanup at
  process exit on Windows with Python 3.14, after the notebook has been written. Check for real errors with:
  `PYTHONIOENCODING=utf-8 python -c "import json; nb=json.load(open('modeling.ipynb',encoding='utf-8')); print(sum(o['output_type']=='error' for c in nb['cells'] if c['cell_type']=='code' for o in c.get('outputs',[])))"`
  (expect `0`).
- **Windows console encoding:** printing notebook output that contains `−`, `→` or `×` from Python fails with cp1252.
  Set `PYTHONIOENCODING=utf-8` first.
- Both notebooks were generated with throwaway builder scripts in a session scratchpad (not in the repo). **The
  notebooks themselves are now the source of truth:** edit their cells directly (or with `NotebookEdit`), then re-execute.
  The "What we found" Markdown cells hold hand-written numbers. If any result changes, update them to match the new
  output.

---

## 5. Data pipeline (unchanged from Milestone 2)

| Stage | Input → output | Key facts |
|---|---|---|
| AQ (A) | 11 Open-Meteo files, 453,192 hourly rows → `aq_daily.parquet` 5,665 × 55 | Values are **CAMS model output**, not monitors. No data before 2022-08-04 in any city. Index = 0.40·z(PM2.5) + 0.12·[z(PM10)+z(NO2)+z(SO2)+z(O3)+z(CO)], with log1p first on columns with skew > 1. Spike = index ≥ the city's P90 of training Oct–Mar days. Thresholds range from 0.36 (Rahim Yar Khan) to 2.18 (Lahore); Islamabad = Rawalpindi = 0.65. |
| Weather (B) | 11 files, 433,728 hourly → `wx_daily.parquet` 7,852 × 40 | No missing values. Wind averaged as U/V vectors. `stagnant` = vector-mean wind < 2 km/h. `rain_day` = rain ≥ 1 mm. No surface pressure. |
| Fire (C) | 4 VIIRS files, 1,284,773 detections → `fire_daily.parquet` 8,030 × 60 + long table | Filters: study box, type 0, confidence n/h → 238,756 detections. Counts per city × radius (50–300 km) × cone (up30/45/60, none, down45 placebo) × origin (IN/PK/ALL). No-fire days = 0, never NaN. |
| Merge (Role 2) | → `master_daily.parquet` **5,665 × 287** | Spine 11 cities × 515 days (2022-08-04 to 2023-12-31). Lags 1–3 per city. Targets `target_index_h{1,2,3}`, `target_spike_h{1,2,3}`. Baselines `persist_index`, `persist_spike`, `index_lag1..3`. `split` = train 4,323 / skip 33 / validation 1,309. |

Full column reference: `Dataset/clean/master_data_dictionary.csv`.

---

## 6. Rules that must not be broken

1. **2024 is sealed.** Never read the 2024 files in Milestone 2 or 3. `src/config.py` lists only 2022–2023 fire
   files. `load_model_frame()` asserts no date ≥ 2024-01-01.
2. **Fit on train only.** Scaling, thresholds, cut-offs, hyperparameters and model choices may use only
   `split == "train"` (2022-08-04 to 2023-08-31). Validation (2023-09-04 to 2023-12-31) is only for reporting.
   The notebook calls `assert_train_only()` before every fit.
3. **Time:** every stream added +5 h to GMT **before** taking the date (UTC+5 for Indian cities too; a known limitation).
4. **Keys:** `city`, `country`, `date`. City spellings come only from `src/config.py`.
5. **Lags and targets are always grouped by city.**
6. **Outliers are flagged, never deleted.**
7. **No fixed performance target** (the professor's instruction): find reasonable predictors, report the pattern,
   and compare against the **persistence** and **weather-only** baselines.
8. **Commits:** author bilal, no AI trailers, one commit per phase, push with `git push origin main`.
9. **No file moves or tidy-up** (D11). Don't restructure folders or rename existing files.

---

## 7. Milestone 2 decisions (still in force)

| Decision | Why |
|---|---|
| Window 2022-08-04 to 2023-12-31 for all streams (5,665-row spine) | AQ has no data before Aug 2022 |
| Week 14: retrain with 2024 H1 added, test on 2024 H2 | User's plan; change dates in `src/config.py` and rerun |
| Headline Milestone 2 statistics on the training harvest season (Oct–Dec 2022); downwind ±45° cone as placebo | Fires and smog share a seasonal cycle; full-year correlations are inflated |
| Default fire setting ±45° upwind cone, 300 km | Best median Spearman ρ over 7 PK cities, training Oct–Dec: 0.23 (circle −0.06, placebo 0.01) |
| Weather-trap proxy uses a **large** temperature range; cut-offs RH > 77.06%, range > 13.6 °C (train P75) | Large range = clear nights with inversions; in `role2_params.json` |
| Surface pressure dropped | Not in the exported files; limitation |
| Islamabad and Rawalpindi have identical AQ (same CAMS cell); both kept | 10 independent AQ series; limitation |
| 44 `suspect_day` rows (13–16 Dec 2022) kept as rows; thresholds and scaling learned without them | Lags and targets need an unbroken calendar |
| H4 city groups: near = Lahore, Sialkot; intermediate = Faisalabad; far = Multan, Rahim Yar Khan, Islamabad, Rawalpindi | Only PK cities can test India-origin smoke |
| References: Lahore (city), January (month); `harvest_season` removed from hypothesis controls (collinear with months 10–12) | Dummy trap |

---

## 8. Milestone 3 decisions

### 8.1 Agreed with the user before coding (from `context/milestone3_plan.md`; do not reopen)

| # | Decision |
|---|---|
| D1 | Everything runs locally on the Windows laptop |
| D2 | Headline target `target_spike_h1`; h2 and h3 get one compact table with the same tuned pipelines |
| D3 | Keep the Milestone 2 spike label; one sensitivity run with a **month-wise** label (`target_index_h1` ≥ city × month P90, learned on train, suspect days excluded) |
| D4 | Models: majority class, persistence, logistic regression, decision tree. LR and DT on 3 feature sets each. No KNN/RF (RF, GBM → Milestone 4) |
| D5 | CV: purged, repeated StratifiedGroupKFold, k = 5 × 5 repeats (seeds 0–4) = 25 folds; group = calendar week shared by all cities; chronological validation split is the held-out test; plain StratifiedKFold not used |
| D6 | Cost FN:FP = **5:1** headline; cost curve over ratios 1–20; thresholds chosen on out-of-fold (OOF) train predictions, never on validation |
| D7 | Feature sets: **full**, **weather-only**, **no-fire** (full minus fire; the ablation) |
| D8 | Only H2 is formally tested in Milestone 3 (statsmodels Logit, city-clustered SE). H1, H3, H4 → Milestone 4 roadmap |
| D9 | Report: Milestone 2 Sections 1–6 unchanged + new Sections 7–12; References move to the end; footer "Milestone 03"; output in `submission/milestone3/` |
| D10 | Single branch `main`, one commit per phase |
| D11 | No file moves or tidy-up |
| D12 | Rows whose feature day **or** target day is a `suspect_day` are excluded from fitting and scoring; report the count |
| D13 | Commits as bilal with no trailers |

### 8.2 Departures from the plan made during implementation (all reported to the user; put them in DECISIONS.md)

| # | Change | Why (evidence) |
|---|---|---|
| X1 | **LR solver `liblinear`** (with `intercept_scaling=10`) instead of `saga` | `saga` reached the 5,000-iteration cap without converging at C = 100 with balanced weights (≈ 8 s/fit; the first full run was still tuning after 10+ min). `liblinear` converges in < 0.2 s with fold PR-AUC within 0.005 of saga. `intercept_scaling=10` keeps liblinear's intercept penalty negligible. The `l1_ratio ∈ {0, 1}` grid (sklearn ≥ 1.8 API, `penalty` deprecated) works with liblinear. |
| X2 | **Embargo** added to the purge: besides dropping fit rows whose target day (t+1…t+h) is held out, also drop fit rows up to **h + 2** days *after* a held-out day | Those rows carry a held-out day's target value in `persist_index`, `index_lag1` or `index_lag2` (AQ history reaches back to t−2). Constant `MAX_AQ_LAG = 2` in `src/modeling.py`. For h = 1: purge 1 day before, embargo 3 days after. |
| X3 | **`wind_from_nw` dropped; NW is the reference wind sector** (not calm) | `calm` ≡ `stagnant` exactly (631 of 631 rows), so with all 8 sector dummies `stagnant` is a linear combination of them and the intercept. NW is the most frequent sector (1,320 rows). `stagnant` now reads as "calm vs NW wind". |
| X4 | **Persistence score = `persist_index − spike_threshold`** (the plan said `persist_index`) | Thresholds differ by city (0.36 to 2.18), so the raw pooled index is not comparable across cities for ROC/PR. The margin is ≥ 0 exactly when `persist_spike = 1` (asserted), so the alert rule is unchanged. |
| X5 | **H2 Logit sample = training rows in Sep–Feb with `rain_day == 0`**; rain tested by a one-sided Fisher exact test on all training rows | Perfect separation: **0 of 1,057** training rain days precede a spike, and **March–August have 0 spikes**, so an unpenalised Logit has no finite MLE for `rain_day` or for months 3–8. Continuous H2 terms are standardised on the H2 sample (ORs per 1 SD). Controls: `temp_mean_c`, months 2/9/10/11/12 (Jan ref), city dummies. `vec_len_kmh` is left out of the controls because `stagnant` is defined from it. |
| X6 | **Grouped permutation importance** (correlated columns shuffled together: AQ history, fire lags, stagnant t/t−1, wind sectors, months, cities) instead of per-column | Per-column permutation splits credit between near-duplicate lags and hides them. 30 repeats, validation PR-AUC drop. |
| X7 | Extra tables beyond the plan: `m3_validation_counts`, `m3_cost_curve`, `m3_top_errors`, `m3_fn_context`, `m3_monthwise_thresholds` | Needed to back up specific report statements |
| X8 | Persistence also scored in CV for the month-wise and h2/h3 runs (same purged folds) | Without it the CV numbers of those runs had no benchmark |

### 8.3 Rubric fixes agreed after the audit (`context/milestone3_finish_plan.md`; all done)

| # | Decision | Where |
|---|---|---|
| Q1 | Leakage check: random stratified 80/20, plain StratifiedKFold, week-grouped without purge, ours; training rows only | M3.3 → `m3_leakage_check.csv`; report §8.2 |
| Q2 | Preliminary disparity check: recall/FPR/precision by country (bootstrap CIs, PK − IN gap) and city | M3.7 → `m3_error_rates_group.csv`; report §10.4 |
| Q3 | 5:1 is a stated assumption; break-even ratio is the robust result; health burden cited (Pandey et al. 2021) | M3.6 Markdown; report §10.1 |
| Q4 | **AQ history = margin over the city threshold** (headline, fixed before results); raw index as sensitivity | `src/modeling.py`; M3.9c → `m3_aq_encoding.csv` |
| Q5 | Milestone 2 Sections 1–6 unchanged except title, one abstract sentence, one §4 line, §6 paragraph (M3 build only) | `build_manuscript.py --milestone 3` |
| Q6 | Self-contained package mirroring the repo layout | `submission/milestone3/` |
| Q7 | Ridge regression of the continuous index vs persistence; fire ΔMAE | M3.9d → `m3_index_regression.csv` |
| Q8 | Policy tied to Punjab EPD (Smog Commission page; Dawn 2024 closures) and CAQM GRAP (Tribune 2024) | report §11.3 |

**Verified references added** (opened and checked in the session; Crossref/Europe PMC for the blocked publisher pages):
Pedregosa et al. 2011 (JMLR 12(85)); Roberts et al. 2017 (Ecography 40(8) 913–929); Saito & Rehmsmeier 2015 (PLoS ONE
10(3) e0118432); Seabold & Perktold 2010 (SciPy proceedings 92–96); Pandey et al. 2021 (Lancet Planet Health 5(1)
e25–e38); Waqar & Gabol 2024 (Dawn); EPD Punjab Smog Commission page; Tribune News Service 2024 (GRAP). The official
CAQM GRAP page could not be read (JavaScript site), so GRAP is cited from the Tribune report only.

### 8.4 Feature sets as implemented (`src/modeling.py`)

- `AQ_HISTORY` = `persist_margin, margin_lag1, margin_lag2` (index − `spike_threshold`); `AQ_HISTORY_RAW` =
  `persist_index, index_lag1, index_lag2` (used only in `FULL_RAW`, M3.9c)
- `FIRE` = `fire_cnt_up45_r300_all` + `_lag1, _lag2, _lag3` (raw counts; `log1p` inside the pipeline)
- `WEATHER` = `stagnant, stagnant_lag1, rh_mean_pct, rain_day, temp_range_c, vec_len_kmh, temp_mean_c, wind_from_{n,ne,e,se,s,sw,w}`
  (left out: `wind_speed_mean_kmh`, ρ 0.85 with `vec_len_kmh`; temp min/max, r 0.91–0.98; `wind_from_nw`, X3)
- `CALENDAR_PLACE` = `month_02..month_12` (Jan ref) + 10 city dummies (Lahore ref)
- `full` = all four groups (42 columns; weather-only 35, no-fire 38); `weather_only` = WEATHER + CALENDAR_PLACE; `no_fire` = full − FIRE
- LR pipeline: `log1p` + `StandardScaler` on FIRE, `StandardScaler` on `CONTINUOUS` (AQ history, RH, temp range,
  vector wind, temp mean), binaries passed through. DT pipeline: `log1p` on FIRE, everything else passed through.
  Every transform is re-learned inside each fold.
- Grids: LR `C ∈ logspace(-3, 2, 8)`, `l1_ratio ∈ {0, 1}`, `class_weight ∈ {None, balanced}` (32);
  DT `max_depth 2–8`, `min_samples_leaf ∈ {10, 25, 50, 100}`, `class_weight ∈ {None, balanced}` (56).
  `GridSearchCV(scoring="average_precision", cv=<25 purged folds>, refit=True)`.

---

## 9. Milestone 3 results (all from `docs/tables/m3_*.csv`; validation = Sep–Dec 2023; margin encoding)

### 9.1 Data after the D12 drops (`m3_split_balance.csv`)

| | City-days | Dates | Spikes | Rate |
|---|---|---|---|---|
| Train | 4,246 (76.6%) | 2022-08-06 → 2023-08-31 | 204 | 4.80% |
| Validation | 1,298 (23.4%) | 2023-09-04 → 2023-12-30 | 89 | 6.86% |

Dropped: 33 skip rows, 11 validation rows without a target (31 Dec 2023), 22 training rows without `index_lag2`
(first 2 days per city), 44 suspect feature-day rows and 11 suspect target-day rows (12 Dec 2022). All validation
spikes fall in Nov (12) and Dec (77).

**CV folds** (`m3_cv_folds.csv`): each fold holds out 11–12 weeks (825–869 rows); purge plus embargo remove
**286–495** fit rows (the earlier handoff said 330; the CSV says 286). Test-fold spike rate 4.81% (SD 1.35, range
3.45–7.08%) against 4.80% overall.

### 9.2 Tuned models and thresholds (`m3_params.json`, `m3_tuning_*.csv`)

| Model | Best setting | CV PR-AUC | OOF threshold (5:1) |
|---|---|---|---|
| LR full | C = 0.0268, **L1**, no weights | 0.6508 | 0.1280 |
| LR no-fire | same | 0.6507 | 0.1280 |
| LR weather-only | C = 0.0052, L2, no weights | 0.4319 | 0.1009 |
| DT full | depth 4, leaf 50, no weights | 0.5190 | 0.1988 |
| DT no-fire | same | 0.5193 | 0.1988 |
| DT weather-only | depth 3, leaf 10, no weights | 0.3368 | 0.1173 |
| Majority | – | – | never alert |
| Persistence | today's spike → tomorrow | 0.6362 (CV) | fixed rule |

**The L1 LR full keeps only 2 of 42 coefficients:** `persist_margin` (OR 10.92 per SD) and `temp_mean_c` (0.70 per SD).
Every fire, weather, month and city coefficient is 0, so LR full ≡ LR no-fire on validation. The LR curve is flat
from C = 0.005 to 0.14 (0.643–0.651) and falls to 0.605 at C = 100; the DT peaks at depth 4.

### 9.3 Validation metrics (`m3_metrics_validation.csv`, 95% block-bootstrap CIs over 18 weeks)

| Model | PR-AUC [CI] | ROC-AUC | Recall | Precision | F1 | Specificity | Accuracy | Cost /1,000 at 5:1 |
|---|---|---|---|---|---|---|---|---|
| Majority class | – | – | 0.000 | – | 0.000 | 1.000 | 0.931 | 342.8 |
| Persistence | 0.669 [0.344, 0.765] | 0.963 | 0.618 | 0.688 | 0.651 | 0.979 | 0.955 | 150.2 |
| LR full (= no-fire) | **0.695** [0.323, 0.790] | 0.966 | 0.865 | 0.456 | 0.597 | 0.924 | 0.920 | 117.1 |
| LR weather-only | 0.388 | 0.855 | 0.764 | 0.228 | 0.351 | 0.810 | 0.807 | 258.1 |
| DT full | 0.590 [0.237, 0.716] | 0.953 | 0.820 | 0.521 | 0.638 | 0.945 | 0.936 | **113.3** |
| DT no-fire | 0.585 | 0.953 | 0.820 | 0.521 | 0.638 | 0.945 | 0.936 | 113.3 |
| DT weather-only | 0.226 | 0.837 | 0.865 | 0.236 | 0.371 | 0.794 | 0.799 | 238.1 |

Confusion (TP/FP/TN/FN): persistence 55/25/1,184/34; LR full 77/92/1,117/12; DT full 73/67/1,142/16.
CV (25 folds): PR-AUC persistence 0.636 ± 0.141, LR full 0.651 ± 0.144, DT full 0.519 ± 0.135; cost 114.0 / 86.7 / 92.4.

### 9.4 Leakage check (`m3_leakage_check.csv`, Q1; training rows only)

| Scheme | LR full PR-AUC | DT full PR-AUC |
|---|---|---|
| Random stratified 80/20 | 0.730 | 0.652 |
| StratifiedKFold(5, shuffle) | 0.677 ± 0.089 | 0.616 ± 0.093 |
| StratifiedGroupKFold(5) by week, no purge | 0.651 ± 0.158 | 0.539 ± 0.143 |
| Ours (purged + embargoed 5 × 5) | 0.651 ± 0.144 | 0.519 ± 0.135 |
| Reference: validation | 0.695 | 0.590 |

Random splits overstate PR-AUC by 0.03–0.08 (LR) and 0.10–0.13 (DT). ROC-AUC barely moves. Validation sits above CV
because December 2023 was very persistent (persistence 0.669 vs 0.636 in CV).

### 9.5 Fire ablation and persistence comparison (`m3_fire_ablation.csv`)

| Comparison | ΔPR-AUC validation [CI] | ΔROC-AUC [CI] | CV folds better |
|---|---|---|---|
| LR full − LR no-fire | 0.000 (identical predictions) | 0.000 | 2/25 |
| DT full − DT no-fire | +0.004 [−0.012, +0.017] | +0.0001 | 6/25 |
| LR no-fire − LR weather-only | +0.307 [+0.188, +0.379] | +0.112 | 25/25 |
| LR full − persistence | +0.026 [−0.020, +0.052] | **+0.0036 [+0.0009, +0.0059]** | 19/25 |
| DT full − persistence | −0.079 [−0.114, −0.036] | −0.010 | 0/25 |

Fires add no next-day skill; LR is level with or slightly ahead of persistence on ranking (ROC-AUC CI excludes 0,
PR-AUC CI does not).

### 9.6 Asymmetric cost (`m3_cost.csv`, `m3_cost_curve.csv`)

- At 5:1 per 1,000 city-days: never alert 342.8; always alert 931.4; persistence 150.2 (34 FN, 25 FP); LR full 117.1
  (12 FN, 92 FP; 65.8% saving); DT full 113.3 (16 FN, 67 FP; 67.0%).
- **Break-even vs persistence = 2:1** for LR full and DT full (persistence cheaper only at 1:1). At 20:1: LR 255.8,
  DT 275.8, persistence 543.1.
- False-alarm rate: LR 7.6%, DT 5.5%, persistence 2.1% of clean days.
- Q3 framing: 5:1 is a stated assumption; the health burden is cited from Pandey et al. 2021 (India 2019: 1.67 M
  deaths, US$36.8 bn, 1.36% of GDP).

### 9.7 Errors, edge cases, disparity (`m3_errors_*`, `m3_top_errors`, `m3_fn_context`, `m3_error_rates_group`)

- Onsets: persistence 0/34; **LR full 22/34 (64.7%)**; DT full 18/34; both catch all 55 continuations.
- LR misses: Nov 4, Dec 8; ≤ 3 per city. False alarms: 92 = 67 onset-type + 25 episode ends; RYK 16, Multan 14,
  Faisalabad 13, Ferozepur 12, Jalandhar 11.
- Missed vs caught spikes (feature day): margin −0.49 vs +0.12; stagnant 16.7% vs 22.1%; RH 73.7 vs 79.8%; fires
  108.5 vs 47.4.
- Disparity (Q2, LR full): recall PK 0.837 [0.750, 0.923], IN 0.900 [0.332, 0.969]; FPR 7.2% vs 8.3%; every PK − IN
  gap CI includes 0. City FPR: RYK 16.7%, Multan 13.0%, Faisalabad 12.1%, Ferozepur 11.4%; Islamabad/Rawalpindi 1.7%.

### 9.8 Drivers (`m3_odds_ratios.csv`, `m3_h2_logit.csv`, `m3_importance.csv`)

- Permutation (validation ΔPR-AUC): LR full AQ history 0.612, mean temperature 0.042, everything else 0.
  DT full AQ history 0.518. DT Gini: persist_margin 0.94, temp_mean 0.047, temp_range 0.008.
- City ORs: all 0 with the margin (raw-index LR reached 9,004 for Rahim Yar Khan).
- Weather-only LR ORs per SD: temp_mean 0.54, vec wind 0.75, RH 1.32, temp range 1.21; rain 0.83; stagnant 1.06.
- **H2 unchanged** (it does not use AQ history): stagnant 3.24 [1.91, 5.48], RH 3.95 [2.03, 7.69], temperature range
  2.22 [1.66, 2.95]; rain 0/1,057, Fisher p = 8.1 × 10⁻²⁷; n = 1,706, 204 spikes, pseudo R² 0.258.
- Depth-3 tree (`fig_m3_7`): first split persist_margin ≤ 0; then margin and mean temperature; validation PR-AUC 0.564.

### 9.9 Sensitivity (`m3_label_monthwise`, `m3_horizons`, `m3_aq_encoding`, `m3_index_regression`)

- Month-wise label: validation PR-AUC persistence 0.439, LR full 0.349, LR no-fire 0.331, DT full 0.247; CV
  full − no-fire +0.001 → no robust fire effect.
- Horizons (validation PR-AUC h1/h2/h3): persistence 0.669/0.553/0.445; LR full 0.695/0.597/0.486; CV agrees by small
  margins (h2 0.453 vs 0.447; h3 0.383 vs 0.375). DT weather-only issues no alerts at h3.
- AQ encoding (M3.9c): raw-index LR full C = 100 L2, CV 0.605, validation 0.634, cost 128.7; raw-index DT 0.373,
  cost 228.8 (these are the old Phase 3 numbers).
- Ridge index (M3.9d, alpha 0.32): validation MAE persistence 0.274, Ridge full 0.287 (Δ +0.013 [−0.004, +0.034]);
  CV Ridge better in 22/25 folds. Fire ΔMAE −0.0011 [−0.0026, +0.0007]. H5 null not rejected for the index.

### 9.10 Figures (`figures/fig_m3_*.png`)

| File | Content |
|---|---|
| `fig_m3_1_cv_folds` | Fold layout of repeat 1; spike rate per test fold |
| `fig_m3_2_tuning` | CV PR-AUC vs C (LR) and depth (DT), 3 feature sets |
| `fig_m3_3_roc_pr` | Validation ROC and PR curves, 5:1 operating points |
| `fig_m3_4_cost_curve` | Validation cost vs FN:FP ratio 1–20 |
| `fig_m3_5_confusion` | Confusion matrices: persistence, LR full, DT full |
| `fig_m3_6_drivers` | A: weather-only LR ORs (bars) + LR full non-zero ORs (diamonds); B: grouped permutation importance |
| `fig_m3_7_tree` | Depth-3 tree |

---

## 10. Notebook map (`modeling.ipynb`, 58 cells, ~5 min)

| Section | Produces |
|---|---|
| Header + setup | imports, `MODELS`/`LABEL`/`COLOR`/`STYLE`, asserts the fire setting |
| M3.1 | `m3_split_balance.csv`; `assert_train_only()`; margin encoding explained |
| M3.2 | `m3_cv_folds.csv`, `fig_m3_1` |
| M3.3 | tuning tables, `fig_m3_2`, OOF thresholds, `m3_params.json`; **leakage check** → `m3_leakage_check.csv` |
| M3.4 | `m3_metrics_cv.csv`, `m3_metrics_validation.csv`, `m3_validation_counts.csv`, `fig_m3_3` |
| M3.5 | `m3_fire_ablation.csv` |
| M3.6 | sourced cost framing, `m3_cost.csv`, `m3_cost_curve.csv`, `fig_m3_4` |
| M3.7 | `m3_confusion.csv`, `m3_errors_onset.csv`, `m3_errors_city_month.csv`, `m3_top_errors.csv`, `m3_fn_context.csv`, `fig_m3_5`; **disparity check** → `m3_error_rates_group.csv` |
| M3.8 | `m3_odds_ratios.csv`, `m3_h2_logit.csv`, `m3_importance.csv`, `fig_m3_6`, `fig_m3_7` |
| M3.9 | (a) `m3_monthwise_thresholds.csv`, `m3_label_monthwise.csv`; (b) `m3_horizons.csv`; (c) `m3_aq_encoding.csv`; (d) `m3_index_regression.csv` |
| M3.10 | `models/*.joblib` (10), versions, run time |

Every computational section is followed by a "What we found" cell whose numbers match the CSVs (spot-checked).

---

## 10b. Milestone 4 (advanced models, fairness audit, mitigation)

Plan: `C:\Users\Bilel\.claude\plans\last-time-we-completed-joyful-truffle.md` (local to the laptop). Decisions:
`DECISIONS.md` rows P1–P9. All numbers below come from `docs/tables/m4_*.csv` and `m4_params.json`.

### 10b.1 Agreed with the user (do not reopen)

- **Sensitive attribute = geography** (the instructor approved it). The groups are country (PK, IN), city (11) and a
  city-size tier from census population.
- **Tiers** (P1, rule fixed before any result): Tier 1 metro ≥ 3 M (Lahore, Faisalabad, Rawalpindi); Tier 2 large
  1–3 M (Multan, Ludhiana, Amritsar, Islamabad); Tier 3 small < 1 M (Jalandhar, Sialkot, Rahim Yar Khan, Ferozepur).
  Pakistan uses the 2023 census, India the 2011 census.
- **Models:** RF and HGB from scikit-learn, no new dependencies. HGB runs with `early_stopping=False` (P4).
- **Report:** one restructured research paper, not Milestone 2 plus appended sections. H1, H3 and H4 are included
  compactly. 2024 stays sealed.

### 10b.2 Notebook map (`advanced_modeling.ipynb`, 39 cells)

| Section | Produces |
|---|---|
| M4.1 | `m4_groups.csv`, `m4_group_summary.csv` (tiers, base rates per group) |
| M4.2 | random search for RF and HGB × 3 feature sets → `m4_tuning_rf.csv`, `m4_tuning_hgb.csv`, `fig_m04_1`, `m4_params.json` |
| M4.3 | `m4_metrics_cv.csv`, `m4_metrics_validation.csv`, `m4_validation_counts.csv`, `m4_deltas.csv` (paired bootstrap Δ, includes the fire ablation), `m4_cost_curve.csv`, `fig_m04_2`, `fig_m04_3` |
| M4.4 | `m4_importance.csv`, `fig_m04_4` |
| M4.5 | `m4_hypotheses.csv` (H1, H3, H4; OLS, city-clustered SE) |
| M4.6 | `m4_fair_groups.csv`, `m4_fair_disparity.csv`, `m4_fair_group_ci.csv`, `fig_m04_5` |
| M4.7 | `m4_mitigation.csv`, `m4_mitigation_groups.csv` |
| M4.8 | `m4_pareto.csv`, `fig_m04_6` |
| M4.9 | `m4_threshold_curves.csv`, `fig_m04_7` |
| M4.10 | `models/rf_*`, `models/hgb_*`, `mitigation_thresholds` in `m4_params.json`, versions, run time |

### 10b.3 Models (validation = Sep–Dec 2023)

| Model | Best setting | CV PR-AUC | 5:1 threshold | Val PR-AUC | Cost /1,000 at 5:1 | Brier |
|---|---|---|---|---|---|---|
| LR full (final) | Milestone 3 | 0.651 | 0.128 | 0.695 | 117.1 | 0.037 |
| RF full | 500 trees, depth 4, leaf 50, max features 0.5, no weights | 0.590 | 0.175 | 0.679 | 114.8 | 0.035 |
| HGB full | lr 0.020, 330 rounds, 7 leaves, depth 8, leaf 61, L2 0.057, balanced | 0.565 | 0.578 | 0.636 | 110.2 | 0.063 |
| DT full | Milestone 3 | 0.519 | 0.199 | 0.590 | 113.3 | 0.037 |
| Persistence | rule | 0.636 | – | 0.669 | 150.2 | – |

- **Paired Δ against LR full:** RF −0.015 [−0.067, 0.015], better in 1 of 25 folds. HGB −0.059 [−0.116, −0.030].
- **RF − DT** = +0.090, better in 25 of 25 folds. The ensembles improve on the tree, not on LR.
- **Cost:** every cost CI against LR includes 0. Break-even against persistence is 2:1 for LR, DT and RF, and 3:1
  for HGB.
- **Fires:** shuffling AQ history costs 0.612 / 0.543 / 0.531 PR-AUC (LR / RF / HGB). Full − no-fire costs are
  RF −6.2 [−10.8, −2.2] and HGB −12.3 [−25.4, −1.5]. CV does not confirm a ranking gain.

### 10b.4 Hypotheses (`m4_hypotheses.csv`)

- **H1 supported:** cone fires β = 0.054 [0.007, 0.101], p = 0.012; with today's index 0.035, p = 0.002; placebo −0.032.
- **H3 not supported:** −0.038 (spec A), −0.045 [−0.073, −0.017] (spec B). On stagnant days the cone count equals the
  radius count, so the term compares two fire measures.
- **H4 not supported:** India-origin β = 0.001, p = 0.48. Pakistan-origin 0.056. Only 7 city clusters.

### 10b.5 Fairness audit (LR full)

- **Country:** TPR PK 0.837, IN 0.900. FPR 7.2% vs 8.3%. DIR 1.30 on validation fails the two-sided rule, but India's
  base rate was 8.5% against 5.9%. OOF DIR is 1.01.
- **Tier:** FPR 5.6% (T1), 6.5% (T2), 10.5% (T3). Predictive-equality gap 0.049 [0.011, 0.126]. Validation base
  rates are 3.4%, 5.3% and 11.0% (ratio 3.25), so the DIR of 2.44 fails. OOF DIR is 1.15–1.18.
- **Training base rates are nearly equal by design** (4.6–4.9%), because each city's spike threshold is its own P90.
- **RF full** has a larger tier gap (equalized odds 0.301) and catches only 7 of 12 metro spikes.
- **Cities:** highest FPR Rahim Yar Khan 16.7%, Multan 13.0%, Faisalabad 12.2%. Islamabad and Rawalpindi 1.7%
  with no spikes.

### 10b.6 Mitigation and Pareto (`m4_mitigation*.csv`, `m4_pareto.csv`)

- **Per-tier 5:1 thresholds** (T1 0.131, T2 0.128, T3 0.160) cut T3 FPR from 10.5% to 8.1% (44 → 34 false alarms).
  The gap falls from 0.049 to 0.025, the cost from 117.1 to 113.3, and F1 rises from 0.597 to 0.615. Recall falls
  from 0.865 to 0.854.
- **Predictive equality and equalized odds at ε = 0.05** give LR full the same validation result. OOF EO gap
  0.091 → 0.026.
- **Reweighing** weights stay between 0.976 and 1.045, so LR alerts do not change. RF cost moves 114.8 → 112.5.
- **Per-tier thresholds do not transfer for RF:** cost rises from 114.8 to 124.8.
- **Pareto (OOF, LR EO):** ε 0.05 → cost 80.8, gap 0.026; ε 0.02 → 82.9, 0.017; ε 0.01 → 169.3 (recall 0.319).
- The cheapest validation rule (PE at ε 0.01, 109.4) was not chosen, because choices must come from training data.

### 10b.7 Report (`submission/milestone4/Milestone4_Report.pdf`, 18 pages)

- Main text pp. 1–14, references pp. 14–15, Appendices A–C pp. 16–18. 16 tables, 12 figures, APA references.
- Sections: abstract (≤ 250 words) and keywords, introduction, related work, data, exploratory findings and
  hypotheses, methods, results, discussion (FATEN table, living lab, failure modes, governance, policy),
  limitations, conclusion.
- The fixes for the Milestone 3 deduction: one title, no draft labels, author-year citations that match the list,
  every listed reference cited in the text, and dense tables moved to the appendices.
- New references were checked on Crossref or the publisher page (DOIs for Inness 2019 and Schroeder 2014).
- **Number check:** `check_numbers_m4.py` matched all 1,000 decimal numbers in `manuscript_m4.json` to the tables.

---

## 10c. Milestone 5 (2024 wave, drift, re-training, fairness shift)

### 10c.1 Agreed with the user (do not reopen)

- New wave = calendar 2024. The window ends 2024-12-29 (the Ludhiana weather file ends there).
- Re-trained evaluation = out-of-time + CV: re-train 2022-08-04 → 2024-08-31, skip 3 days, test 2024-09-04 →
  2024-12-29, plus purged CV over the combined data.
- Labels frozen: 2022–23 index weights, z-scores and city P90 thresholds. One sensitivity re-learns the thresholds.
- Exposure lite: census population × spike days. The 1 km WorldPop grid was not done, and the paper says so.
- Manuscript: IEEE two-column, 6–8 pages, detail tables in an appendix after page 8.

### 10c.2 Results (all from `docs/tables/m5_*.csv`)

- **Data:** N = 5,665 + 4,004 = 9,669 city-days, P = 291. 9,548 modelling rows, 663 spikes. Train 8,272 (483 spikes),
  test 1,276 (180). The ingestion reproduces every committed 2022–23 cell inside the window.
- **Covariate drift:** most PSI < 0.10. Season-matched, fires within 300 km PSI 0.401 (307 → 171 per city-day).
  Domain AUC 0.531 whole wave, 0.645 season-matched.
- **Label shift:** spike rate 5.4% → 9.1% (Sep–Dec 8.1% → 14.1%; November 4.5% → 27.6%).
- **Concept drift:** LR test p 0.002. The stagnation effect weakened (ratio 0.43), the fire effect strengthened (1.51).
  The frozen LR under-predicts (0.102 predicted vs 0.141 observed, Sep–Dec 2024).
- **Three-way (LR full, PR-AUC / cost):** (1) 0.695 / 117.1; (2b) zero-shot 0.726 / 167.7; (3a) re-trained 0.728 /
  166.9; (3b) CV 0.727 / 95.7. Re-trained − zero-shot not significant for LR; HGB +0.048 [0.003, 0.090]. LR full
  stays final (CV 0.738), best ensemble RF full. The re-trained LR keeps only `persist_margin` and `temp_mean_c`.
- **Fairness:** under one threshold no paired gap change excludes 0. Per-tier thresholds re-chosen on the combined
  data nearly converge (0.174–0.180 vs 0.128–0.160 in M4); their tier DIR rises by 0.110 [0.018, 0.301].
- **Exposure:** 295 M person-days in Sep–Dec 2024; zero-shot missed 10.6%, 58% of that in the 3 Pakistani metros.
- **VIIRS gaps:** 20 dates in 2024 with no detection anywhere (incl. 3–5 Nov). Counts stay 0; dropping them changes
  little (PR-AUC 0.728 → 0.730).

### 10c.3 Report (`submission/milestone5/Milestone5_Report.pdf`, 10 pages)

- Body and 34 numbered references pp. 1–7; one-column appendix (Tables A1–A9) pp. 8–10. 7 tables, 7 figures.
- Build: `python docs/manuscript/make_figures_m5.py`, `python docs/manuscript/build_manuscript_m5.py`,
  `python docs/manuscript/check_numbers_m5.py` (1,239 numbers, 0 missing), `node docs/manuscript/render_docx.js 5`,
  then docx2pdf to `submission/milestone5/Milestone5_Report.pdf`.
- The builder asserts every directional claim (e.g. "precision rose", "gaps within uncertainty", "per-tier
  thresholds converge"). If a rerun changes a result, an assert fails instead of the text going wrong.

## 11. What is left

Milestones 4 and 5 are complete but not pushed. Next:
- **Push** with `git push origin main` when the user asks.
- Ask the user whether to commit their hand edits to `submission/milestone4/advanced_modeling.ipynb`.
- The M5 package has no raw files (about 180 MB). The README says to copy them from the repository. Bundle them only
  if the user asks.
- Open ideas not done: the 1 km WorldPop exposure grid, a monthly intercept re-calibration of the alert, per-horizon tuning of the ensembles, surface pressure, an ozone weight check, and probability
  calibration of HGB.
- **Report builds:**
  - Milestone 4: `python docs/manuscript/build_manuscript_m4.py`, then `python docs/manuscript/check_numbers_m4.py`
    (expect 0 missing), then `node docs/manuscript/render_docx.js 4`. PDF with
    `python -c "from docx2pdf import convert; convert('submission/milestone4/Milestone4_Report.docx','submission/milestone4/Milestone4_Report.pdf')"`.
  - Milestone 3: `python docs/manuscript/build_manuscript.py --milestone 3`, then `node docs/manuscript/render_docx.js 3`.
  - The default build (no argument) still produces the Milestone 2 report.

## 12. Rubric reminders

**Milestone 5** (`context/mielstone 05 New Data Ingestion.md`):

| Criterion | Weight | Where it is covered |
|---|---|---|
| Data ingestion + schema integration | 20 | M5.1–M5.3; report §II, Tables A1–A3 |
| Drift + concept shift (KS, PSI, plots) | 30 | M5.4–M5.5; report §VI.B–C, Figs. 1–3, Table A4 |
| Re-training + generalization, 3-way table | 30 | M5.6–M5.8; report §VI.D, Table V, Fig. 6, Tables A5–A6 |
| Fairness shift, FATEN, code, PDF | 20 | M5.9–M5.10; report §VI.E, §VII, Tables A7–A9 |

**Milestone 4** (`context/milestone 4.md`):

| Criterion | Weight | Where it is covered |
|---|---|---|
| Advanced models + structured tuning, compared with baselines | 30 | M4.2–M4.4; report §5.2, §§6.1–6.3, Appendix B |
| Fairness audit (DIR / 80% rule, equalized odds, predictive equality, Pareto) | 35 | M4.6, M4.8; report §5.4, §6.5, §6.6, Appendix C |
| Bias mitigation + asymmetric thresholds by group | 20 | M4.7, M4.9; report §5.5, §6.6 |
| Notebook + manuscript (FATEN, living lab) | 15 | `advanced_modeling.ipynb`, report §§7.2–7.3 |

**Milestone 3** (`context/milestone3.md`):

| Criterion | Weight | Where it is covered |
|---|---|---|
| Baseline models + CV framework | 35 | M3.2–M3.3; report §7–8 |
| Metrics + asymmetric error analysis | 30 | M3.4, M3.6, M3.7; report §9–10 |
| Feature importance + insights + roadmap | 20 | M3.8–M3.9; report §11–12 |
| Written report + reproducibility | 15 | Notebook, modules, `models/`, PDF |

The brief lists "accuracy, precision, recall, specificity, F1, ROC-AUC". All of them are in the tables, plus PR-AUC,
Brier and cost.

The brief also asks to "document train/test split ratios and apply stratified sampling". Our answer:
- the split is chronological, 76.6/23.4, by design;
- stratification is applied inside the grouped CV (StratifiedGroupKFold);
- the split balance is checked rather than forced;
- the leakage check (report §8.2, Table 14) shows numerically why a random stratified split would overstate skill.

The report is 19 pages (Sections 1–6 from Milestone 2, Sections 7–12 new, 21 tables, 13 figures); the 16–17 page
target of the finish plan was not reached without dropping figures.

**Figure rules (still in force):** a title, axes with units, a legend, the Okabe-Ito palette via `src/plotting.py`,
and `P.save()` at 300 dpi. Every number in the report must come from `docs/tables/*.csv`.

---

## 13. Known quirks and pitfalls

- **Shell hang I hit:** a stray `cat > file` with no heredoc waits on stdin forever. If a command shows no output for
  minutes, check for that before blaming joblib. Joblib itself works fine here.
- **Python buffers its output when run from scripts:** use `python -u` for long runs.
- **`saga` is slow on this problem** (X1). Don't switch back.
- `LogisticRegression(penalty=...)` is deprecated in sklearn 1.9. Use `l1_ratio` (0 = L2, 1 = L1).
- **`calm` ≡ `stagnant`** (X3). Never enter all 8 `wind_from_*` together with `stagnant`.
- **Perfect separation:** rain days and Mar–Aug have no spikes. Any unpenalised logit on the spike label must handle
  that (X5).
- **Balanced-weight trees** have inflated probabilities. Their 5:1 thresholds are about 0.67–0.71, against about
  0.10 for LR. This is not a bug. The same holds for HGB full (balanced, threshold 0.578, Brier 0.063).
- **Reweighing barely moves anything** (Milestone 4). The spike label is each city's own training P90, so training
  base rates are 4.6–4.9% in every group and the weights stay near 1. Identical LR alerts after reweighing are real.
- **Fairness results differ between OOF and validation** because the validation base rates differ by tier
  (3.4% / 5.3% / 11.0%). Report both. Never choose a rule on validation.
- **The number checker** (`check_numbers_m4.py`) compares within half a unit of the last shown digit. Exact
  comparison flags false misses because `np.round` rounds half to even.
- **The Milestone 4 manuscript JSON holds absolute figure paths**, like the earlier ones.
- **Rerunning `merge_analysis.ipynb`** regenerates `master_daily.parquet` with identical data but different bytes.
  Avoid it, or `git checkout` the file afterwards.
- **The AQ notebook** defines its own `TRAIN_START/END` and does not import `src/config.py`. This matters for Week 14.
- **Report tables are at 4 decimals on purpose:** rounding twice from 3 decimals rounded some values the wrong way.
- `requirements.txt` is UTF-8. An older UTF-16 Windows freeze existed, so don't restore it.
- **`manuscript.json` holds absolute figure paths.** The committed Milestone 2 JSON was built on a cloud machine
  (`/home/user/...`); rebuilding on the laptop changes only those paths (content verified identical), so don't
  commit a path-only rebuild. `build_manuscript.py` now writes UTF-8 explicitly.
- **The tuned LR is sparse.** With the margin encoding the L1 penalty keeps only 2 columns; driver analysis of
  weather therefore uses the weather-only LR and the H2 Logit.
- **Git warnings** "LF will be replaced by CRLF" on commit are normal on this machine.
- **Milestone 5 did not move the old constants.** `WINDOW_*`, `SEALED_FROM` and `NASA_FILES` keep their Milestone 4
  values, so the M2–M4 notebooks still reproduce. M5 uses the `M5_*` constants, `NASA_FILES_M5` and explicit
  `sealed_from=SEAL_M5` arguments.
- **`rain_day` rounding:** daily rain is summed from hourly floats. Use `precip_sum_mm.round(6) >= 1`, or a day of
  0.9999999999999999 mm flips the flag.
- **`s.pop` on a DataFrame row** resolves to the method, not a column named `pop`. The exposure column is `popn`.
- **Bash heredocs with quotes sometimes fail in this shell** ("unexpected EOF"). Write a script file instead.
- **`python -I` ignores `PYTHONIOENCODING`.** Call `sys.stdout.reconfigure(encoding="utf-8")` inside the script.
