# Milestone 5 submission: new data ingestion, drift and re-training

Trans-Boundary Smog Prediction: Crop Fires and Climate Traps across Punjab (Pakistan and India).
Munir Tariq (10067), Ismail Nooruddin (09958), Bilal Ayub (09716).

This folder mirrors the repository layout, so the notebooks run from here.

| File | What it is |
|---|---|
| `Milestone5_Report.pdf` / `.docx` | The report: one IEEE two-column paper over the whole semester. It has Sections I–VIII (introduction, data, EDA and drivers, modelling, fairness, data expansion and drift, policy, limitations and conclusion), numbered references and a one-column appendix (Tables A1–A9). The body and references fill 7 pages. |
| `data_extension.ipynb` | The Milestone 5 notebook (sections M5.1–M5.11), executed top to bottom with all outputs saved. Every section ends with a "What we found" cell, and a summary closes the notebook. |
| `advanced_modeling.ipynb`, `modeling.ipynb` | The Milestone 4 and Milestone 3 notebooks. They built the initial models that `data_extension.ipynb` tests zero-shot. |
| `src/ingest.py` | New. The Role 1 cleaning logic for air quality, weather and fire, ported from the three stream notebooks into functions. It reads the raw files for any date window and applies the frozen 2022–23 parameters. It also holds the schema report and the reproduction check. |
| `src/drift.py` | New. PSI, KS and χ² drift tables with Benjamini–Hochberg q-values, the domain classifier and the concept-drift likelihood-ratio test. |
| `src/config.py`, `src/merge.py`, `src/modeling.py` | Milestone 4 code plus the Milestone 5 windows. The 2024 seal moves only through an explicit `sealed_from` argument, so the earlier notebooks still reproduce. |
| `src/evaluate.py`, `src/fairness.py`, `src/plotting.py` | Metrics and week-block bootstrap, the fairness audit and mitigation, and the figure style. Unchanged. |
| `Dataset/clean/master_daily_m5.parquet` | The expanded master table: 9,669 city-days (5,665 initial + 4,004 new) × 291 columns. `master_data_dictionary_m5.csv` describes the columns. |
| `Dataset/clean/m5/` | The daily AQ, weather, wind and fire tables for 2022–2024, written by `src/ingest.py`, with copies of the frozen parameter files. |
| `Dataset/clean/*.parquet`, `*_params.json` | The committed 2022–23 daily tables and master, used by the reproduction check. The frozen parameters are in `aq_params.json`, `weather_zscore_params.json`, `fire_zscore_params.json` and `role2_params.json`. `m3_params.json` and `m4_params.json` hold the Milestone 3 and 4 settings. |
| `Dataset/clean/m5_params.json` | Written by the notebook: windows, dataset sizes, VIIRS gap days, drift settings, CV and search settings, best hyperparameters, the final model, its thresholds and the re-learned label sensitivity. |
| `Dataset/external/city_population.csv` | Census population and city-size tier for the 11 cities (Pakistan 2023, India 2011). |
| `docs/tables/m4_metrics_validation.csv`, `m4_mitigation.csv` | Milestone 4 results. The notebook asserts that the zero-shot setting (1) reproduces them. |
| `models/*.joblib` | The Milestone 3 and 4 models (no prefix) and the re-trained Milestone 5 models (`m5_` prefix). The final re-trained model is `models/m5_lr_full.joblib`. |
| `requirements.txt` | Python packages. Milestone 5 adds none. |

**Raw files.** Section M5.1 reads the raw air-quality, weather and NASA VIIRS files (about 180 MB). They are not in this
folder. Copy `Dataset/Pakistan/` and `Dataset/India/` from the project repository into `Dataset/` before running.

**How to run** (Python 3.14 was used; about 80 minutes on 8 cores, mostly the random searches):

```
python -m pip install -r requirements.txt
# from this folder, after copying the raw files:
jupyter nbconvert --to notebook --execute --inplace --ExecutePreprocessor.timeout=10800 data_extension.ipynb
```

The notebook writes its tables to `docs/tables/m5_*.csv` and its figures to `figures/fig_m05_*.png`. Setting the
environment variable `M5_FAST=1` runs a short debugging version (100 bootstrap draws, 4 search draws, one CV repeat). It
records `"fast_run": true` in `m5_params.json`, and the manuscript builder refuses those tables. All seeds are fixed. On
Windows, joblib may print `KeyError: ...joblib_memmapping_folder...` tracebacks at the end of a run. They appear after
the notebook is saved and are harmless.

**Main results** (LR full, Sep–Dec test seasons, 5:1 cost ratio):

| Setting | PR-AUC | Cost per 1,000 city-days |
|---|---|---|
| (1) Initial model, Sep–Dec 2023 | 0.695 | 117.1 |
| (2b) Initial model, zero-shot, Sep–Dec 2024 | 0.726 | 167.7 |
| (3a) Re-trained model, Sep–Dec 2024 | 0.728 | 166.9 |
| (3b) Re-trained model, combined data, purged CV | 0.727 | 95.7 |

**Rules kept.**
- The 2024 rows use the 2022–23 index weights, z-scores and spike thresholds. Nothing is re-learned, except in the one labelled sensitivity run.
- Every re-training fit, threshold and hyperparameter uses rows up to 31 Aug 2024 only. The Sep–Dec 2024 test only reports.
- Outliers and suspect days are flagged, never deleted from the daily tables.
- Every number in the report comes from `docs/tables/*.csv` or the params files. The decision log (`DECISIONS.md`, Milestone 5 rows N1–N16) and the manuscript builder are in the project repository.
