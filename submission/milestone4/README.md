# Milestone 4 submission: advanced models, geographic fairness audit and bias mitigation

Trans-Boundary Smog Prediction: Crop Fires and Climate Traps across Punjab (Pakistan and India).
Munir Tariq (10067), Ismail Nooruddin (09958), Bilal Ayub (09716).

This folder mirrors the repository layout, so both notebooks run from here.

| File | What it is |
|---|---|
| `Milestone4_Report.pdf` / `.docx` | The report, rewritten as one research paper: abstract, introduction, related work, data, exploratory findings and hypotheses, methods, results (models, costs, drivers, hypotheses H1–H5, fairness audit, mitigation), discussion (FATEN, living lab, governance, policy), limitations, conclusion, APA references and Appendices A–C. |
| `advanced_modeling.ipynb` | The Milestone 4 notebook (sections M4.1–M4.10), executed top to bottom with all outputs saved. Every section ends with a "What we found" cell. |
| `modeling.ipynb` | The Milestone 3 notebook. It builds the baseline models that `advanced_modeling.ipynb` reloads. |
| `src/fairness.py` | New. City-size tiers, group metrics (alert rate, TPR, FPR, precision, cost), disparity measures (DIR and the two-sided 80% rule, equal opportunity, predictive equality, equalized odds), reweighing, per-tier and constrained thresholds, and the Pareto mask. |
| `src/modeling.py` | Milestone 3 code, plus the random forest and gradient-boosting pipelines, their search spaces, `tune_random` and sample weights in `oof_predict`. |
| `src/evaluate.py`, `src/config.py`, `src/plotting.py` | Metrics and week-block bootstrap, shared settings and the figure style. |
| `Dataset/clean/master_daily.parquet` | The master table (5,665 city-days × 287 columns). |
| `Dataset/clean/role2_params.json`, `m3_params.json` | Milestone 2 and Milestone 3 settings. The notebook checks the Milestone 3 thresholds against `m3_params.json`. |
| `Dataset/clean/m4_params.json` | Written by the notebook: search settings, best hyperparameters, thresholds, the final-model rule and choice, the fairness settings and the per-tier thresholds of every mitigation rule. |
| `Dataset/external/city_population.csv` | Census population and city-size tier for the 11 cities, with sources (Pakistan 2023, India 2011). |
| `docs/tables/m3_metrics_validation.csv` | Milestone 3 validation metrics. The notebook asserts that the reloaded LR and DT reproduce them. |
| `models/*.joblib` | Fitted pipelines refitted on all training rows: the Milestone 3 models (majority class, LR, DT, Ridge) and the new RF and HGB models on the full, weather-only and no-fire sets. The final model is `models/lr_full.joblib`. |
| `requirements.txt` | Python packages. Milestone 4 adds none. |

**How to run** (Python 3.14 was used; about 80 minutes on 8 cores, mostly the random searches):

```
python -m pip install -r requirements.txt
# from this folder:
jupyter nbconvert --to notebook --execute --inplace advanced_modeling.ipynb
```

The notebook writes its tables to `docs/tables/m4_*.csv` and its figures to `figures/fig_m04_*.png`. It also writes the
parameters to `Dataset/clean/m4_params.json` and the RF and HGB models to `models/`. All seeds are fixed, and two runs
write byte-identical tables. On Windows, joblib may print `KeyError: ...joblib_memmapping_folder...` tracebacks at the
end of a run. They appear after the notebook is saved and are harmless.

**Using the alert.** Load `models/lr_full.joblib` with `joblib.load` and call `predict_proba` on the columns in
`src.modeling.FEATURE_SETS["full"]`. Map each city to its tier with `src.fairness.add_groups`. Then alert when the
probability reaches the tier's threshold in `m4_params.json` (`mitigation_thresholds` → `LR full` →
`threshold per tier, cost-optimal`).

**Rules kept.**
- Every fit, weight, threshold and hyperparameter uses training rows only (to 31 Aug 2023).
- The validation season (Sep–Dec 2023) only reports results.
- 2024 is sealed and never read. The loader asserts it.
- The decision log (`DECISIONS.md`, Milestone 4 rows P1–P9) and the earlier notebooks are in the project repository.
