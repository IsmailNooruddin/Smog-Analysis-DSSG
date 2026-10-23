# Handoff: Trans-Boundary Smog Prediction (Milestone 3, Phases 0–3 done → Phases 4–5 next)

This document is for an AI coding agent (any vendor) picking up the project cold. It explains what the project is,
what is finished, where everything lives, which decisions were made and why, what the Milestone 3 results are, and
exactly what is still open. Read it fully, then `context/milestone3_plan.md` (the agreed plan) and
`context/milestone3.md` (the brief and rubric), before touching the code.

Last updated: 2026-10-24. State of `main` at writing: commit `fd1b67d`, plus the commit that updates this file.
Milestone 3 deadline: **Sunday 25 Oct 2026, 23:59**.

---

## 0. Where we are, in five lines

1. Milestone 2 (data, EDA, hypotheses) is finished and handed in (`submission/`).
2. Milestone 3 Phases 0–3 are done and pushed: dependencies, `src/modeling.py`, `src/evaluate.py`, and an executed
   `modeling.ipynb` with 21 tables, 7 figures, saved models and tuned parameters.
3. The user reviewed the Phase 3 headline results (section 9) before Phases 4–5.
4. **Still to do:** Phase 4 (the `DECISIONS.md` section for Milestone 3) and Phase 5 (report Sections 7–12, rendering,
   PDF, and the `submission/milestone3/` package). See section 11.
5. One commit per phase, straight to `main`, author `bilal <bilelayub@gmail.com>`, **no** `Co-Authored-By`,
   `Claude-Session` or "Generated with" lines.

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
- **Milestone 3: baseline models, leakage-free CV, error-cost analysis (in progress: Phases 0–3 of 5 done).**
- Milestone 4: advanced models, fairness audit, ethics.
- Week 14: out-of-time test on 2024 data.

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
modeling.ipynb         ★ Milestone 3: 46 cells, sections M3.1–M3.10, executed, ~4.5 min (reads only the master + role2_params.json)
src/config.py          ALL shared settings: cities, files, coordinates, window and split dates, city groups
src/merge.py           Merge functions (every one takes a date window)
src/eda.py             EDA helpers (summary_table, outlier_audit, spearman_by_city, rate_by_condition, contingency)
src/plotting.py        One figure style: Okabe-Ito palette, cividis / RdBu_r, save() at 300 dpi
src/modeling.py        ★ M3: load_model_frame, FEATURE_SETS, week_groups, purged_sgkf_splits, make_lr, make_tree,
                         LR_GRID, DT_GRID, tune, oof_predict, choose_threshold, make_majority, persistence
src/evaluate.py        ★ M3: binary_metrics, cv_metrics, block_bootstrap, cost_curve, error_breakdown, save_table
models/                ★ M3: majority, lr_{full,weather_only,no_fire}, dt_{full,weather_only,no_fire}.joblib (56 KB total)
Dataset/clean/         Role 1/2 outputs + master_daily.parquet (5,665 × 287), master_data_dictionary.csv,
                       aq_params.json, weather/fire z-score params, role2_params.json,
                       ★ m3_params.json (best hyperparameters, OOF thresholds, CV settings, feature sets),
                       Milestone2_Final_Master_and_EDA.xlsx
figures/               fig_a*, fig_b*, fig_fire_*, fig_m1..m6 (Milestone 2); ★ fig_m3_1 … fig_m3_7 (Milestone 3)
docs/tables/*.csv      Every report table at 4 decimals; ★ 21 files named m3_*.csv
docs/manuscript/       build_manuscript.py (CSV → manuscript.json) + render_docx.js (JSON → .docx)
submission/            Milestone 2 hand-in package (Milestone2_Report.docx, notebook, Excel, README.md)
DECISIONS.md           Every data removal/change with exact counts: sections F, A, W, M (★ M3 section to add, Phase 4)
context/               milestone1/2/3.md briefs, Final Proposal.md, milestone3_plan.md, this file
package.json           npm dependency for render_docx.js (`npm install` restores node_modules/, which is gitignored)
```

★ = new in Milestone 3.

---

## 4. How to run

```powershell
python -m pip install -r requirements.txt
python -m pip install docx2pdf            # Windows-only, PDF export via Word
npm install                               # restores node_modules/ for render_docx.js
# from the repository root:
jupyter nbconvert --to notebook --execute --inplace modeling.ipynb     # ~4.5 min, 8 cores
```

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
- The notebook was generated with a throwaway builder script in a session scratchpad (not in the repo). **The
  notebook itself is now the source of truth:** edit its cells directly (or with `NotebookEdit`), then re-execute.
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

### 8.3 Feature sets as implemented (`src/modeling.py`)

- `AQ_HISTORY` = `persist_index, index_lag1, index_lag2`
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

## 9. Milestone 3 results (all from `docs/tables/m3_*.csv`; validation = Sep–Dec 2023)

### 9.1 Data after the D12 drops (`m3_split_balance.csv`)

| | City-days | Dates | Spikes | Rate |
|---|---|---|---|---|
| Train | 4,246 (76.6%) | 2022-08-06 → 2023-08-31 | 204 | 4.80% |
| Validation | 1,298 (23.4%) | 2023-09-04 → 2023-12-30 | 89 | 6.86% |

Dropped: 33 skip rows, 11 validation rows without a target (31 Dec 2023), 22 training rows without `index_lag2`
(first 2 days per city), 44 suspect feature-day rows and 11 suspect target-day rows (12 Dec 2022). That is 55
suspect-related training rows in all, and none in validation. All validation spikes fall in Nov (12) and Dec (77).

**CV folds** (`m3_cv_folds.csv`): each fold holds out 11–12 weeks (825–869 rows), and the purge plus embargo remove
330–495 fit rows. The test-fold spike rate averages 4.81% (SD 1.35, range 3.45–7.08) against 4.80% overall.

### 9.2 Tuned models and thresholds (`m3_params.json`, `m3_tuning_*.csv`)

| Model | Best setting | CV PR-AUC | OOF threshold (5:1) |
|---|---|---|---|
| LR full | C = 100, L2, no weights | 0.6048 | 0.0999 |
| LR no-fire | C = 19.31, L1, no weights | 0.6109 | 0.0927 |
| LR weather-only | C = 0.0052, L2, no weights | 0.4319 | 0.1009 |
| DT full | depth 6, leaf 50, balanced | 0.3495 | 0.6662 |
| DT no-fire | depth 6, leaf 50, balanced | 0.3613 | 0.7073 |
| DT weather-only | depth 3, leaf 10, no weights | 0.3368 | 0.1173 |
| Majority | – | – | never alert |
| Persistence (benchmark) | today's spike → tomorrow | 0.6362 (CV) | fixed rule |

### 9.3 Validation metrics (`m3_metrics_validation.csv`, 95% block-bootstrap CIs over 18 weeks, 1,000 resamples)

| Model | PR-AUC [CI] | ROC-AUC | Recall | Precision | F1 | Specificity | Accuracy | Cost /1,000 at 5:1 |
|---|---|---|---|---|---|---|---|---|
| Majority class | – | – | 0.000 | – | 0.000 | 1.000 | 0.931 | 342.8 |
| Persistence | **0.669** [0.344, 0.765] | 0.963 | 0.618 | 0.688 | 0.651 | 0.979 | 0.955 | 150.2 |
| LR full | 0.634 [0.316, 0.730] | 0.961 | 0.831 | 0.446 | 0.580 | 0.924 | 0.918 | 128.7 |
| LR no-fire | 0.647 [0.317, 0.740] | 0.963 | 0.888 | 0.451 | 0.598 | 0.921 | 0.918 | **112.5** |
| LR weather-only | 0.388 | 0.855 | 0.764 | 0.228 | 0.351 | 0.810 | 0.807 | 258.1 |
| DT full | 0.373 | 0.852 | 0.562 | 0.329 | 0.415 | 0.916 | 0.891 | 228.8 |
| DT no-fire | 0.371 | 0.836 | 0.663 | 0.303 | 0.415 | 0.888 | 0.872 | 220.3 |
| DT weather-only | 0.226 | 0.837 | 0.865 | 0.236 | 0.371 | 0.794 | 0.799 | 238.1 |

Confusion counts (TP/FP/TN/FN): persistence 55/25/1,184/34; LR full 74/92/1,117/15; DT full 50/102/1,107/39.
CV (mean ± SD over 25 folds, `m3_metrics_cv.csv`): persistence PR-AUC 0.636 ± 0.141, cost 114.0; LR full
0.605 ± 0.108, cost 93.8; majority accuracy 0.952, cost 240.6.

**Reading:** persistence ranks spikes as well as any model, but at the 5:1 alert decision LR is cheaper and catches
far more spikes. Accuracy is misleading: the majority class beats every model on it while catching no spike.

### 9.4 Fire ablation (`m3_fire_ablation.csv`): fires add no next-day skill

| Comparison | ΔPR-AUC on validation [CI] | ΔROC-AUC [CI] | CV folds where the first model is better |
|---|---|---|---|
| LR full − LR no-fire | −0.0130 [−0.0235, +0.0098] | −0.0020 [−0.0033, −0.0001] | 10/25 |
| DT full − DT no-fire | +0.0018 [−0.0263, +0.0309] | +0.0162 [−0.0042, +0.0577] | 7/25 |
| LR no-fire − LR weather-only | **+0.2590** [+0.0934, +0.3899] | +0.1079 | 25/25 |
| LR full − persistence | −0.0349 [−0.0713, +0.0504] | −0.0022 | 8/25 |
| DT full − persistence | −0.2962 [−0.4166, −0.1586] | −0.1112 | 0/25 |

The interpretation agreed for the report: fires may still cause smog (Milestone 2 found ρ ≈ 0.24 at lag 1), but
their smoke is already in today's index, the strongest input. The month-wise label (9.8) gives the same null, so the
result is not just an artefact of the fog-season label.

### 9.5 Asymmetric cost (`m3_cost.csv`, `m3_cost_curve.csv`)

- **At 5:1**, per 1,000 city-days: never alert 342.8; always alert 931.4; persistence 150.2 (34 FN, 25 FP);
  LR full 128.7 (15 FN, 92 FP; 62.5% saving vs never alert); LR no-fire 112.5 (10 FN, 96 FP; 67.2%).
- **The cost curve:** persistence is cheaper only at ratios 1 and 2. **LR full is cheaper at every ratio from 3 to 20**
  (at 20:1 it costs 243.5 against 543.1). DT full beats persistence only from 13:1.
- **The price:** LR full false-alarms on 7.6% of non-spike days, against 2.1% for persistence.
- A qualitative FP/FN consequence table is in the M3.6 Markdown cell:
  - FN = sensitive groups exposed without warning;
  - FP = needless closures, lost wages, alert fatigue.

### 9.6 Errors and edge cases (`m3_errors_onset.csv`, `m3_errors_city_month.csv`, `m3_top_errors.csv`, `m3_fn_context.csv`)

- **Onsets** (tomorrow a spike, today not):
  - persistence catches 0 of 34 by construction;
  - **LR full catches 19 of 34 (55.9%)** and all 55 continuation days;
  - DT full catches 10 of 34 onsets and misses 15 continuations.
- **LR false alarms by day type:** 69 on onset-type days and 23 on episode ends.
- **By month:** LR misses 4 spikes in Nov and 11 in Dec; 74 of its 92 false alarms are in Dec.
- **By city:**
  - LR misses: Faisalabad 4, Rahim Yar Khan 4, Ferozepur 3, Amritsar 2, Multan 2;
  - LR false alarms: Ferozepur 18, Faisalabad 15, Multan 12, Rahim Yar Khan 11;
  - Lahore and Islamabad/Rawalpindi have very few errors of either kind.
- **The 10 worst misses** are all late-December onsets with LR probability < 0.10 (for example Amritsar 25 Dec,
  Faisalabad 12/23/25/28 Dec).
- **Feature day of missed vs caught spikes:**
  - stagnant: 0% vs 26%;
  - humidity: 73.9% vs 80.0%;
  - today's margin over the threshold: −0.38 vs +0.12;
  - fires were *higher* on missed days (68 vs 53).
- **The most confident false alarms** are episode ends just under the threshold (for example Rahim Yar Khan,
  10 Dec: next-day index 0.23 against a threshold of 0.36).

### 9.7 Drivers (`m3_odds_ratios.csv`, `m3_h2_logit.csv`, `m3_importance.csv`)

- **Grouped permutation importance** (drop in validation PR-AUC):
  - LR full: AQ history 0.524, City 0.322, Rain 0.055, Month 0.023, Humidity 0.019; fires −0.011 (nothing);
  - DT full: AQ history 0.281, Mean temperature 0.185.
- **DT Gini importance:** `persist_index` 0.72, `temp_mean_c` 0.13, `temp_range_c` 0.05,
  `fire_cnt_up45_r300_all_lag1` 0.04.
- **LR full odds ratios** (per 1 SD for continuous columns, 0→1 for binaries):
  - `persist_index` 49.2, `rain_day` 0.005;
  - `temp_range_c` 1.93, `rh_mean_pct` 1.41, `stagnant` 1.38, `stagnant_lag1` 0.41, `vec_len_kmh` 0.78;
  - fire lag 1 1.43 and lag 2 0.79 (they cancel);
  - `wind_from_sw` 0.12.
- **City dummies are huge** (Rahim Yar Khan 9,004; Islamabad 3,721; vs Lahore). This is a **threshold
  correction, not a risk ranking**: the model reads one pooled index, but each city has its own threshold.
  Say this explicitly in the report. A feature `persist_index − spike_threshold` would remove it (Milestone 4).
- **Month dummies** for Mar–Aug are strongly negative (no spikes in those months, near-separation at C = 100).
- **H2 (weather trap) is supported on every component.** Logit on 1,706 rain-free Sep–Feb training rows (204 spikes),
  pseudo R² 0.258, city-clustered SE (11 clusters):

  | Term | Odds ratio | 95% CI |
  |---|---|---|
  | stagnant | **3.24** | [1.91, 5.48] |
  | RH, per SD | **3.95** | [2.03, 7.69] |
  | temperature range, per SD | **2.22** | [1.66, 2.95] |
  | mean temperature, per SD | 2.08 | [0.87, 5.00], p = 0.10 |

  - Rain: 0 of 1,057 rain days vs 204 of 3,189 dry days are followed by a spike (one-sided Fisher p = 8.1 × 10⁻²⁷).
  - The week-clustered check gives the same conclusions (temperature range p = 0.006).
  - In the forecasting model, stagnation adds little permutation importance because today's index already absorbs
    it (stagnant air today means smog today).
- **Depth-3 tree** (`fig_m3_7`):
  - first split: `persist_index ≤ 0.39`;
  - then, on the high side, `temp_mean_c ≤ 18.88 °C` (81% spike share);
  - validation PR-AUC 0.364, ROC-AUC 0.867.

### 9.8 Sensitivity (`m3_label_monthwise.csv`, `m3_horizons.csv`)

- **Month-wise label:**
  - train spike rate 11.4%; validation only 4.1% (Sep 0.3%, Oct 1.2%, Nov 5.5%, Dec 8.8%), because autumn 2023 was
    cleaner than autumn 2022;
  - validation PR-AUC: persistence 0.439 (CV 0.316), LR full 0.307 (CV 0.234), LR no-fire 0.325 (CV 0.231),
    LR weather-only 0.090;
  - **fire still adds nothing.**
- **Horizons** (validation PR-AUC at h1 / h2 / h3):

  | Model | h1 | h2 | h3 |
  |---|---|---|---|
  | Persistence | 0.669 | 0.553 | 0.445 |
  | LR full | 0.634 | 0.575 | 0.480 |
  | LR no-fire | 0.647 | 0.604 | 0.485 |

  - CV does not confirm the h2/h3 LR advantage: LR full 0.298 and 0.229 against persistence 0.447 and 0.375. It reuses
    the h1 hyperparameters → per-horizon tuning goes on the Milestone 4 roadmap.
  - At h3 the DT full and DT weather-only models issue **no alerts** on validation (recall 0).

### 9.9 Figures (all `figures/fig_m3_*.png`, 300 dpi, Okabe-Ito; colour = feature set, solid = LR, dashed = DT, black = persistence, grey = majority)

| File | Content |
|---|---|
| `fig_m3_1_cv_folds` | A: repeat-1 fold layout over the training calendar (fit / purged-embargoed / held out / dropped); B: spike rate per test fold |
| `fig_m3_2_tuning` | CV PR-AUC vs C (LR) and vs depth (DT), 3 feature sets, ±1 SD bands |
| `fig_m3_3_roc_pr` | Validation ROC and PR curves for 7 models; markers at the 5:1 operating points |
| `fig_m3_4_cost_curve` | Validation cost per 1,000 city-days vs FN:FP ratio 1–20, with never/always-alert references |
| `fig_m3_5_confusion` | 2×2 matrices (counts and %) for persistence, LR full, DT full |
| `fig_m3_6_drivers` | A: LR full odds ratios (log scale, bars from OR = 1); B: grouped permutation importance, LR vs DT |
| `fig_m3_7_tree` | Depth-3 decision tree |

---

## 10. Notebook map (`modeling.ipynb`, 46 cells)

| Section | Produces |
|---|---|
| Header + setup | imports, `MODELS`/`LABEL`/`COLOR`/`STYLE` dicts, asserts `role2_params` fire tag = `up45_r300` |
| M3.1 Data and leakage guards | `m3_split_balance.csv`; `assert_train_only()` helper; why not a random split |
| M3.2 CV design | `m3_cv_folds.csv`, `fig_m3_1` |
| M3.3 Baselines + tuning | `m3_tuning_lr.csv`, `m3_tuning_dt.csv`, `fig_m3_2`, OOF predictions, thresholds, `m3_params.json`. Thresholds are fixed **before** any validation metric (stated in a Markdown cell) |
| M3.4 Metrics | `m3_metrics_cv.csv`, `m3_metrics_validation.csv` (long: model, metric, estimate, ci_low, ci_high, n_weeks), `m3_validation_counts.csv`, `fig_m3_3`; persistence hand-count assert |
| M3.5 Fire ablation | `m3_fire_ablation.csv` (paired bootstrap + per-fold CV differences) |
| M3.6 Error cost | FP/FN consequence table (Markdown), `m3_cost.csv`, `m3_cost_curve.csv`, `fig_m3_4` |
| M3.7 Confusion + edge cases | `m3_confusion.csv`, `m3_errors_onset.csv`, `m3_errors_city_month.csv`, `m3_top_errors.csv`, `m3_fn_context.csv`, `fig_m3_5` |
| M3.8 Drivers | `m3_odds_ratios.csv`, `m3_h2_logit.csv`, `m3_importance.csv`, `fig_m3_6`, `fig_m3_7` |
| M3.9 Sensitivity | `m3_monthwise_thresholds.csv`, `m3_label_monthwise.csv`, `m3_horizons.csv` |
| M3.10 Artifacts | `models/*.joblib`, package versions, total run time (~259 s) |

Every computational section is followed by a "What we found" Markdown cell with the numbers above.

---

## 11. What is left: Phases 4 and 5 (from `context/milestone3_plan.md`)

### Phase 4: `DECISIONS.md` section for Milestone 3 → commit "Decision log: Milestone 3 modelling choices"

- Add a section after "Merge and analysis (Role 2)", in the same table style as F/A/W/M. Use numbered rows, e.g. `S1…`
  (avoid clashing with the existing `M1–M10` ids).
- List D3–D13 **and X1–X8** (section 8.2) with exact counts from section 9.1:
  - 4,246 / 1,298 rows; 33 skip, 11 no target, 22 no lag, 44 + 11 suspect;
  - best hyperparameters and thresholds from 9.2;
  - the CV settings (5 × 5, seeds 0–4, purge 1 day, embargo 3 days, 330–495 rows removed per fold);
  - calm ≡ stagnant (631/631); rain 0/1,057; Mar–Aug 0 spikes.

### Phase 5: manuscript and submission package → commit "Milestone 3 report sections and submission package"

**`docs/manuscript/build_manuscript.py`:**
- Keep Sections 1–6 unchanged and add one sentence to the abstract.
- Insert Sections 7–12 **before** the existing `h2("References")` call (currently line 409), so References move to
  the end.
- Read numbers **only** from `docs/tables/m3_*.csv`, so every number matches the notebook.
- Add references and verify each one; the cloud session wrote them from memory:
  - scikit-learn (Pedregosa et al. 2011, JMLR 12);
  - Roberts et al. 2017, *Ecography*, on blocked CV for structured data;
  - Saito & Rehmsmeier 2015, *PLOS ONE*, on PR vs ROC for imbalanced data.
- Update Section 6 (Reproducibility) with `modeling.ipynb`, `src/modeling.py`, `src/evaluate.py` and `models/`.

**Sections, about 5–6 pages in total:**
- **7 Baseline Models and Justification.**
  - Majority: the floor, and why accuracy misleads.
  - Persistence: the benchmark.
  - LR: interpretable odds ratios and calibrated probabilities.
  - Shallow DT: non-linear trap rules that officials can read.
- **8 Experimental Setup.**
  - Chronological split, 76.6/23.4, with a 3-day gap.
  - Why not random or plain stratified K-fold (ρ = 0.82 day to day; Islamabad = Rawalpindi; same-day weather).
  - Purged and embargoed grouped CV, and the stratification check.
  - Tuning grids, PR-AUC as the tuning metric, and the OOF threshold rule.
  - Leakage guards.
  - The solver note (X1).
- **9 Results.** Metrics table (9.3), ROC/PR figure, fire ablation (9.4), month-wise label and horizons as short
  sensitivity paragraphs.
- **10 Asymmetric Error Cost Analysis.** FN/FP consequence table, cost at 5:1, cost curve (break-even 3:1 vs
  persistence), confusion matrices, onset vs continuation, edge cases (9.6).
- **11 Drivers and Initial Policy Takeaways.**
  - The H2 table, permutation importance, the tree.
  - **Explain the city-dummy artefact.**
  - Policy points, Pakistan first, then cross-border:
    - a next-day advisory driven by today's index plus a weather-trap check (stagnant, humid, rain-free,
      large day-night range);
    - rain as an all-clear signal;
    - a ≥ 3:1 cost view justifies a model-based alert over persistence;
    - fire control is a source-reduction policy whose benefit shows up in today's smog, not as extra next-day
      forecast skill;
    - the cross-border claim can't be settled from these baselines (H4 → Milestone 4).
- **12 Limitations and Milestone 4 Roadmap.**
  - Limitations:
    - no model beats persistence on ranking;
    - class imbalance, and one training winter;
    - 18 validation weeks, 77 of 89 spikes in December;
    - Islamabad/Rawalpindi duplicate series;
    - the label-timing artefact (partly answered by the month-wise run);
    - the city-threshold artefact;
    - CAMS model data rather than monitors, and UTC+5 for India.
  - Milestone 4 work:
    - RF/GBM;
    - a threshold-margin feature;
    - per-horizon tuning;
    - probability calibration;
    - a fairness audit of error rates by city and PK vs IN (LR false alarms concentrate in Ferozepur, Faisalabad,
      Multan and Rahim Yar Khan);
    - the H1/H3/H4 tests;
    - surface pressure;
    - the 2024 out-of-time test.

**`docs/manuscript/render_docx.js`:**
- Add an optional CLI argument for the milestone, defaulting to 2 so the Milestone 2 build stays identical.
- **Current behaviour to know:**
  - it reads `docs/manuscript/manuscript.json`;
  - it writes `Milestone2_Manuscript_Draft.docx` at the **repo root** (line 148);
  - the footer text is hard-coded as "Trans-Boundary Smog Prediction, Milestone 02" (line 141).
- Check how `submission/Milestone2_Report.docx` was produced before changing paths (probably a copy of that output).
- With argument `3` it should write `submission/milestone3/Milestone3_Report.docx` with the footer "Milestone 03".
- Note that `build_manuscript.py` writes a single `manuscript.json`. The Milestone 2 rebuild must still be possible,
  for example by building the M3 sections only when a flag or argument is set.

**PDF:**
- `python -c "from docx2pdf import convert; convert('submission/milestone3/Milestone3_Report.docx')"`.
- Fallback: Word → Save As PDF.
- Check that the figures render and the total is about 16 pages.
- Spot-check 5 numbers in the PDF against the CSVs.

**`submission/milestone3/`:**
- `Milestone3_Report.docx` and `.pdf`;
- a copy of the executed `modeling.ipynb`;
- `README.md` with how to run and a file map (modules, tables, figures, models, `m3_params.json`).

**Final verification (from the plan):**
- `git log -5 --format='%an <%ae>%n%b'` shows only bilal and no trailers.
- `git branch -a` shows only `main`.

---

## 12. Rubric reminders

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
- the split balance is checked rather than forced.

Explain this in §8.

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
  0.10 for LR. This is not a bug.
- **Rerunning `merge_analysis.ipynb`** regenerates `master_daily.parquet` with identical data but different bytes.
  Avoid it, or `git checkout` the file afterwards.
- **The AQ notebook** defines its own `TRAIN_START/END` and does not import `src/config.py`. This matters for Week 14.
- **Report tables are at 4 decimals on purpose:** rounding twice from 3 decimals rounded some values the wrong way.
- `requirements.txt` is UTF-8. An older UTF-16 Windows freeze existed, so don't restore it.
- **Git warnings** "LF will be replaced by CRLF" on commit are normal on this machine.
- **Week 14:**
  - change `WINDOW_START/END` and the split dates in `src/config.py`;
  - add the 2024 files to `NASA_FILES`;
  - rerun all notebooks, including `modeling.ipynb`;
  - the `SEALED_FROM` assert in `src/modeling.py` must then be moved deliberately.
