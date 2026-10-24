# Milestone 3 submission: baseline models, leakage-free validation and error-cost analysis

Trans-Boundary Smog Prediction: Crop Fires and Climate Traps across Punjab (Pakistan and India).
Munir Tariq (10067), Ismail Nooruddin (09958), Bilal Ayub (09716).

This folder is self-contained: it mirrors the repository layout, so the notebook runs from here.

| File | What it is |
|---|---|
| `Milestone3_Report.pdf` / `.docx` | The report. Sections 1–6 are the Milestone 2 draft (data, preprocessing, EDA, hypotheses); Sections 7–12 are new: baseline models, experimental setup, results, asymmetric error cost, drivers and policy takeaways, limitations and the Milestone 4 roadmap. |
| `modeling.ipynb` | The Milestone 3 notebook (sections M3.1–M3.10), executed top to bottom with all outputs saved. Every computational section ends with a "What we found" cell. |
| `src/modeling.py` | Data access (`load_model_frame`), feature sets, the purged and embargoed `StratifiedGroupKFold` splitter, LR / DT / Ridge pipelines, grids, tuning, out-of-fold predictions and the cost-based alert threshold. |
| `src/evaluate.py` | Metrics (accuracy, precision, recall, specificity, F1, ROC-AUC, PR-AUC, Brier, cost), week-block bootstrap, cost curve, error breakdown, group error rates, regression metrics. |
| `src/config.py`, `src/plotting.py` | Shared settings (cities, dates, folders) and the figure style, unchanged from Milestone 2. |
| `Dataset/clean/master_daily.parquet` | The master table from Milestone 2 (5,665 city-days × 287 columns): the only data the notebook reads. |
| `Dataset/clean/role2_params.json` | Milestone 2 settings (fire cone and radius); the notebook checks it. |
| `Dataset/clean/m3_params.json` | Written by the notebook: target, cost ratio, CV settings, feature sets, best hyperparameters and alert thresholds of every model. |
| `models/*.joblib` | The ten fitted pipelines (majority class; LR and DT on the full, weather-only and no-fire sets; Ridge index models), refitted on all training rows. Load with `joblib.load("models/lr_full.joblib")` and call `predict_proba` on the columns in `src.modeling.FEATURE_SETS`. |
| `requirements.txt` | Python packages. |

**How to run** (Python 3.14 was used; about 5 minutes on 8 cores):

```
python -m pip install -r requirements.txt
# from this folder:
jupyter nbconvert --to notebook --execute --inplace modeling.ipynb
```

The notebook writes its tables to `docs/tables/m3_*.csv` and its figures to `figures/fig_m3_*.png` (both folders are created
if missing), the parameters to `Dataset/clean/m3_params.json` and the models to `models/`. All seeds are fixed: two runs
write byte-identical tables. At the end of a run on Windows, joblib may print `KeyError: ...joblib_memmapping_folder...`
tracebacks while cleaning up its temporary folders; they appear after the notebook is saved and are harmless.

**Rules kept.** Every fit, scaler, threshold and hyperparameter uses training rows only (to 31 Aug 2023); the validation
season (Sep–Dec 2023) only reports results; 2024 is sealed and never read (the loader asserts it). The Role 1 notebooks
(`air_quality.ipynb`, `weather.ipynb`, `fire.ipynb`), the merge notebook (`merge_analysis.ipynb`) that builds the master table,
and the decision log (`DECISIONS.md`, Milestone 3 rows S1–S19) are in the project repository.
