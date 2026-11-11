# Data decisions log

Every step that removes or changes data, with exact row counts, so the report's data audit can be written straight from here.
Each data stream gets its own section. Numbers come from the notebook's printed output; update them if the notebook changes.

## Fire (NASA VIIRS), `fire.ipynb`, owner: Person C

Raw input: 4 files (2022 and 2023, India and Pakistan), 1,284,773 points, all NOAA-20 (`N`), version 2, 0 duplicates.

| # | Decision | Rule | Rows before → after | Removed | Why | Sensitivity check |
|---|---|---|---|---|---|---|
| F1 | 2024 files not used | `NASA_FILES` in `src/config.py` lists 2022 and 2023 only | 6 files → 4 files | 2024 India + Pakistan files | Reserved for the Week 14 out-of-time extension; never read in this milestone | None |
| F2 | Study-area box | Keep lat 26–37 N, lon 68–79 E | 1,284,773 → 287,323 | 997,450 | The India file covers all of India; the box keeps every point within 300 km (largest radius) of the 11 cities | None needed (points outside can never be within 300 km) |
| F3 | Vegetation fires only | Keep `type == 0` | 287,323 → 279,968 | 7,355 (type 2: 7,305; type 3: 50) | Type 2 = static land sources (brick kilns, industry, flares) at 144 fixed locations, roughly flat across months, so they cannot explain day-to-day smog; type 3 = offshore. Hypotheses are about crop burning | None |
| F4 | Drop low confidence | Keep confidence `n` and `h` | 279,968 → 238,796 | 41,172 | `l` = daytime only, weak heat signal, often sun glint or hot bare ground. It is 27–36% of Apr–May points but only 2–8% of Oct–Nov points | Two kept versions: `n+h+l` (279,968 points) and `h` only (8,534 points), as columns `fire_*_r150_conf_nhl_*` and `fire_*_r150_conf_h_*` |
| F5 | Date window after the time shift | UTC + 5 h, then keep local dates 2022-01-01 to 2023-12-31 | 238,796 → 238,756 | 40 | Detections on the evening of 31 Dec 2023 UTC fall on 1 Jan 2024 local time | None |
| F6 | Cone features left empty when there is no wind | Cone and `stagnant` columns are NaN on city-days missing from `Dataset/clean/wind_daily.parquet` | 8,030 → 7,852 city-days with cone values | 178 city-days (1–11 Jan 2022 for Pakistani cities; up to 29 Jan 2022 for Indian cities) | The weather files start mid/late January 2022, so there is no wind direction for these days; writing 0 would claim "no upwind fires". Radius columns stay complete | None needed: all 178 days fall before the modelling window (2022-08-04) |

Known gap (no rows removed): detections from 31 Dec 2021 (UTC 19:00–24:00) would belong to 1 Jan 2022 local time, but 2021 files were not downloaded, so the first local day is missing up to 5 hours of fires. This is irrelevant for modeling, which starts on 2022-08-04.

Settings fixed for the daily features (not removals, recorded for consistency):
- City coordinates come from the weather file headers (`CITY_COORDS` in `src/config.py`).
- Radii: 50, 100, 150, 200, 300 km. Cones: ±30/45/60° upwind and ±45° downwind (placebo). Provisional default: 150 km; the merge chose ±45° upwind at 300 km from the training data (see M6 below).
- Days with no fires are 0, never missing (8,030-row city-day grid).
- Wind for the cones: Person B's `wind_dir_daily_deg` (vector mean of hourly winds, direction the wind comes FROM).
- Stagnant days (Person B's flag: daily vector-mean wind < 2 km/h, 10.7% of city-days): the cone count equals the radius count.
- Outliers are flagged (`out_z_*`, `out_iqr_*`), never deleted.

## Air quality (Open-Meteo / CAMS), `air_quality.ipynb`, owner: Person A

Raw input: 11 files (7 Pakistani CSV, 3 Indian CSV, Ludhiana XLSX), 453,192 hourly rows, 0 duplicate or skipped hours.

| # | Decision | Rule | Rows before → after | Removed | Why | Sensitivity check |
|---|---|---|---|---|---|---|
| A1 | Study years | Local (UTC+5) dates 2022-01-01 to 2023-12-31 | 453,192 → 191,153 | 262,039 | 2024 sealed for Week 14; later years out of scope | None |
| A2 | Negative concentrations | Set to 0 | 0 rows (218 cells: NO2 19, O3 197, dust 2) | 0 | A concentration cannot be negative; log1p needs x ≥ 0 | None |
| A3 | Empty block not imputed | Drop hourly rows with no pollutant value | 191,153 → 135,905 | 55,248 (28.9%) | The source has no values before 2022-08-04 in any city; filling 7 months would invent data | None (structural) |
| A4 | Short-gap interpolation | Linear, at most 6 hours | 0 cells filled | 0 | Kept for 2024; no gap exists after 2022-08-04 | None |
| A5 | Daily completeness | Keep a day only with ≥ 18 valid hours | 5,665 → 5,665 city-days | 0 | 11 first days have 19 hours, all others 24 | None |
| A6 | Suspect days flagged, not removed | `suspect_day = 1` on 13-16 Dec 2022 (PM2.5 < 2 ug/m3 in all cities) | 0 | 0 (44 city-days flagged) | Likely source error; excluded from A's learned parameters, kept in Role 2 statistics by team decision | Index skew −1.15 with them, +0.26 without |
| A7 | Islamabad = Rawalpindi | Kept both | 0 | 0 | Identical AQ series (same model grid cell): 10 independent AQ series | Stated as a limitation |

Spike thresholds (P90 of training Oct–Mar index per city) and z-score parameters: `Dataset/clean/aq_params.json`.

## Weather (Open-Meteo), `weather.ipynb`, owner: Person B

Raw input: 11 files (10 CSV, Ludhiana XLSX), 433,728 hourly rows, 0 missing values, 0 duplicates.

| # | Decision | Rule | Rows before → after | Removed | Why |
|---|---|---|---|---|---|
| W1 | Study years | Local (UTC+5) dates 2022-01-01 to 2023-12-31 | 433,728 → 188,393 hourly | 245,335 | 2024 sealed; later years out of scope |
| W2 | Hourly to daily | Mean (temperature, humidity, wind speed), total (rain), min/max/range (temperature), vector mean (wind) | 188,393 → 7,852 city-days | - | All targets and fire counts are daily |
| W3 | Stagnation flag | `stagnant = 1` if daily vector-mean wind < 2 km/h | - | 0 (837 of 7,852 flagged) | Daily direction is noise below this; 3 km/h would flag a third of days in some cities |
| W4 | Rain day | `rain_day = 1` if daily rain ≥ 1 mm | - | 0 | Separates real rain from trace values |
| W5 | Surface pressure | Not used in Milestone 2 | - | - | Not in the exported files; team decision to drop it for Milestone 2 (it can be re-exported for the same coordinates in Week 14); temperature range and stagnation are the stated proxies |

## Merge and analysis (Role 2), `merge_analysis.ipynb` + `src/merge.py`, lead: Person B

| # | Decision | Rule | Rows before → after | Why |
|---|---|---|---|---|
| M1 | Modelling window for all streams | Keep 2022-08-04 to 2023-12-31 (team decision; replaces the work plan's 8,030-row spine) | AQ 5,665 → 5,665; weather 7,852 → 5,665; fire 8,030 → 5,665 | AQ has no data before 2022-08-04; 2022 rows would be empty targets |
| M2 | Lag lead-in | Weather and fire read from 3 days before the window for their 1–3 day lags, then cut | - | Lags on the first window days stay complete |
| M3 | Spine and joins | Spine 11 × 515 = 5,665; left joins on city, country, date with `validate="one_to_one"` | 5,665 after every join; every spine row matched | Missing days stay visible; key mismatches fail loudly |
| M4 | Targets | `target_index_h{1,2,3}`, `target_spike_h{1,2,3}` with A's thresholds, grouped by city | 5,654 / 5,643 / 5,632 rows with a target | Targets that fall in 2024 are left missing (sealed) |
| M5 | Duplicate stagnant column | Fire table's `stagnant` dropped before the join | - | Verified identical to the weather flag |
| M6 | Default fire setting | ±45° upwind cone, 300 km (was 150 km in the work plan) | - | Highest median Spearman (fire day t vs index day t+1) over the 7 Pakistani cities in training Oct–Dec: 0.23, vs −0.06 for the 300 km circle and 0.01 for the downwind placebo |
| M7 | Weather-trap cut-offs | Humid: RH > 77.06% (training P75); large temperature range: > 13.6 °C (training P75) | - | Saved in `Dataset/clean/role2_params.json` |
| M8 | Temperature-range direction | Trap proxy = large range (work plan said small) | - | 0 of 61 small-range harvest days preceded a spike vs 15.4% of large-range days; a large range marks clear nights with radiative inversions |
| M9 | Suspect days and Islamabad/Rawalpindi | Kept as rows in the master and in the Role 2 statistics (unless a table says otherwise); thresholds and scaling are learned without the suspect days | - | Team decision: removing 4 days would break each city's unbroken daily calendar, which the 1–3 day lags and targets need; `suspect_day` lets Milestone 3 drop them; their effect is reported (index skew −1.15 with them, +0.26 without). Both listed as limitations |
| M10 | Encoding | Dummies: city (Lahore ref.), `is_india`, `near_border`, `harvest_season`, month (January ref.), 8 wind sectors (calm ref.) | 287 columns in the master | One reference category each to avoid the dummy trap |

## Milestone 3 modelling, `modeling.ipynb` + `src/modeling.py` + `src/evaluate.py`

Every fit, scaler, threshold and hyperparameter uses `split == "train"` rows only (2022-08-06 to 2023-08-31 after the drops); the validation split (2023-09-04 to 2023-12-30) only reports results; 2024 is sealed (`load_model_frame()` asserts no date ≥ 2024-01-01). Hyperparameters and thresholds are saved in `Dataset/clean/m3_params.json`. The original plan ids (D…) and the departures made while coding (X…) are given in brackets.

| # | Decision | Rule | Rows before → after | Why |
|---|---|---|---|---|
| S1 | Modelling rows (D12) | Drop the 3-day skip, rows with a missing target or feature, and rows whose feature day **or** target day (t + h) is a `suspect_day` | 5,665 → 5,544 for h = 1: 33 skip; 11 validation rows without a target (31 Dec 2023); 22 training rows without `index_lag2` (first 2 days per city); 44 suspect feature-day rows; 11 suspect target-day rows (12 Dec 2022). Train 4,246 (204 spikes, 4.80%), validation 1,298 (89 spikes, 6.86%), a 76.6 / 23.4 split | The suspect days (13–16 Dec 2022) have near-zero pollutants in every city; kept in the master so the calendar stays unbroken, but never fitted or scored. Validation has no suspect day |
| S2 | Headline target and label (D2, D3) | `target_spike_h1` with the Milestone 2 label (city P90 of training Oct–Mar). h2/h3 reuse the h1 hyperparameters (one compact table). Sensitivity: month-wise label, `target_index_h1` ≥ city × month P90 of training days | Month-wise label: train spike rate 11.4%, validation 4.1% | The Milestone 2 label puts most spikes in Dec–Jan, after the burning peak; the month-wise label checks that the fire result is not a label artefact |
| S3 | Models and feature sets (D4, D7) | Majority class, persistence, logistic regression (LR), decision tree (DT). LR and DT on **full** (42 columns), **weather-only** (35) and **no-fire** (38 = full minus the 4 fire columns) | – | RF/GBM go to Milestone 4; KNN not used (distances on mixed binary and continuous columns, no interpretability) |
| S4 | AQ history as a threshold margin (Q4, headline) | `persist_margin`, `margin_lag1`, `margin_lag2` = index on day t, t − 1, t − 2 minus the city's `spike_threshold`; asserted: margin ≥ 0 ⇔ `persist_spike = 1`. Fixed before any result was seen. Raw-index version (`FULL_RAW`) retuned as a sensitivity run (M3.9c, `m3_aq_encoding.csv`) | – | The label is defined relative to each city's threshold (0.36 to 2.18); with the raw pooled index the city dummies acted as a threshold correction (city odds ratios up to 9,004 vs Lahore). The thresholds are learned on all training rows in Milestone 2, so CV folds share them, exactly as they share the label itself; no new leakage |
| S5 | Wind-sector reference (X3) | `wind_from_nw` dropped; NW is the reference sector instead of calm | – | `calm` ≡ `stagnant` on 631 of 631 rows, so all 8 sectors plus `stagnant` are collinear with the intercept. NW is the most frequent sector (1,320 rows) |
| S6 | Other columns left out | `wind_speed_mean_kmh` (ρ 0.85 with `vec_len_kmh`), temperature min/max (r 0.91–0.98 with the mean) | – | Near-duplicates |
| S7 | Cross-validation (D5, X2) | Purged, repeated `StratifiedGroupKFold`: 5 folds × 5 repeats (seeds 0–4) = 25 folds; group = calendar week shared by all cities. Purge: drop fit rows whose target day is held out (1 day for h = 1). Embargo: drop fit rows up to h + 2 days after a held-out day (3 days for h = 1; `MAX_AQ_LAG = 2`) | Each fold holds out 11–12 weeks (825–869 rows); purge + embargo remove 286–495 fit rows per fold. Test-fold spike rate 4.81% ± 1.35 (range 3.45–7.08%) vs 4.80% overall | Neighbouring days are near-duplicates (ρ = 0.82), Islamabad = Rawalpindi, cities share same-day weather; AQ history reaches back to t − 2, so a row after a held-out day carries its target |
| S8 | No random stratified outer split (Q1) | The outer split is chronological; stratification is applied inside the grouped CV and checked, not forced. Leakage check on training rows (`m3_leakage_check.csv`): LR full PR-AUC 0.730 (random stratified 80/20), 0.677 (plain StratifiedKFold), 0.651 (grouped, no purge), 0.651 (ours) | – | The brief asks for stratified sampling; the check shows numerically that random splits overstate skill (by 0.08 PR-AUC for LR, 0.13 for DT) |
| S9 | Tuning (D5) | `GridSearchCV` on the 25 purged folds, scoring PR-AUC, refit on all training rows. LR grid: C ∈ logspace(−3, 2, 8), `l1_ratio` ∈ {0, 1}, class weight none/balanced (32). DT grid: depth 2–8, min leaf 10/25/50/100, class weight none/balanced (56) | Best: LR full C = 0.0268, L1, no weights (CV PR-AUC 0.6508); LR no-fire the same setting (0.6507); LR weather-only C = 0.0052, L2 (0.4319); DT full depth 4, leaf 50, no weights (0.5190); DT no-fire the same (0.5193); DT weather-only depth 3, leaf 10 (0.3368) | Spikes are rare (4.8%); PR-AUC focuses on the positive class |
| S10 | LR solver (X1) | `liblinear` with `intercept_scaling = 10` instead of `saga` | – | `saga` hit the 5,000-iteration cap at large C with balanced weights (≈ 8 s per fit); `liblinear` converges in < 0.2 s with fold PR-AUC within 0.005 |
| S11 | Alert thresholds and cost ratio (D6, Q3) | Threshold = minimum of 5·FN + 1·FP on the out-of-fold training predictions, fixed before any validation metric. Cost curve: ratios 1 to 20, threshold re-chosen on OOF predictions at each ratio | Thresholds: LR full 0.1280, LR no-fire 0.1280, LR weather-only 0.1009, DT full 0.1988, DT no-fire 0.1988, DT weather-only 0.1173; majority = never alert | 5:1 is a stated policy assumption, not an estimate: no verified source prices a missed smog day against an unnecessary advisory. The health burden is large (India 2019: 1.67 million deaths, US$36.8 billion, 1.36% of GDP; Pandey et al. 2021), so the report leads with the break-even ratio on the cost curve |
| S12 | Persistence score (X4) | Score = `persist_index − spike_threshold`; alert rule unchanged (`persist_spike`) | – | Thresholds differ by city, so the raw pooled index is not comparable across cities for ROC/PR. Score ≥ 0 ⇔ `persist_spike = 1` (asserted) |
| S13 | H2 test (D8, X5) | `statsmodels` Logit on training rows in Sep–Feb with `rain_day = 0`, city-clustered SE (week-clustered check); continuous terms standardised on that sample; controls: mean temperature, months 2/9/10/11/12 (Jan ref.), city dummies. Rain: one-sided Fisher exact test on all training rows | Logit n = 1,706 (204 spikes). Rain: 0 of 1,057 training rain days precede a spike vs 204 of 3,189 dry days. March–August: 0 spikes | Perfect separation: no finite MLE for `rain_day` or months 3–8. `vec_len_kmh` left out of the controls because `stagnant` is defined from it. H1, H3, H4 go to Milestone 4 |
| S14 | Grouped permutation importance (X6) | Correlated columns shuffled together (AQ history, fire lags, stagnant t/t − 1, wind sectors, months, cities); 30 repeats; drop in validation PR-AUC | – | Per-column permutation splits credit between near-duplicate lags |
| S15 | Persistence in sensitivity CV (X8) | Persistence scored on the same purged folds in the month-wise and h2/h3 runs | – | Gives those CV numbers a benchmark |
| S16 | Preliminary disparity check (Q2) | Persistence and LR full on validation: spikes, alerts, recall, FPR, precision per country with 95% week-block bootstrap CIs and the PK − IN gap; per city as point estimates (`m3_error_rates_group.csv`) | – | The brief asks about potential bias; the full fairness audit is Milestone 4 |
| S17 | Index regression check (Q7) | `Ridge` on `target_index_h1` with the LR preprocessing, alpha ∈ logspace(−2, 3, 11) tuned on the same folds by MAE; benchmark persistence (`persist_index`); paired week-block bootstrap ΔMAE (`m3_index_regression.csv`) | – | Milestone 2 promised results for the continuous index (H5, ΔMAE); a continuous target is a more sensitive test of the fire effect |
| S18 | Extra tables (X7) | `m3_validation_counts`, `m3_cost_curve`, `m3_top_errors`, `m3_fn_context`, `m3_monthwise_thresholds` | – | Back up specific report statements |
| S19 | Report and commits (D9–D13) | Milestone 2 Sections 1–6 kept (new title, one abstract sentence, one closing line in §4, updated §6) plus Sections 7–12; output in `submission/milestone3/`; single branch `main`; no file moves | – | The Milestone 2 report was already graded |

## Milestone 4 modelling and fairness audit, `advanced_modeling.ipynb` + `src/modeling.py` + `src/fairness.py`

Same rules as Milestone 3: every fit, weight, threshold and hyperparameter uses `split == "train"` rows only; validation (2023-09-04 to 2023-12-30) only reports; 2024 stays sealed.

| # | Decision | Rule | Rows before → after | Why |
|---|---|---|---|---|
| P1 | Sensitive attribute = geography; city-size tier as a socio-economic proxy (agreed with the instructor) | Groups: country (PK, IN), city (11) and tier from census population, city including its cantonments (`Dataset/external/city_population.csv`). Tier 1 metro ≥ 3 M; Tier 2 large 1–3 M; Tier 3 small < 1 M. Rule fixed before any fairness result. Result: T1 Lahore 13.00 M, Faisalabad 3.69 M, Rawalpindi 3.36 M; T2 Multan 2.22 M, Ludhiana 1.62 M, Amritsar 1.17 M, Islamabad 1.11 M; T3 Jalandhar 0.92 M, Sialkot 0.91 M, Rahim Yar Khan 0.52 M, Ferozepur 0.16 M | – | Pakistan 2023 census (PBS National Census Report Table 4.5 for Lahore and Islamabad; the citypopulation.de compilation of the PBS urban localities for the rest, matching the PBS text: Faisalabad 3.6 M, Rawalpindi 3.3 M). India: 2011 census, the latest held (citypopulation.de compilation). The official PBS locality tables and censusindia.gov.in could not be downloaded. PBS Table 4.5 prints district totals for several cities in its 2023 column (e.g. Sialkot 4.50 M), so it was not used for them. Limitations: 12 years between the two censuses; Jalandhar (0.92 M in 2011) has probably passed 1 M since |
| P2 | Advanced models | Random forest (RF) and histogram gradient boosting (HGB, scikit-learn's LightGBM-style learner) on the same three feature sets as Milestone 3 (full, weather-only, no-fire) | – | No new dependencies on Python 3.14; XGBoost, LightGBM and fairlearn are not installed. Same feature sets keep the fire ablation comparable |
| P3 | Search | `RandomizedSearchCV`, 60 draws per model and feature set, seed 42, scored by PR-AUC on the same 25 purged, embargoed, week-grouped stratified folds (S7). RF: trees {300, 500}, depth {3, 4, 5, 6, 8, 10, 12, none}, min leaf {5, 10, 25, 50, 100}, max features {√p, 0.3, 0.5, 1.0}, class weight {none, balanced, balanced_subsample}. HGB: learning rate log-uniform 0.01–0.3, rounds 100–600, leaves {7, 15, 31, 63}, depth {none, 3, 5, 8}, min leaf 10–100, L2 log-uniform 0.001–10, class weight {none, balanced} | – | Random search covers 7-dimensional spaces better than a grid at the same cost (Bergstra and Bengio, 2012) |
| P4 | HGB early stopping off | `early_stopping=False`; rounds tuned on the purged folds | – | Early stopping holds out a random 10% of fit rows, which puts neighbouring days of one week on both sides of the split (leakage) |
| P5 | Milestone 3 models reused, not retuned | LR and DT pipelines loaded from `models/*.joblib`; their OOF thresholds are recomputed and asserted equal to `m3_params.json`; their validation PR-AUC is asserted equal to `m3_metrics_validation.csv` | – | The comparison with the baselines must use exactly the Milestone 3 models |
| P6 | Final-model rule | Highest CV PR-AUC among the full-feature LR, DT, RF and HGB; models within 0.005 of the best count as tied; the simplest tied model wins (LR < DT < RF < HGB). Fixed before any validation metric | Result: LR full (CV PR-AUC 0.651) stays final; RF full 0.590, HGB full 0.565, DT full 0.519 | 0.005 is below the fold-to-fold SD (about 0.14), so a smaller difference is noise; simpler models are easier to explain to officials |
| P7 | Fairness metrics and reference groups | Positive prediction = alert. Selection rate, TPR, FPR per group; DIR against the reference group with the 80% rule read two-sided (0.8–1.25); equal-opportunity (ΔTPR), predictive-equality (ΔFPR), equalized-odds (max of both) and demographic-parity differences as max − min over groups. References: Pakistan, Tier 1 metros, Lahore. Audited on validation and on the OOF training predictions; 95% week-block bootstrap CIs; city level descriptive | – | An alert protects (fewer missed spikes) and costs (false alarms), so both too few and too many alerts can be unfair. Metros hold the most monitoring and administrative capacity |
| P8 | Mitigation | Target attribute: city-size tier. Pre-processing: Kamiran–Calders reweighing (weights from each CV fold's fit rows only). Post-processing: per-tier cost-optimal 5:1 thresholds; predictive-equality and equalized-odds thresholds (every tier's FPR, and TPR for equalized odds, within ±ε/2 of a common target; cheapest feasible thresholds on OOF). Headline ε = 0.05, fixed before results; Pareto sweep ε 0.01–0.20 and reweighing strength α 0–1 | – | All mitigation choices use OOF training predictions; validation only reports |
| P9 | Hypotheses H1, H3, H4 | OLS on `target_index_h1`, training rows, city-clustered SE (week-clustered check). Controls: months, cities, mean temperature, temperature range, humidity, rain total, vector wind. Spec A = Milestone 2 spec; spec B adds today's index. H4 on the 7 Pakistani cities | – | Promised in the Milestone 3 report; spec B separates association from forecast value |
