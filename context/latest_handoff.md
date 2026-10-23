# Handoff: Trans-Boundary Smog Prediction (Milestone 2 done → Milestone 3 next)

This document is for an AI coding agent (any vendor) picking up the project cold. It explains what the project is, what is finished, where everything lives, which decisions were made and why, and what is still open. Read it fully before touching the code.

Last updated: 2026-10-23. State of `main` at writing: commit `67973e9`.

---

## 1. Project in one paragraph

A university Data Science for Social Good project at Habib University. The team is Munir Tariq (10067), Ismail Nooruddin (09958) and Bilal Ayub (09716), all in Computer Science. The goal is to predict hazardous **smog spikes** in 11 cities of Punjab (7 in Pakistan, 4 in India) **1 to 3 days ahead**. The predictors are:
- **upwind crop fires** from NASA VIIRS satellite detections, split by country of origin to test the cross-border claim;
- **weather "traps"**: stagnant wind, humidity, no rain and clear-night inversions.

The target is a **Composite Smog Index** built from six pollutants, plus a per-city spike label. The project is aligned with SDG 3.9, 11.6 and 13. The course runs in milestones:
- Milestone 1: proposal (done).
- **Milestone 2: data preparation, EDA and hypotheses (done).**
- Milestone 3: modelling and hypothesis tests (next).
- Week 14: out-of-time test on 2024 data.

---

## 2. Repository and git state

- GitHub: `IsmailNooruddin/Smog-Analysis-DSSG` (private).
- **`main` is the source of truth** at `67973e9`. Its last four commits came from a second AI session that did review fixes and built the submission package; they sit on top of the Role 2 work.
- Other remote branches:
  - `claude/wonderful-cori-4rdox0` stops at `1071958`, which is behind `main`.
  - `milestone2-submission`, `claude/blissful-archimedes-2nlkzn`, `claude/keen-cannon-mv7k42` and `feature/fire-stream` come from earlier or parallel work.
  - Treat all of these as historical. Branch off `main` for new work.
- Commit history worth reading, oldest first:
  1. `5306bfe`: Role 1 hand-over fixes (AQ outputs to `Dataset/clean`, notebooks rerun, requirements fixed).
  2. `986d7d0`: Role 2 merge plus analysis (`merge_analysis.ipynb`, `src/merge.py`, `src/eda.py`, `src/plotting.py`).
  3. `1071958`: combined manuscript, weather report fixes, decision log.
  4. `dd2db4e`, `631c3b6`: review fixes (4-decimal tables, collinearity fix in the hypothesis controls, threshold consistency).
  5. `70faa64`: Excel export cell, `submission/` folder.
  6. `67973e9`: report rewritten to 10 pages in the weather-report style.

---

## 3. Where everything is

```
air_quality.ipynb      Role 1, Person A (Ismail): AQ cleaning, Composite Smog Index, spike label
weather.ipynb          Role 1, Person B (Munir): weather, vector-mean wind, stagnation flag
fire.ipynb             Role 1, Person C (Bilal): VIIRS filtering, Haversine/bearing, wind cones
merge_analysis.ipynb   Role 2: Part 2A merge → master table; Part 2B analysis; hypotheses; Excel export (83 cells, runs clean)
src/config.py          ALL shared settings: cities, file names, coordinates, window and split dates, city groups
src/merge.py           Merge functions; every one takes a date window (build_master(), add_fire_setting(), add_log_z(), data_dictionary(), …)
src/eda.py             summary_table, outlier_audit (both rules + masking + SD inflation), spearman_by_city, rate_by_condition (Wilson CI), contingency (χ², OR)
src/plotting.py        One figure style: Okabe-Ito palette (CVD-validated order), cividis / RdBu_r, save() at 300 dpi
Dataset/<Country>/…    Raw files (Air Quality, NASA, Weather). 2024 files exist but are SEALED.
Dataset/clean/         Role 1 outputs + master_daily.parquet, master_data_dictionary.csv,
                       aq_params.json, weather_zscore_params.json, fire_zscore_params.json, role2_params.json,
                       Milestone2_Final_Master_and_EDA.xlsx (65 sheets)
figures/               fig_a* (AQ), fig_b* (weather), fig_fire_* (fire), fig_m1..m6 (merged)
docs/tables/*.csv      Every table quoted in the report, written by merge_analysis.ipynb at 4 decimals
docs/manuscript/       build_manuscript.py (CSV → JSON) + render_docx.js (JSON → .docx, needs `npm install docx`)
submission/            The hand-in package: Milestone2_Report.docx (10 pages), executed merge_analysis.ipynb,
                       the Excel workbook, README.md
DECISIONS.md           Every data removal or change, with exact row counts (sections F, A, W, M)
context/milestone2.md  The Milestone 2 brief and grading rubric (35/35/15/15)
context/Final Proposal.md, context/milestone1.md   Earlier milestones
Report_Weather.docx, Milestone_2_Report_-_Air_Quality_Condensed.docx, "Milestone 2 Report - Fire.docx"   Role 1 stream reports
Milestone2_Manuscript_Draft.docx   Longer 16-page draft, superseded by submission/Milestone2_Report.docx
```

The original work plan (`Milestone2_Work_Plan.docx`, Roles 1 and 2 per person) was uploaded by the user and **is not in the repo**. Sections 6 and 7 below capture everything that mattered from it.

---

## 4. How to run

```bash
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt          # UTF-8, cross-platform; pandas 3, pyarrow, scipy, seaborn, jupyter, python-docx
# from the repository root, in this order:
jupyter nbconvert --to notebook --execute --inplace air_quality.ipynb
jupyter nbconvert --to notebook --execute --inplace weather.ipynb
jupyter nbconvert --to notebook --execute --inplace fire.ipynb
jupyter nbconvert --to notebook --execute --inplace merge_analysis.ipynb
# optional: rebuild the report
python docs/manuscript/build_manuscript.py && node docs/manuscript/render_docx.js
```

- A clean clone ran all four notebooks top to bottom without error and rebuilt an identical `master_daily.parquet`. The environment was Python 3.13, pandas 3.0.
- **Always run from the repo root.** The notebooks use relative paths, and `merge_analysis.ipynb` puts the root on `sys.path` so it can import `src`.
- Re-running regenerates parquet files and PNGs with identical data but different bytes. If you didn't mean to change them, `git checkout` them to keep diffs clean.
- `Dataset/Exported_AQ/` and `Dataset/Exported_Fire/` are gitignored scratch outputs. Only `Dataset/clean/` is committed.

---

## 5. The data pipeline (what each stage produces)

| Stage | Input → output | Key facts |
|---|---|---|
| AQ (A) | 11 Open-Meteo files, 453,192 hourly rows → `aq_daily.parquet` 5,665 × 55 | Values are **CAMS model output**, not monitors. No data before 2022-08-04 in any city (block dropped, not imputed). Index = 0.40·z(PM2.5) + 0.12·[z(PM10)+z(NO2)+z(SO2)+z(O3)+z(CO)], with log1p first on columns whose skew is above 1. Spike = index ≥ city's P90 of training Oct–Mar days. Thresholds range from 0.36 (Rahim Yar Khan) to 2.18 (Lahore), saved in `aq_params.json`. 297 spikes in the window; 208 in training. |
| Weather (B) | 11 files, 433,728 hourly → `wx_daily.parquet` 7,852 × 40 | No missing values. Wind is averaged as U/V vectors. `stagnant` = vector-mean wind < 2 km/h. `rain_day` = rain ≥ 1 mm. Files start 12–30 Jan 2022. No surface pressure. |
| Fire (C) | 4 VIIRS files, 1,284,773 detections → `fire_daily.parquet` 8,030 × 60 (wide) and `fire_daily_long.parquet` 602,250 rows | Filters: study box, type 0, confidence n/h, giving 238,756 detections. Counts and FRP are computed per city × radius (50–300 km) × cone (up30/45/60, none, down45 placebo) × origin (IN/PK/ALL). Days with no fires are 0, never NaN. |
| Merge (Role 2) | → `master_daily.parquet` **5,665 rows × 287 cols** | Spine is 11 cities × 515 days (2022-08-04 to 2023-12-31). Three one-to-one left joins, each asserted to keep 5,665 rows. Lags 1–3 per city. Targets `target_index_h{1,2,3}` and `target_spike_h{1,2,3}`. Baselines `persist_index`/`persist_spike` and `index_lag1..3`. Dummies. `split` = train 4,323 / skip 33 / validation 1,309. Only 9 columns have NaN: the targets near 2024-01-01 and the index lags at the window start. |

The full column reference, with meaning, unit, source and owner for each column, is `Dataset/clean/master_data_dictionary.csv`.

---

## 6. Rules that must not be broken

1. **2024 is sealed.** Never read the 2024 files in Milestone 2 or 3 analysis. `src/config.py` lists only 2022–2023 fire files on purpose.
2. **Fit on train only.** Scaling, thresholds, cut-offs and model/setting choices may use only `split == "train"` (2022-08-04 to 2023-08-31). Validation (2023-09-04 to 2023-12-31) is for reporting results. The 3-day skip equals the longest horizon.
3. **Time:** every stream added +5 h to GMT **before** taking the date (UTC+5 for Indian cities too; this is a known limitation).
4. **Keys:** `city`, `country`, `date`. City spellings come only from `src/config.py`.
5. **Lags and targets are always grouped by city.**
6. **Outliers are flagged, never deleted.**
7. **No fixed performance target** (the professor's instruction): find reasonable predictors, report the pattern, and compare against the **persistence** and **weather-only** baselines.

---

## 7. Decisions made, with reasons

All of these were agreed with the user. Many depart from the original work plan on purpose.

| Decision | Why |
|---|---|
| Window 2022-08-04 to 2023-12-31 for **all** streams (5,665-row spine, not the plan's 8,030) | AQ has no data before Aug 2022; the user chose to drop rather than carry empty rows. |
| Week 14 plan: retrain with 2024 H1 added, test on 2024 H2 | This is the user's plan to make up for the missing early 2022. It is implemented by changing the dates in `src/config.py` and rerunning. |
| Headline statistics use the **training harvest season (Oct–Dec 2022)**, with the full training year as secondary and the downwind ±45° cone as a **placebo** | Fires and smog share a seasonal cycle. Full-year correlations are inflated, and even the placebo reaches ρ ≈ 0.19 over the full year. |
| Default fire setting: **±45° upwind cone, 300 km** (plan said 150 km) | Best median Spearman ρ over the 7 Pakistani cities in training Oct–Dec: 0.23, against −0.06 for the plain 300 km circle and 0.01 for the placebo. The angle differences between 30°, 45° and 60° are within noise (SE ≈ 0.10). |
| Weather-trap proxy uses a **large** temperature range (plan said small) | 0 of 61 small-range harvest days preceded a spike, against 15.4% of large-range days. A large range marks clear nights with radiative inversions. |
| Trap cut-offs: humid = RH > 77.06% (train P75); large range > 13.6 °C (train P75) | Saved in `role2_params.json`. |
| Surface pressure dropped for Milestone 2 | Not in the exported files, and the cloud environment could not reach Open-Meteo. Listed as a limitation; could be added in Week 14. |
| Islamabad and Rawalpindi have **identical AQ** (same CAMS grid cell). Both are kept everywhere. | User decision. Stated as a limitation: there are 10 independent AQ series. |
| 44 `suspect_day` rows (13–16 Dec 2022, near-zero pollutants in all cities) are **kept as rows**. Thresholds and scaling are learned **without** them. | Removing them breaks the daily calendar that lags and targets need. Their effect is reported (index skew −1.15 with them, +0.26 without). DECISIONS.md M9. |
| H4 groups use Pakistani cities only: near = Lahore, Sialkot; intermediate = Faisalabad; far = Multan, Rahim Yar Khan, Islamabad, Rawalpindi | Only these can test India-origin smoke. Only Lahore, Sialkot and Faisalabad have ≥ 20 harvest days with India-origin fires in the cone. |
| Encoding references: Lahore (city), January (month), calm (wind sector) | `harvest_season` was **removed from the hypothesis controls** because it equals month_10 + month_11 + month_12 (collinear). |

---

## 8. Key findings so far (training period; tables in `docs/tables/`)

- **Cone vs circle:** see `cone_vs_radius.csv` and Figure M1. The upwind cone tracks next-day smog and the circle and placebo don't. The effect peaks **one day** after the fires (ρ ≈ 0.24 at lag 1, from `lagged_fire_correlation.csv`).
- **Weather traps** (`weather_trap_harvest.csv`):
  - after stagnant days, 27.3% of next days are spikes, against 9.4% after other days;
  - humid days: 22.0% against 8.5%;
  - rain days: 0 spikes;
  - stagnant + rain-free + humid together: 45% (9 of 20 days).
- **Timing problem:** spikes concentrate in **Dec–Jan**, but fires peak in **Oct–Nov**, and the May wheat-burning peak produced zero spikes. The spike label (P90 of Oct–Mar) therefore mostly captures fog-season episodes, so a null fire effect on the *label* could be an artefact of how the label is defined.
- **Persistence is strong:** today's index has ρ = 0.82 with tomorrow's, so any model must beat it.
- **Cross-border** (`cross_border.csv`): mixed. In Sialkot India-origin fires show ρ = 0.33 against 0.10 for Pakistan-origin; in Lahore it is −0.04 against 0.23. The far cities can't test the claim.
- **Index weights** (`weight_check_train.csv`): the index is robust (ρ ≥ 0.979 across versions). Dropping ozone changes the most labels.

---

## 9. Hypotheses for Milestone 3

Each hypothesis comes from `docs/tables/hypothesis_mapping.csv` and the notebook's "Hypotheses" section, where every column name is checked to exist in the master.

| ID (owner) | Y | Main X | Planned test |
|---|---|---|---|
| H1 cone vs radius (C) | `target_index_h1` | `fire_cnt_up45_r300_all_log1p_z` (+ lags) vs `fire_cnt_r300_all_log1p_z`; placebo `fire_cnt_down45_r300_all_log1p_z` | Nested OLS, city-clustered SE, partial F / ΔR² |
| H2 weather trap (B) | `target_spike_h1` | `stagnant`, `rh_mean_pct`, `rain_day`, `temp_range_c` | Logistic regression, odds ratios, clustered SE |
| H3 fire × stagnation (A) | `target_index_h1` | `fire_cnt_up45_r300_all_log1p_z × stagnant` | OLS interaction, one-sided |
| H4 cross-border (C) | `target_index_h1` (7 PK cities) | `fire_cnt_up45_r300_in_log1p_z` and its interaction with `near_border`; control `…_pk_log1p_z` | OLS, near vs far slope |
| H5 forecast value (A) | `target_spike_h1..h3`, `target_index_h1..h3` | all engineered features | Validation PR-AUC, ROC-AUC, Brier, MAE vs persistence and weather-only, block-bootstrap CIs; **no fixed target** |

Shared controls are `month_02..month_12`, the city dummies, and the weather columns not used as X. Consecutive days are autocorrelated, so use **city-clustered or block-bootstrap** standard errors, never plain ones.

---

## 10. Open items / suggested next steps

1. **Milestone 2 hand-in.** `submission/` is ready. Someone must export `submission/Milestone2_Report.docx` to PDF and check it reads well.
2. **Fact checks still needed before hand-in:**
   - The CAMS grid size (about 0.4°) quoted in the report was written from memory; confirm it in the Open-Meteo Air Quality API documentation.
   - The reference list was also written from memory; verify each entry (authors, years, volumes, DOIs).
3. **Milestone 3 (modelling).** Build it in a new notebook, e.g. `modeling.ipynb`, that reads only `Dataset/clean/master_daily.parquet` and `role2_params.json`.
   - Fit on `split == "train"`, report on `"validation"`.
   - Address the **label-timing issue**: model the continuous `target_index_h*` alongside the spike label, and consider a label with month-wise thresholds (learned on train only).
   - Rare positives: about 5% spikes, and the validation season has few. Use PR-AUC, recall and precision as well as ROC-AUC.
   - Don't enter near-duplicate predictors together: wind speed vs `vec_len_kmh` (ρ 0.85), and temp mean/min/max (r 0.91–0.98).
4. **Week 14:** change `WINDOW_START/END` and the split dates in `src/config.py`, add the 2024 files to `NASA_FILES`, and rerun all notebooks. The AQ and weather notebooks have their own date cuts, so check them too (AQ redefines `TRAIN_START/END` locally in its skewness cell).
5. **Optional:** add surface pressure if the team can export it from Open-Meteo (same coordinates as the weather file headers, GMT).

---

## 11. Known quirks and pitfalls

- The AQ notebook defines its own `TRAIN_START/END` and does not import `src/config.py`. Weather and fire do import it.
- The fire table's own `stagnant` column is dropped in the merge because it duplicates the weather one (verified identical).
- In the long fire table, cone counts are NaN for 178 Jan-2022 city-days with no wind. These fall outside the window, but `src/merge.py` asserts that no fire count is missing inside it.
- `pivot_table(dropna=False)` created phantom city×country rows once. `fire_setting_wide` uses `pivot` for that reason.
- Report tables are saved at **4 decimals** on purpose: rounding twice from 3 decimals rounded some values the wrong way.
- `Milestone2_Manuscript_Draft.docx` (16 pages) is the older long draft. The submitted report is `submission/Milestone2_Report.docx` (10 pages), built by the same `docs/manuscript` scripts.
- `requirements.txt` is now UTF-8. An older UTF-16 Windows freeze existed, so don't restore it.

---

## 12. Rubric reminder (`context/milestone2.md`)

| Criterion | Weight |
|---|---|
| Data preparation and structural readiness | 35% |
| EDA and visualisation | 35% |
| Hypotheses and analytical plan | 15% |
| Manuscript structure and code quality | 15% |

Every figure needs a title, a detailed caption, axes with units, a legend and a colourblind-safe palette (use `src/plotting.py`). Every number in the report must match notebook output: tables come from `docs/tables/*.csv`.
