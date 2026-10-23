# Milestone 3 plan: baseline models, leakage-free CV, error-cost analysis

This plan is for the Claude Code agent on Bilal's Windows laptop, which starts with no prior context. Read
`context/latest_handoff.md` (project state after Milestone 2) and `context/milestone3.md` (brief and rubric)
before writing any code. The 7 rules in handoff section 6 still apply. The most important: **2024 is sealed**,
and **fit on `split == "train"` only**.

## Context
Milestone 2 is finished (`main` @ 67973e9). Milestone 3 asks for:
- a naive benchmark and at least 2 baseline ML models;
- stratified, leakage-free K-fold CV;
- hyperparameter tuning;
- Accuracy, Precision, Recall, Specificity, F1 and ROC-AUC;
- an asymmetric FP/FN cost analysis;
- confusion matrices and edge cases;
- feature importance, policy takeaways and a Milestone 4 roadmap.

Deliverables are an executed notebook, modular scripts and a report section appended to the 10-page Milestone 2
report. Rubric weights: models + CV 35, metrics + cost 30, drivers + insights 20, report + reproducibility 15.
Due Sunday 25 Oct 2026, 23:59. Keep the Milestone 3 part of the report to about 5–6 pages.

## Decisions already made with the user (do not reopen)
| # | Decision |
|---|---|
| D1 | Everything runs locally: Windows 11, global Python 3.14.6, 8 logical CPUs, 16 GB RAM, Node 24, MS Word. No Colab, no cloud. |
| D2 | Headline target `target_spike_h1`. `target_spike_h2/h3` get one compact table using the same tuned pipelines. |
| D3 | Keep the Milestone 2 spike label (city P90 of train Oct–Mar). Add one sensitivity run with a **month-wise** label: `target_index_h1 ≥` city×month P90, learned on train only, suspect days excluded. |
| D4 | Models: (1) majority class, (2) persistence (`persist_spike`; score = `persist_index`), (3) logistic regression, (4) decision tree. LR and DT are each fitted on 3 feature sets (D7). No KNN or RF; RF and GBM go to Milestone 4. |
| D5 | CV: **purged, repeated StratifiedGroupKFold**, k = 5 × 5 repeats (seeds 0–4) = 25 folds. Group = calendar week shared by all 11 cities, so the same week is never split between fit and score folds, and Islamabad and Rawalpindi always share a fold. Purge: drop from each fold's training part the rows dated within 3 days before a held-out week (their targets fall inside it). The chronological validation split (2023-09-04 → 2023-12-31) is the held-out test. Plain StratifiedKFold is **not** used; the report explains why (neighbouring days ρ = 0.82, same-day cross-city duplicates). |
| D6 | Cost FN:FP = **5:1** headline. Cost curve over ratios 1–20. Thresholds are chosen on out-of-fold (OOF) train predictions, never on validation. |
| D7 | Feature sets: **full**, **weather-only**, **full − fire** (ablation; tests whether fires add skill). |
| D8 | Only H2 enters Milestone 3: LR odds ratios with city-clustered SE, which also serve as the driver analysis. H1, H3 and H4 go to the Milestone 4 roadmap as named tests. |
| D9 | Report: unchanged Milestone 2 Sections 1–6 plus new Sections 7–12; References move to the end; footer "Milestone 03". Output in `submission/milestone3/`. |
| D10 | Single branch: the cloud session already pushed the plan files to `main` and deleted all other remote branches. Laptop work is committed straight to `main`, one commit per phase. |
| D11 | No file moves or tidy-up beyond branches. |
| D12 | Rows whose feature day **or** target day (t + h) is a `suspect_day` are excluded from fitting and CV scoring. Report the count. Validation has none. |
| D13 | **Commits:** author `bilal <bilelayub@gmail.com>` (the laptop's git config). **No** `Co-Authored-By`, `Claude-Session` or "Generated with" lines in any commit message. |

## Phase 0: setup (PowerShell, repo root)
```powershell
Remove-Item context\latest_handoff.md     # untracked local copy; the same file is now on main
git pull origin main
git branch -a                              # expect only main and origin/main
git fetch --prune
git config user.name; git config user.email   # expect: bilal / bilelayub@gmail.com
```
- In Claude Code settings (`~/.claude/settings.json`), turn off commit attribution:
  `"attribution": {"commit": "", "pr": ""}`. On older versions use `"includeCoAuthoredBy": false`.
- Add to `requirements.txt`: `scikit-learn>=1.5`, `statsmodels>=0.14.5`, `joblib`.
- Run `python -m pip install -r requirements.txt`, then `python -m pip install docx2pdf` (PDF export through
  Word; Windows-only helper, so leave it out of requirements.txt).
- Run `npm install docx` if `node_modules` is missing.
- Sanity check: `python -c "import sklearn, statsmodels, pyarrow; print(sklearn.__version__)"`.

## Phase 1: `src/modeling.py` (new)
This module holds data access, feature sets, the CV splitter, pipelines, tuning, OOF prediction and threshold
selection. Follow the style of `src/merge.py` and `src/eda.py`: short docstrings, plain functions, settings
imported from `src/config.py`.
- `load_model_frame(horizon=1)`:
  - read `Dataset/clean/master_daily.parquet` with pathlib;
  - assert that no date is ≥ 2024-01-01;
  - add `suspect_target` = `suspect_day` shifted by −h **within city**;
  - drop rows with NaN target or features, and rows with `suspect_day | suspect_target` (D12);
  - return the frame and a log of the dropped counts per split.
- `FEATURE_SETS` (verify every name exists in the master; assert it):
  - `AQ_HISTORY = [persist_index, index_lag1, index_lag2]`
  - `FIRE = [fire_cnt_up45_r300_all, fire_cnt_up45_r300_all_lag1, _lag2, _lag3]` (raw counts; log1p is applied
    inside the pipeline)
  - `WEATHER = [stagnant, stagnant_lag1, rh_mean_pct, rain_day, temp_range_c, vec_len_kmh, temp_mean_c,
    wind_from_n … wind_from_nw]`. Leave out `wind_speed_mean_kmh` (ρ 0.85 with `vec_len_kmh`) and temp min/max
    (r 0.91–0.98).
  - `CALENDAR_PLACE = month_02..month_12 + city_* dummies` (references: January, Lahore)
  - `full = AQ_HISTORY + FIRE + WEATHER + CALENDAR_PLACE`
  - `weather_only = WEATHER + CALENDAR_PLACE`
  - `no_fire = full − FIRE`
- `week_groups(dates)`: `(date − WINDOW_START).days // 7`.
- `purged_sgkf_splits(df, y, n_splits=5, seeds=range(5), horizon=1)`: returns a list of (train_idx, test_idx)
  from `StratifiedGroupKFold(shuffle=True, random_state=seed)`, purged as in D5. Assert that the train and test
  groups are disjoint in every fold.
- Pipelines, with every transform inside the pipeline so scaling is learned within each fold:
  - `make_lr(features)`: `ColumnTransformer` (log1p on FIRE + StandardScaler on continuous; binary columns
    passthrough) → `LogisticRegression(solver="saga", max_iter=5000)`.
  - `make_tree(features)`: log1p on FIRE, no scaling → `DecisionTreeClassifier(random_state=42)`.
- Grids:
  - LR: `C ∈ logspace(-3, 2, 8)`, `l1_ratio ∈ {0, 1}` (sklearn ≥ 1.8 deprecates `penalty`; if the installed
    version still needs it, use `penalty ∈ {l1, l2}`), `class_weight ∈ {None, "balanced"}`.
  - DT: `max_depth ∈ 2..8`, `min_samples_leaf ∈ {10, 25, 50, 100}`, `class_weight ∈ {None, "balanced"}`.
- `tune(pipe, grid, X, y, splits)`: `GridSearchCV(scoring="average_precision", cv=splits, n_jobs=-1, refit=True)`.
  The tuning metric is **PR-AUC**, because spikes are rare (about 5%).
- `oof_predict(best_estimator, X, y, splits)`: averages each row's out-of-fold probability across the 5 repeats.
- `choose_threshold(y, p, cost_fn=5, cost_fp=1)`: the threshold that minimises `cost_fn·FN + cost_fp·FP` on OOF
  predictions.
- Naive models: `DummyClassifier("most_frequent")` and persistence (prediction = `persist_spike`,
  score = `persist_index`).

## Phase 2: `src/evaluate.py` (new)
- `binary_metrics(y, p, threshold)`: accuracy, precision, recall, **specificity**, F1, ROC-AUC, PR-AUC, Brier,
  TP/FP/TN/FN, and expected cost per 1,000 city-days at 5:1. Guard the AUCs when a model returns a constant
  prediction (the Dummy).
- `cv_metrics(...)`: mean ± SD over the 25 folds. Each fold uses the OOF-chosen threshold; the report notes this
  is slightly optimistic.
- `block_bootstrap(df, fn, n=1000, seed=42)`: resample whole weeks of validation and return 95% CIs. Also use it
  for paired differences: full vs no-fire ΔPR-AUC, and each model vs persistence.
- `cost_curve(y_oof, p_oof, y_val, p_val, ratios=range(1, 21))`: re-optimise the threshold per ratio on OOF and
  report the validation cost for each ratio. Include the "never alert" and "always alert" reference lines.
- `error_breakdown(df, y, yhat)`: splits FN and FP into **onset** days (target spike while `persist_spike == 0`)
  and **continuation** days, and breaks them down by city and by month. Also list the top-10 FNs by
  `target_index_h1` and the top-10 FPs by score.
- Every table goes through `round(4)` and is written to `docs/tables/m3_*.csv`.

## Phase 3: `modeling.ipynb` (new; reads only `master_daily.parquet` and `role2_params.json`)
Start the notebook like `merge_analysis.ipynb`: put the repo root on `sys.path` and call `plotting.set_style()`.
Use Markdown cells that explain each step.

| Section | Content | Main outputs |
|---|---|---|
| M3.1 Data and leakage guards | Load, apply D12 drops, show class balance per split (stratification check: spike rate in train vs validation), assert that no validation or 2024 row reaches any `fit` | `m3_split_balance.csv` |
| M3.2 CV design | Build the 25 purged folds; show the per-fold spike rate and group disjointness | `m3_cv_folds.csv`, `fig_m3_1_cv_folds.png` |
| M3.3 Baselines + tuning | Dummy and persistence; GridSearch for LR and DT × 3 feature sets; plot the tuning curve (PR-AUC vs C, PR-AUC vs depth) with fold SD | `m3_tuning_lr.csv`, `m3_tuning_dt.csv`, `fig_m3_2_tuning.png`, `Dataset/clean/m3_params.json` (best params + thresholds) |
| M3.4 Metrics | CV mean ± SD and validation point estimates with bootstrap CIs, all 8 models | `m3_metrics_cv.csv`, `m3_metrics_validation.csv`, `fig_m3_3_roc_pr.png` |
| M3.5 Fire ablation | Full − no-fire ΔPR-AUC and ΔROC-AUC, bootstrap CI (the core project question) | `m3_fire_ablation.csv` |
| M3.6 Error cost | Qualitative FP/FN consequence table; expected cost at 5:1; cost curve 1–20; break-even ratio vs never/always alert | `m3_cost.csv`, `fig_m3_4_cost_curve.png` |
| M3.7 Confusion matrices + edge cases | 2×2 grids for persistence, LR-full and DT-full on validation (cividis, counts and %); onset vs continuation; by city and month; top FN/FP lists | `m3_confusion.csv`, `m3_errors_onset.csv`, `m3_errors_city_month.csv`, `fig_m3_5_confusion.png` |
| M3.8 Drivers | LR standardised coefficients and odds ratios per 1 SD; H2 via `statsmodels` Logit on train (city-clustered SE, week-clustered as a check; only 11 clusters, so note it); DT Gini importance; permutation importance (PR-AUC) on validation for both models; small tree plot (depth ≤ 3) | `m3_odds_ratios.csv`, `m3_h2_logit.csv`, `m3_importance.csv`, `fig_m3_6_drivers.png`, `fig_m3_7_tree.png` |
| M3.9 Sensitivity | Month-wise label (D3); h2/h3 metrics table (D2) | `m3_label_monthwise.csv`, `m3_horizons.csv` |
| M3.10 Artifacts | `joblib.dump` the best pipelines to `models/*.joblib`; print the package versions | `models/` |

Figure rules from Milestone 2 apply: a title, axes with units, a legend, the Okabe-Ito palette from
`src/plotting.py` (fixed model colours), and `plotting.save()` at 300 dpi. The OOF thresholds are fixed **before**
any validation metric is computed; state this in a Markdown cell.

## Phase 4: `DECISIONS.md` section M3
List D3–D13 with exact row counts (dropped suspect rows, rows per split after drops, chosen hyperparameters and
thresholds), in the same style as sections F, A, W and M.

## Phase 5: manuscript (Sections 7–12, about 5–6 pages)
- `docs/manuscript/build_manuscript.py`:
  - keep Sections 1–6 unchanged;
  - add one sentence to the abstract;
  - insert the new sections before the existing `h2("References")`, which moves to the end;
  - read only `docs/tables/m3_*.csv`, so every number matches the notebook;
  - add references (sklearn; Roberts et al. 2017 on blocked CV for structured data; Saito & Rehmsmeier 2015 on
    PR-AUC). The cloud session wrote these from memory, so check each one.
- New sections:
  - **7 Baseline Models and Justification.** Why majority, persistence, LR (interpretable odds ratios for policy,
    calibrated probabilities) and a shallow DT (non-linear "trap" rules such as stagnant ∧ humid, readable by
    officials).
  - **8 Experimental Setup.** Chronological split (train 2022-08-04 → 2023-08-31, 3-day gap, validation to
    2023-12-31, about 77/23), purged grouped CV, leakage guards, tuning grids, threshold rule.
  - **9 Results.** Metrics table, ROC/PR figure, fire ablation.
  - **10 Asymmetric Error Cost Analysis.** FN = missed health advisory (exposure of children, the elderly and
    asthma patients); FP = needless school or kiln closures and alert fatigue. Cost at 5:1, cost curve,
    confusion matrices, onset vs continuation.
  - **11 Drivers and Initial Policy Takeaways.** Pakistan first, then cross-border. Write the policy points only
    once the Phase 3 numbers are in.
  - **12 Limitations and Milestone 4 Roadmap.** Underfitting vs persistence, class imbalance, one training winter,
    Islamabad/Rawalpindi duplicate series, the label-timing artefact, city/country bias. Milestone 4 work: RF/GBM,
    calibration, a fairness audit across cities and countries (error rates by city, PK vs IN), and H1/H3/H4 tests.
- Update Section 6 (Reproducibility) with `modeling.ipynb`, `src/modeling.py`, `src/evaluate.py` and `models/`.
- `docs/manuscript/render_docx.js`: take an optional CLI argument for the milestone (default 2, so Milestone 2
  rebuilds stay identical). With `3` it writes `submission/milestone3/Milestone3_Report.docx` and the footer
  reads "Milestone 03".
- PDF: `python -c "from docx2pdf import convert; convert('submission/milestone3/Milestone3_Report.docx')"`.
  Fallback: Word → Save As PDF.
- `submission/milestone3/`: report .docx and .pdf, executed `modeling.ipynb` copy, `README.md` (how to run,
  file map).

## Commits (one per phase, straight to `main`, author bilal, no trailers)
1. "Milestone 3 setup: modelling dependencies"
2. "Add modelling and evaluation modules"
3. "Milestone 3 modelling notebook with results, tables and figures"
4. "Decision log: Milestone 3 modelling choices"
5. "Milestone 3 report sections and submission package"

Push with `git push origin main` after each commit. If you re-run older notebooks by accident,
`git checkout` the regenerated parquet and PNG files.

## Verification
- `jupyter nbconvert --to notebook --execute --inplace modeling.ipynb` from the repo root finishes without error
  in under about 10 minutes.
- Run it a second time: the `docs/tables/m3_*.csv` files are byte-identical (all seeds fixed).
- Notebook asserts pass: no 2024 dates; every fit uses train rows only; CV groups are disjoint and purged; the
  feature names exist.
- Persistence validation metrics match a hand count from `persist_spike` vs `target_spike_h1`.
- `python docs/manuscript/build_manuscript.py`, then `node docs/manuscript/render_docx.js 3`, builds the report.
  Running `render_docx.js` with no argument still builds the Milestone 2 report.
- Spot-check 5 numbers in the PDF against the CSVs. Open the PDF and check that the figures render and the total
  is about 16 pages.
- `git log -5 --format='%an <%ae>%n%b'` shows bilal and no Co-Authored-By lines. `git branch -a` shows only main.

## What the cloud session does after approval
1. Copy this plan to `context/milestone3_plan.md`, the brief to `context/milestone3.md` and the handoff to
   `context/latest_handoff.md`.
2. Commit to `main` as `bilal <bilelayub@gmail.com>` with no trailers, and push.
3. Delete the remote branches `claude/blissful-archimedes-2nlkzn`, `claude/keen-cannon-mv7k42`,
   `claude/wonderful-cori-4rdox0`, `feature/fire-stream`, `milestone2-submission` and
   `claude/admiring-lamport-hdyyiw`. All are verified to have 0 commits that are not in `main`.
4. If the push to `main` or a branch delete is refused, report it. Phase 0 then covers it from the laptop with
   `git push origin --delete <branch>`.
