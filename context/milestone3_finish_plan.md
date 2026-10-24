# Handoff: finish Milestone 3 (rubric fixes to the built work, then Phases 4–5)

This document is for an AI coding agent that starts a **new session with no context**. It is self-contained.
Execute it top to bottom.

File: `context/milestone3_finish_plan.md`. The decisions in section 2 were agreed with the user in a grilling
session, so do not reopen them.

Written 2026-10-25. **Deadline: Sunday 25 Oct 2026, 23:59 (today).** The order of steps follows the marks, so if
time runs short, Steps 1–3 matter more than Step 4.

---

## 0. Read first (in this order)
1. `context/latest_handoff.md`: the full project state after Phases 0–3. It covers the environment, file map,
   rules, decisions D1–D13 and X1–X8, every current result, the notebook map and the pitfalls. **Everything in it
   still holds unless this document overrides it.**
2. `context/milestone3.md`: the brief and rubric (Models + CV 35, Metrics + cost 30, Drivers + insights 20,
   Report + reproducibility 15).
3. `context/milestone3_plan.md`: the original agreed plan (Phases 0–5).
4. This document: what changed after a rubric audit, and exactly what to do.

**Hard rules (from latest_handoff §6; do not break them):**
- 2024 is sealed.
- Fit on `split == "train"` only. Validation is used only for reporting.
- Lags and targets are grouped by city.
- Outliers are never deleted.
- No file moves or renames.
- Commits are straight to `main` as `bilal <bilelayub@gmail.com>`, with **no** `Co-Authored-By`, `Claude-Session`
  or "Generated with" lines. Push with `git push origin main` after each commit.
- Windows 11, global Python 3.14.6, run from the repo root, `PYTHONIOENCODING=utf-8` when printing notebook text.

**State at writing:** `main` @ `018bfcd`, working tree clean.

---

## 1. Rubric audit of the built work (Phases 0–3), and the verdict

Every rubric line has code behind it, and the CV design, cost analysis and edge-case work are strong. These risks
would cost marks:

| # | Risk | Rubric line affected | Fix agreed (section 2) |
|---|---|---|---|
| R1 | The outer split is chronological, **not stratified**; the brief literally says "apply stratified sampling" | Models + CV (35) | Q1 leakage check |
| R2 | "Potential demographic bias" appears only as a roadmap phrase, with no evidence | Insights + roadmap (20) | Q2 group error rates |
| R3 | The M3.6 Markdown justifies FN:FP = 5:1 as "a conservative view of the health literature", with **no citation** | Asymmetric cost (30) | Q3 sourced framing |
| R4 | The LR city odds ratios look absurd (Rahim Yar Khan 9,004 vs Lahore; Islamabad 3,721). They are a threshold correction (one pooled index, a threshold per city, 0.36 to 2.18), not a risk ranking | Drivers (20) | Q4 margin features |
| R5 | The Milestone 2 report (§4 Analytical plan; H5 says "ΔMAE ≥ 0") promised that "Milestone 3 will also report results for the continuous index". Nothing models the index yet | Consistency, Metrics (30) | Q7 Ridge check |
| R6 | The report §7–12, the PDF and the submission package don't exist | Report (15) and the written half of the other 85 | Steps 3–4 |

**Checked and fine (no change, state it in the report):**
- The LR best `C = 100` is the top of the grid, but the curve has flattened. LR full: C = 19.31 → 0.6041, C = 100
  → 0.6048 CV PR-AUC. LR no-fire: 0.6109 → 0.6109.
- The DT plateaus after depth 6.
- Accuracy, precision, recall, specificity, F1 and ROC-AUC are all in `m3_metrics_validation.csv` and
  `m3_metrics_cv.csv`.

Current LR-full validation errors per city (from `m3_errors_city_month.csv`; spikes / FN / FP):

| City | Spikes | FN | FP |
|---|---|---|---|
| Amritsar | 5 | 2 | 6 |
| Faisalabad | 11 | 4 | 15 |
| Ferozepur | 13 | 3 | 18 |
| Islamabad | 0 | 0 | 2 |
| Jalandhar | 12 | 0 | 8 |
| Lahore | 1 | 0 | 5 |
| Ludhiana | 10 | 0 | 7 |
| Multan | 10 | 2 | 12 |
| Rahim Yar Khan | 22 | 4 | 11 |
| Rawalpindi | 0 | 0 | 2 |
| Sialkot | 5 | 0 | 6 |

That gives PK recall 39/49 = 80% and IN recall 35/40 = 88%. FP: PK 53 over 7 cities, IN 39 over 4 cities. These
numbers **will change** after Q4; recompute them.

The Milestone 2 report got full marks, so its Sections 1–6 stay as they are (Q5).

---

## 2. Decisions agreed with the user (do not reopen)

| # | Decision | Detail |
|---|---|---|
| Q1 | **Leakage check** | New cell in M3.3, after the thresholds cell. It uses **training rows only** (rule 2 stays strict) and the tuned best estimators of **LR full and DT full**. It scores the same pipeline four ways (PR-AUC and ROC-AUC, mean ± SD where there are folds): (a) one random **stratified 80/20** split of the training rows (`train_test_split(stratify=y, random_state=42)`); (b) plain `StratifiedKFold(5, shuffle=True, random_state=0)`; (c) `StratifiedGroupKFold(5)` by week **without** purge or embargo (seed 0); (d) our purged and embargoed 25 folds (already in `cv_folds`). Reference row: the chronological validation score. Output: `docs/tables/m3_leakage_check.csv`. The report (§8) uses it to show **numerically** why a random stratified split overstates skill. Report the result honestly even if the inflation is small. |
| Q2 | **Group error rates** | New cell in M3.7, for persistence and LR full on validation. Per **country** (PK/IN): spikes, alerts, recall, FPR, precision, with 95% week-block bootstrap CIs via `EV.block_bootstrap`. Per **city**: the same, as point estimates. Output: `docs/tables/m3_error_rates_group.csv`, long format with columns `model, level (country/city), group, metric, estimate, ci_low, ci_high`. The report calls it a *preliminary disparity check*; the full fairness audit is Milestone 4. |
| Q3 | **Cost-ratio framing + a quantitative source** | 5:1 is a stated policy assumption, not an estimate. The robust result is the break-even ratio on the cost curve. **Web-search for a verified quantitative source** (South Asia / Pakistan / India preferred) that values a high-pollution day's health cost (hospital admissions, mortality, VSL-based daily cost, or an economic-cost study of smog days) against the cost of a school closure or a day of lost activity. Cite only what you have opened and verified (author, year, venue, the figure). If nothing fits cleanly, cite the closest verified source for the health burden and say the ratio is an assumption. Remove "a conservative view of the health literature" from the M3.6 notebook Markdown. WHO 2021 is already in the references. |
| Q4 | **Threshold-margin AQ history is the headline** | Replace the raw-index AQ-history columns with margins over the city spike threshold: `persist_margin = persist_index − spike_threshold`, `margin_lag1 = index_lag1 − spike_threshold`, `margin_lag2 = index_lag2 − spike_threshold`. **Fixed in advance:** the margin version is the headline whatever it scores (we are not picking features on results). Reasons: the label is defined relative to each city's threshold; the persistence score already uses the margin (departure X4); thresholds are learned on train only in Milestone 2, so this adds no new leakage beyond what the label itself already has (note in DECISIONS that the thresholds come from all training rows, so CV folds share them, just as they share the label). The **raw-index version is retuned and kept as a sensitivity run** (M3.9c), so the old numbers stay reproducible and the city-OR fix can be shown. |
| Q5 | Milestone 2 Sections 1–6 unchanged | Only the title/subtitle, one abstract sentence, one closing line in §4 (where H2 and H5 are now answered; H1, H3, H4 → Milestone 4) and §6 Reproducibility change, and **only in the Milestone 3 build**. |
| Q6 | **Self-contained package** | `submission/milestone3/` mirrors the repo layout, so the notebook runs from that folder (all paths are relative to the working directory: `Path.cwd()`, `Dataset/clean`, `docs/tables`, `figures`). Contents: `Milestone3_Report.docx`, `Milestone3_Report.pdf`, `modeling.ipynb` (the executed copy), `src/config.py`, `src/plotting.py`, `src/modeling.py`, `src/evaluate.py` (`src` has no `__init__.py`; it works as a namespace package, so don't add one), `models/*.joblib`, `Dataset/clean/master_daily.parquet` (3.9 MB), `Dataset/clean/role2_params.json`, `Dataset/clean/m3_params.json`, `requirements.txt`, `README.md`. |
| Q7 | **Index regression check (Ridge)** | New M3.9d. `Ridge` on `target_index_h1` for full, no-fire and weather-only, using the same preprocessing as the LR. Alpha is tuned on the same purged folds with `scoring="neg_mean_absolute_error"`. Report CV and validation MAE, RMSE and R² against persistence (prediction = `persist_index`), plus paired week-block bootstrap ΔMAE for full − no-fire and for each model − persistence. Output: `docs/tables/m3_index_regression.csv`. A continuous target is a more sensitive test of the fire effect than the binary label, so report whether fire helps here. |
| Q8 | **Policy tied to real institutions** | In §11, map each takeaway to existing mechanisms: **Punjab EPD** (Environment Protection Department, Pakistan) smog advisories, smog emergency and school-closure orders; **CAQM GRAP** (Commission for Air Quality Management, Graded Response Action Plan, India). Verify each by web search before citing (official page or reliable news), and add 2–3 references. |

---

## 3. Step 1: revise the modules and notebook
**Commit:** "Milestone 3 revisions: threshold-margin features, leakage check, group error rates, index regression"

### 3.1 `src/modeling.py` (currently 242 lines; keep its style: short docstrings, section banners, plain functions)
- **Feature lists:**
  - `AQ_HISTORY = ["persist_margin", "margin_lag1", "margin_lag2"]`. Comment: margin over the city spike threshold;
    this removes the city-dummy threshold correction.
  - `AQ_HISTORY_RAW = ["persist_index", "index_lag1", "index_lag2"]` (the Phase 3 encoding, kept for sensitivity).
  - `FULL_RAW = AQ_HISTORY_RAW + FIRE + WEATHER + CALENDAR_PLACE`. Keep it **outside** `FEATURE_SETS`, so the
    notebook's `SETS` loop and the `MODELS` list stay at 3 sets.
  - `CONTINUOUS = AQ_HISTORY + AQ_HISTORY_RAW + ["rh_mean_pct", "temp_range_c", "vec_len_kmh", "temp_mean_c"]`.
    `make_lr`/`make_tree` pick columns by membership, so both encodings work.
  - The `MAX_AQ_LAG = 2` embargo is unchanged (the margins come from the same days).
- **`load_model_frame()`:**
  - before the drop steps, add the three margin columns from `spike_threshold` (a master column, already used by
    `persistence()`);
  - the missing-feature check covers `FEATURE_SETS["full"] + AQ_HISTORY_RAW + ["spike_threshold"]`;
  - cast the margins to float with the other features;
  - assert `((out.persist_margin >= 0).astype(int) == out.persist_spike).all()`.
- **Ridge:** `make_ridge(features)` has the same `ColumnTransformer` as `make_lr`, then
  `Ridge(random_state=42)` (or no random_state; Ridge is deterministic with the default solver).
  Factor the shared preprocessing into a small `_lr_prep(features)` helper used by both.
  `RIDGE_GRID = {"model__alpha": np.logspace(-2, 3, 11)}`.
- **`tune(pipe, grid, X, y, splits, n_jobs=-1, scoring="average_precision")`:** add the `scoring` argument.
- **`oof_predict`** calls `predict_proba`. For Ridge, add a `method="predict_proba"` argument (or a small
  `oof_regress`) that uses `predict`.

### 3.2 `src/evaluate.py`
- `group_error_rates(y, yhat)` returns a dict: spikes, alerts, recall, fpr, precision (NaN-safe with the existing
  `div` pattern). Use it inside a `block_bootstrap` fn per country, and with `groupby` per city.
- `regression_metrics(y, yhat)` returns a dict: mae, rmse, r2.

### 3.3 `modeling.ipynb` (46 cells, indices 0–45)
Edit it with NotebookEdit; Read the notebook first to get the cell ids. A text dump of all cell sources can be
made with:
`python -c "import json;nb=json.load(open('modeling.ipynb',encoding='utf-8'));[print(i,c['cell_type'],''.join(c['source'])[:80]) for i,c in enumerate(nb['cells'])]"`

Current cell map:
- 0 header table
- 1 setup
- 2–5 M3.1
- 6–9 M3.2
- 10–15 M3.3 (11 tuning, 12 fig 2, 14 OOF/thresholds/params, 15 findings)
- 16–19 M3.4
- 20–22 M3.5
- 23–26 M3.6
- 27–30 M3.7 (28 confusion + breakdown, 30 top errors/fn_context)
- 31–38 M3.8 (32 odds ratios, 33 H2 Logit, 35 permutation, 37 fig 6, 38 tree)
- 39–43 M3.9 (40 month-wise, 42 horizons)
- 44–45 M3.10

**Edits:**
1. **Cell 0:** add the new subsections to the section table (leakage check in M3.3; group error rates in M3.7;
   M3.9c AQ encoding; M3.9d index regression).
2. **Cells 2 and 10:** explain the margin encoding of AQ history (why it is used, and that the raw version is in
   M3.9c).
3. **After cell 14:** insert Markdown "Leakage check: why not a random stratified split" plus a code cell (Q1)
   that writes `m3_leakage_check.csv`. Call `assert_train_only(train)` before the fits. Clone `searches[m].best_estimator_`.
4. **Cell 23 (M3.6 Markdown):** reword with the Q3 framing and the citation. Remove the uncited phrase. Also fix
   the phrase in cell 25 ("which is a conservative view of the health literature").
5. **After cell 30:** insert the Q2 group error-rate code cell and its findings Markdown.
6. **Cell 36 and others:** remove or replace the text about the city-OR artefact. After Q4 the city ORs should be
   modest; report what they actually are. Also update cell 32 if needed.
7. **After cell 43:** insert M3.9c (Markdown plus code): retune LR and DT on `MD.FULL_RAW` with `MD.tune` on the
   same `splits`, then compute OOF thresholds and validation metrics. Write `m3_aq_encoding.csv`: rows = encoding
   (margin headline / raw index) × model (LR full, DT full); columns = best params, CV PR-AUC, validation PR-AUC,
   ROC-AUC, recall, precision, cost at 5:1, and max |city OR| for LR. Then add M3.9d (Markdown plus code): the Q7
   Ridge index regression, writing `m3_index_regression.csv`. Each gets a findings cell.
8. **Rerun** (about 5–6 min): `jupyter nbconvert --to notebook --execute --inplace modeling.ipynb`. Check
   0 error outputs with the one-liner in `latest_handoff.md` §4. The loky `KeyError` tracebacks at exit are
   harmless noise.
9. **Rewrite every "What we found" cell** (4, 8, 15, 18, 22, 25, 29, 34, 36, 41, 43 and the new ones) from the new
   printed output and CSVs. Check these explicitly and state any change honestly:
   - does the fire-ablation null still hold;
   - is LR still cheaper than persistence from about 3:1;
   - the onset catch rate;
   - the city ORs;
   - the H2 table (it should be identical: the H2 Logit doesn't use AQ history);
   - the horizon and month-wise results.
10. **Run a second time** and confirm byte-identical `docs/tables/m3_*.csv` (determinism).
11. **Regenerated artifacts to commit:** `src/*.py`, `modeling.ipynb`, `Dataset/clean/m3_params.json`,
    `docs/tables/m3_*.csv` (now 25 files), `figures/fig_m3_*.png`, `models/*.joblib`.

**Pitfalls:**
- `calm ≡ stagnant`: never enter all 8 wind sectors.
- Rain and Mar–Aug perfect separation in the Logit (X5).
- `liblinear` stays (X1).
- Balanced-tree thresholds near 0.7 are not a bug.
- Don't rerun the Role 1 or merge notebooks. If you do, `git checkout` the parquet and PNG files.
- A stray `cat > file` hangs the shell.

---

## 4. Step 2 (Phase 4): `DECISIONS.md`
**Commit:** "Decision log: Milestone 3 modelling choices"

**Where and how:**
- Add a section after "Merge and analysis (Role 2)" (the file ends at line 70 with row M10).
- Heading: `## Milestone 3 modelling, modeling.ipynb + src/modeling.py + src/evaluate.py`.
- Same columns: `# | Decision | Rule | Rows before → after | Why`. Rows `S1…`.

**Rows to include:**
- D3–D13 (from `context/milestone3_plan.md`).
- X1–X8 (`latest_handoff.md` §8.2).
- New rows: S-margin (Q4), S-leakage-check (Q1), S-group-error-rates (Q2), S-ridge (Q7), S-cost-framing (Q3).

**Exact counts to include:**
- 4,246 train / 1,298 validation rows;
- drops: 33 skip, 11 no target, 22 no `index_lag2`, 44 suspect feature-day rows and 11 suspect target-day rows;
- calm ≡ stagnant 631/631;
- rain 0 of 1,057 training rain days followed by a spike;
- Mar–Aug 0 spikes;
- CV 5 × 5 folds, seeds 0–4, purge 1 day, embargo 3 days, 330–495 fit rows removed per fold, test spike rate
  4.81% ± 1.35;
- **new** best hyperparameters and OOF thresholds, read from the regenerated `m3_params.json`. Don't copy them
  from the old handoff.

---

## 5. Step 3 (Phase 5): report and submission package
**Commit:** "Milestone 3 report sections and submission package"

### 5.1 `docs/manuscript/build_manuscript.py` (423 lines)
**How it works now:**
- Helpers `tab`, `h1`, `h2`, `p`, `bullets`, `table`, `figure`, `f` append to `blocks`, and the script writes
  `docs/manuscript/manuscript.json`.
- Sections: front matter at lines 84–99; §4 Hypotheses ends at line 389; §5 Limitations at 394; §6
  Reproducibility at 401–407; `h2("References")` at 409; refs list at 410–419.

**Changes:**
- Add `argparse --milestone {2,3}`, default 2. **The default run must produce a byte-identical `manuscript.json`**
  (verify with `git diff --exit-code docs/manuscript/manuscript.json`).
- With `--milestone 3`, write `docs/manuscript/manuscript_m3.json` and change:
  - title, e.g. "Crop Fires, Weather Traps and Smog across Punjab: Data, Exploratory Analysis and Baseline
    Forecasts";
  - subtitle "Trans-Boundary Smog Prediction: Milestone 03, Baseline Models, Leakage-Free Validation and
    Error-Cost Analysis";
  - one sentence added to the abstract with the headline result;
  - one closing line in §4;
  - an updated §6 (adds `modeling.ipynb`, `src/modeling.py`, `src/evaluate.py`, `models/`, `m3_params.json`,
    run time);
  - Sections 7–12 inserted **before** References;
  - the new references.
- Read **every number** from `docs/tables/m3_*.csv` through `tab()`. Format with `f()` (no "-0.00"). No
  hand-typed results.

**Sections 7–12** (about 6 pages; aim for 16–17 pages in total):
- **7 Baseline Models and Justification.**
  - Majority class: the floor; shows that accuracy misleads (93.1%-style number from the CSV).
  - Persistence: the benchmark, ρ = 0.82 day to day.
  - LR: interpretable odds ratios for health officials, probabilistic output for thresholding, L1/L2
    regularisation for correlated weather.
  - Shallow DT: non-additive trap rules, readable as a flow chart.
  - Why not KNN: distance on mixed binary and continuous columns, and no interpretability. RF/GBM →
    Milestone 4.
  - The margin encoding (Q4) and why.
- **8 Experimental Setup.**
  - Chronological split 76.6/23.4 with a 3-day gap; class balance per split (`m3_split_balance`).
  - Why there is no random stratified split, with the **`m3_leakage_check` table**.
  - The purged and embargoed 5 × 5 StratifiedGroupKFold and the stratification check (`m3_cv_folds`,
    Fig. M3.1).
  - Grids and PR-AUC as the tuning metric (Saito & Rehmsmeier 2015); the C = 100 plateau note; Fig. M3.2.
  - The OOF threshold rule, fixed before validation.
  - Leakage guards (asserts) and the solver note (X1).
- **9 Results.**
  - Metrics table: all 8 models × accuracy, precision, recall, specificity, F1, ROC-AUC, PR-AUC [CI], cost
    (`m3_metrics_validation`); one CV row summary.
  - Fig. M3.3.
  - Fire ablation (`m3_fire_ablation`).
  - Short sensitivity paragraphs: month-wise label, horizons, AQ encoding (`m3_aq_encoding`), index regression
    (`m3_index_regression`).
- **10 Asymmetric Error Cost Analysis.**
  - FN/FP consequence table (who bears it, consequence, reversible?) and the Q3 sourced framing.
  - Cost at 5:1 (`m3_cost`) and the cost curve with its break-even point (Fig. M3.4).
  - Confusion matrices (Fig. M3.5).
  - Onset vs continuation (`m3_errors_onset`); by city and month; edge cases (`m3_top_errors`,
    `m3_fn_context`).
  - The group error rates (`m3_error_rates_group`, Q2).
- **11 Drivers and Initial Policy Takeaways.**
  - The H2 table (`m3_h2_logit`): stagnant, RH, temperature range, rain via Fisher.
  - Odds ratios and the permutation/Gini importance (Fig. M3.6, `m3_odds_ratios`, `m3_importance`); the tree
    (Fig. M3.7).
  - How the margin feature changed the city ORs.
  - Policy, Pakistan first:
    - a next-day advisory driven by today's index plus a weather-trap check (stagnant, humid, rain-free, large
      day-night range), slotted into the Punjab EPD advisory and closure process;
    - rain as an all-clear signal;
    - the ≥ break-even cost view justifies model-based alerts over persistence;
    - fire control as a source-reduction policy whose benefit shows up in today's smog, not as extra next-day
      forecast skill.
  - Then cross-border: CAQM GRAP and the open H4 question.
- **12 Limitations and Milestone 4 Roadmap.**
  - Limitations:
    - no model beats persistence on ranking (re-check after Q4);
    - class imbalance, and one training winter;
    - 18 validation weeks with most spikes in December;
    - Islamabad = Rawalpindi;
    - the label-timing artefact;
    - CAMS model data and UTC+5 for India;
    - the group disparities found in Q2.
  - Roadmap:
    - RF/GBM;
    - per-horizon tuning;
    - probability calibration;
    - a full fairness audit (error-rate parity by city and country, threshold per group);
    - the H1/H3/H4 tests;
    - surface pressure;
    - the 2024 out-of-time test (Week 14).

**Figures:** `figures/fig_m3_1` … `fig_m3_7`, using the `figure(path, caption, width_in)` helper. Captions end
with "Produced by modeling.ipynb."

**References** (verify **each** by web search before adding; never cite from memory):
- Pedregosa et al. 2011, *JMLR* 12, scikit-learn;
- Roberts et al. 2017, *Ecography* 40, blocked CV for structured data;
- Saito & Rehmsmeier 2015, *PLOS ONE* 10(3), PR vs ROC on imbalanced data;
- Seabold & Perktold 2010, statsmodels, SciPy proceedings;
- the Q3 cost source(s);
- the Punjab EPD and CAQM GRAP sources (Q8).

Keep the existing reference style. The list is numbered by the renderer.

### 5.2 `docs/manuscript/render_docx.js` (151 lines)
**How it works now:** reads `manuscript.json`, writes `Milestone2_Manuscript_Draft.docx` at the repo root (line
148), with the footer "Trans-Boundary Smog Prediction, Milestone 02" (line 141) and the document title at line 120.

**Change:** an optional CLI argument `process.argv[2]`, default `"2"`, so the behaviour is unchanged by default.
With `"3"` it:
- reads `manuscript_m3.json`;
- writes `submission/milestone3/Milestone3_Report.docx` (create the directory);
- uses the footer "Trans-Boundary Smog Prediction, Milestone 03";
- sets the title "Trans-Boundary Smog Prediction: Milestone 3 report".

**Run:**
```
python docs/manuscript/build_manuscript.py --milestone 3
node docs/manuscript/render_docx.js 3
```
`npm install` first if `node_modules/` is missing.

### 5.3 PDF
`python -c "from docx2pdf import convert; convert('submission/milestone3/Milestone3_Report.docx')"`. This needs
MS Word; the fallback is Word → Save As PDF. Read the PDF and check:
- the figures render;
- 16–17 pages;
- the footer says "Milestone 03";
- no table overflows;
- 5 numbers spot-checked against the CSVs.

### 5.4 Package (Q6)
- Copy the Q6 file list into `submission/milestone3/` with the repo-relative layout.
- Write `README.md` in the style of `submission/README.md`: what each file is, how to run (`pip install -r
  requirements.txt`, then from that folder `jupyter nbconvert --to notebook --execute --inplace modeling.ipynb`,
  about 6 min on 8 cores), the file map (modules, tables, figures, models, `m3_params.json`), and the note that
  2024 is sealed and the Role 1 and merge notebooks are in the repo.
- **Test:** copy `submission/milestone3/` to the session scratchpad, run the notebook there, and expect 0 errors.
  The tables and figures it writes go to that scratch copy only.

---

## 6. Step 4: refresh `context/latest_handoff.md`
**Commit:** "Update project handoff after Milestone 3"

Update §0 (state), §2 (commits), §8 (add Q1–Q8 as decisions), §9 (new results), §10 (notebook map) and §11
(nothing left except Milestone 4 / Week 14).

---

## 7. Final verification checklist
- [ ] The notebook runs with 0 error outputs, and a second run gives byte-identical `docs/tables/m3_*.csv`.
- [ ] The asserts pass: no 2024 date; `assert_train_only` before every fit, including the leakage check and the
      raw/Ridge refits; disjoint purged folds; margin ≥ 0 ⇔ `persist_spike`.
- [ ] Every number in the "What we found" cells matches its CSV. Spot-check 10 with a short script.
- [ ] Default `python docs/manuscript/build_manuscript.py`, then `git diff --exit-code docs/manuscript/manuscript.json`,
      shows no change.
- [ ] The Milestone 3 docx and PDF are built and inspected (pages, figures, footer, 5 numbers).
- [ ] The package runs on its own from a scratch copy.
- [ ] `git log -4 --format='%an <%ae>%n%b'` shows only bilal and no trailers. `git branch -a` shows only `main`.
      Everything is pushed.
