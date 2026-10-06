"""Builds the Milestone 2 manuscript draft (Sections I-VI) as a JSON content model.

Tables are read from docs/tables/*.csv, which merge_analysis.ipynb writes, so the numbers in
the manuscript are the numbers the notebook printed. render_docx.js turns the JSON into Word.

Run from the repository root, after the four notebooks:
    python docs/manuscript/build_manuscript.py
    node docs/manuscript/render_docx.js
"""
import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
T = ROOT / "docs" / "tables"
OUT = ROOT / "docs" / "manuscript" / "manuscript.json"

blocks = []
counters = {"table": 0, "figure": 0}


def tab(name, **kw):
    return pd.read_csv(T / f"{name}.csv", **kw)


def h1(text):
    blocks.append({"t": "h1", "text": text})


def h2(text):
    blocks.append({"t": "h2", "text": text})


def h3(text):
    blocks.append({"t": "h3", "text": text})


def p(text):
    """Paragraph; **bold** and *italic* are rendered."""
    blocks.append({"t": "p", "text": text})


def bullets(items):
    blocks.append({"t": "bullets", "items": items})


def table(caption, header, rows, widths, note=None, font=8.5):
    counters["table"] += 1
    blocks.append({"t": "table", "caption": f"**Table {counters['table']}.** {caption}", "header": header,
                   "rows": [[str(c) for c in r] for r in rows], "widths": widths, "note": note, "font": font})
    return counters["table"]


def figure(path, caption, width_in=6.3):
    counters["figure"] += 1
    blocks.append({"t": "figure", "path": str(ROOT / path), "caption": f"**Figure {counters['figure']}.** {caption}",
                   "width_in": width_in})
    return counters["figure"]


def f(x, d=2):
    out = f"{x:,.{d}f}"
    return out[1:] if out.startswith("-") and float(out) == 0 else out    # no "-0.00"


# The notebook saves tables at 3 decimals, so a value such as -1.1546 is stored as -1.155 and then
# rounds the wrong way at 2 decimals. These cells carry the full-precision value from merge_analysis.ipynb.
EXACT = {("summary_train", "Composite Smog Index (z units)", "skew"): -1.1546,
         ("summary_train", "NO2 daily mean (µg/m³)", "iqr"): 26.8146,
         ("summary_train", "Fires in upwind cone, 300 km (count)", "sd"): 176.9945,
         ("outlier_audit_train", "Fires in upwind cone, 300 km (count)", "sd_all"): 176.9945,
         ("outlier_audit_train", "Rain total (mm)", "sd_without_iqr_outliers"): 0.4253,
         ("cone_vs_radius", ("Training Oct-Dec (headline)", "Far (PK)"), "upwind cone (up45, 300 km)"): 0.2351,
         ("cone_vs_radius", ("Training Oct-Dec (headline)", "Near border (PK)"), "downwind placebo (down45, 300 km)"): -0.0045}


def exact(name, df):
    for (n, row, col), v in EXACT.items():
        if n == name:
            df.loc[row, col] = v
    return df


# =====================================================================
# Front matter
# =====================================================================
blocks.append({"t": "title", "text": "Trans-Boundary Smog Prediction: Crop Fires and Climate Traps across Punjab (Pakistan and India)"})
blocks.append({"t": "subtitle", "text": "Milestone 02 manuscript draft: data preparation, exploratory analysis and hypotheses"})
blocks.append({"t": "authors", "text": "Munir Tariq (10067) · Ismail Nooruddin (09958) · Bilal Ayub (09716)"})
blocks.append({"t": "affil", "text": "Data Science for Social Good, Habib University, Karachi · October 2026"})

p("**Abstract.** Every winter, smoke from crop-residue burning and urban emissions is trapped over the Punjab plain shared by Pakistan and India. "
  "We build a daily master dataset for 11 cities (7 Pakistani, 4 Indian Punjab) from three independent streams: hourly Open-Meteo air quality "
  "(CAMS model output), hourly Open-Meteo weather, and 1.28 million NASA VIIRS fire detections. After alignment to one UTC+5 clock and a one-to-one "
  "merge, the master table holds 5,665 city-days (4 August 2022 to 31 December 2023) and 287 columns, with no missing predictor value. "
  "The target is a Composite Smog Index of six z-scored pollutants and a city-specific spike label. Exploratory analysis on the training period shows "
  "four results. (i) Fires inside a ±45° upwind cone within 300 km track next-day smog (median Spearman ρ = 0.23 over the Pakistani cities in the harvest season), "
  "while the plain 300 km circle (−0.06) and a downwind placebo cone (0.01) do not. (ii) The association peaks one day after the fires. "
  "(iii) Stagnant and humid days roughly triple the next-day spike rate (risk ratios 2.9 and 2.6, and 4.4 when both fall on a dry day), and no rain day was followed by a spike. (iv) Spikes concentrate in December and January, after the "
  "October–November burning peak, which shows that fires alone are not enough: the weather must trap the smoke. Five formal hypotheses, mapped to master-file columns, set up Milestone 3.")

# =====================================================================
# I. Project alignment and master dataset inventory
# =====================================================================
h1("I. Project Alignment and Master Dataset Inventory")
h2("A. Team, problem and research question")
table("Team members, disciplinary background and Milestone 2 roles.",
      ["Member", "ID", "Background", "Role 1 (own stream)", "Role 2 (merged data)"],
      [["Munir Tariq", "10067", "Computer Science (minor: Social Development and Policy)", "Person B: weather and wind",
        "Leads the merge; master overview, combined summary, correlations, weather traps"],
       ["Ismail Nooruddin", "09958", "Computer Science", "Person A: air quality and target",
        "Group-by and contingency tables, index figure, weight check"],
       ["Bilal Ayub", "09716", "Computer Science", "Person C: NASA VIIRS fire",
        "Cone and radius sensitivity, cross-border check"]],
      [1500, 700, 2300, 2000, 3138])
p("**Social problem.** Smoke ignores borders. Winter smog episodes in Lahore and the other Punjab cities combine local emissions with smoke from rice-residue "
  "burning on both sides of the border, trapped by calm, humid air. Health services receive no advance warning, and city agencies cannot separate imported from local smoke.")
p("**SDG alignment.** SDG 3 (target 3.9, illness from air pollution; 3.d, early warning), SDG 11 (target 11.6, urban air quality) and SDG 13 "
  "(regional, cross-border climate action). The cross-border analysis also speaks to SDG 17 (cooperation between countries).")
p("**Research question.** Which fire and weather predictors, available on day *t*, explain hazardous Composite Smog spikes in Pakistani Punjab cities on days *t + 1* to *t + 3*, "
  "and how much better than a persistence baseline and a weather-only baseline can they forecast those spikes? Following our instructor's feedback, the proposal's "
  "fixed target score (ROC-AUC above 0.88) has been dropped: we identify reasonable predictors, report the pattern, and then report the best performance we can honestly reach.")

h2("B. Master dataset overview")
ov = tab("master_overview", index_col=0)["value"]
table("Master analytical dataset (Dataset/clean/master_daily.parquet).",
      ["Item", "Value"],
      [["Rows (observations)", ov["Rows (observations)"]], ["Columns (variables)", ov["Columns (variables)"]],
       ["Observational unit", ov["Observational unit"]], ["Cities", ov["Cities"] + ": Lahore, Faisalabad, Multan, Rawalpindi, Sialkot, Rahim Yar Khan, Islamabad; Amritsar, Ferozepur, Ludhiana, Jalandhar"],
       ["Period", ov["Period"]], ["Split (city-days)", ov["Split"] + " (train 4 Aug 2022 to 31 Aug 2023; skip 1 to 3 Sep 2023; validation 4 Sep to 31 Dec 2023)"],
       ["Source 1: air quality", ov["Source 1: air quality"]], ["Source 2: weather", ov["Source 2: weather"]], ["Source 3: fire", ov["Source 3: fire"]],
       ["Columns by owner", "Air quality (A) 52; weather (B) 58; fire (C) 128; keys, targets, lags, encodings and split built in the merge 49"],
       ["Sealed", "All 2024 files (kept for the Week 14 out-of-time test); never read in this milestone"]],
      [2400, 7238])
p("The full column list with meaning, unit, source and owner is in Dataset/clean/master_data_dictionary.csv (287 rows, one per column).")

# =====================================================================
# II. Data and Preprocessing
# =====================================================================
h1("II. Data and Preprocessing")
h2("A. Collection audit")
table("Raw data collected for each stream.",
      ["Stream", "Source and collection", "Raw files", "Raw records", "Notes from the audit"],
      [["Air quality (A)", "Open-Meteo Air Quality API, exported per city centre as hourly CSV/XLSX in GMT. Values are output of the CAMS global atmospheric-composition model (about 0.4° grid), not ground monitors.",
        "11 (10 CSV, Ludhiana XLSX); 3-line metadata header", "453,192 hourly rows (6 Jan 2022 to Sep 2026)",
        "No duplicate or skipped hours; Ludhiana column order differs (read by name). Islamabad and Rawalpindi identical (same model grid cell). No values before 4 Aug 2022."],
       ["Weather (B)", "Open-Meteo Historical Weather API (reanalysis-based gridded estimates), hourly, GMT, same city points as the file headers.",
        "11 (10 CSV, Ludhiana XLSX); two irregular file names", "433,728 hourly rows",
        "No missing value, no duplicate or skipped hour. Files start 12 to 30 Jan 2022. No surface-pressure column."],
       ["Fire (C)", "NASA FIRMS archive download, VIIRS 375 m active fires (NOAA-20), one file per country and year.",
        "4 used (IN and PK, 2022 and 2023); 2 sealed (2024)", "1,284,773 detections",
        "0 duplicates; one satellite; acq_time read as text to keep leading zeros; time in UTC."]],
      [1150, 3000, 1600, 1500, 2388])

h2("B. Temporal alignment and structural organisation")
p("All raw times are GMT/UTC. Each stream added 5 hours to the full timestamp **before** taking the calendar date, so evening hours fall on the right local day "
  "(26,626 fire detections moved to the next local date). The same UTC+5 clock is used for the Indian cities (IST is UTC+5:30) so that all streams share day boundaries. "
  "The reshaping steps were: stacking the 11 city files of each stream (concat); aggregating hourly rows to one row per city-day (group-by, with mean, max, total and vector-mean rules); "
  "computing fire counts per city, cone, radius and origin as a long table (602,250 rows) and pivoting the chosen settings to wide columns; and joining the three "
  "streams on a calendar spine. City names come from one shared dictionary (src/config.py), so the keys are spelled the same in every table.")
book = [["Air quality", "453,192 hourly rows → 191,153 in 2022–2023 → 135,905 after removing the empty Jan–Aug 2022 block → 5,665 city-days (≥ 18 of 24 hours; none dropped)"],
        ["Weather", "433,728 hourly rows → 188,393 in 2022–2023 → 7,852 city-days → 5,665 in the modelling window"],
        ["Fire", "1,284,773 → 287,323 in the study box (26–37°N, 68–79°E) → 279,968 vegetation fires (type 0) → 238,796 nominal/high confidence → 238,756 on 2022–2023 local dates → 8,030 city-days (zeros filled) → 5,665 in the window"],
        ["Master", "spine 5,665 → AQ join 5,665 (all matched) → weather join 5,665 (all matched) → fire join 5,665 (all matched); 287 columns"]]
table("Row bookkeeping from raw files to the master table (every removal is logged in DECISIONS.md).", ["Stream", "Steps and row counts"], book, [1500, 8138])

h3("Merge procedure (Part 2A)")
bullets(["**Swap and check.** Each stream was checked against the shared rules before joining: 11 cities spelled as in the dictionary, correct country code, no duplicate city-day, complete calendar, date stored as a real date. All three passed (merge_analysis.ipynb, 2A.1).",
         "**Spine.** An empty table of 11 cities × 515 days (5,665 rows) was built from the calendar, not from a data table, so a missing day in any stream would stay visible.",
         "**Key types.** city and country as clean text and date as datetime64[ns] in all tables; a type mismatch is the usual reason a join silently matches nothing.",
         "**One-to-one joins.** AQ, then weather, then fire were left-joined on city, country and date with pandas' one_to_one validation. The row count stayed 5,665 after every join and every spine row found a partner.",
         "**Lags and targets, grouped by city.** Lags of 1 to 3 days for the key weather and fire predictors (computed with a 3-day lead-in before the window). Targets: the index on days t+1, t+2 and t+3, and the spike labels for those days computed with Person A's saved thresholds. Baselines: today's index (persistence) and yesterday's index. Grouping by city prevents the last days of one city leaking into the first days of the next; a test confirms each target is the same city's index h days later.",
         "**Reusable.** Every step is a function in src/merge.py that takes the date window; build_master() reproduces the master exactly, so the Week 14 run on 2024 only changes the dates in src/config.py."])
sp = tab("split_counts", index_col=0)
rt = tab("rows_with_target", index_col=0)
table("Split and target availability.",
      ["Split / horizon", "City-days", "of which Oct–Dec", "Dates"],
      [["Train", f"{sp.loc['train','rows']:,}", f"{sp.loc['train','oct_dec_rows']:,}", "2022-08-04 to 2023-08-31"],
       ["Skip (3 days = longest horizon)", f"{sp.loc['skip','rows']:,}", "0", "2023-09-01 to 2023-09-03"],
       ["Validation", f"{sp.loc['validation','rows']:,}", f"{sp.loc['validation','oct_dec_rows']:,}", "2023-09-04 to 2023-12-31"]] +
      [[f"Rows with a target, h = {h}", f"{rt.loc[f'h={h}','rows with target']:,}", f"{rt.loc[f'h={h}','of which Oct-Dec']:,}",
        f"target missing on the last {h} day(s) of 2023 (2024 sealed)"] for h in (1, 2, 3)],
      [3300, 1500, 1600, 3238])

h2("C. Cleaning and missing-data strategy")
mis = tab("master_missing_all_columns", index_col=0)
complete = int((mis["missing_count"] == 0).sum())
table("Missing values by stage. Counts and percentages for every one of the 287 master columns are in docs/tables/master_missing_all_columns.csv and in the notebook (Part 2B, step 1).",
      ["Where", "What is missing", "Count (%)", "Decision"],
      [["AQ raw, 2022–2023", "All 7 pollutants in one continuous block, 6 Jan (first hour in the files) to 4 Aug 2022, same hours in all cities", "55,248 of 191,153 hourly rows (28.9%)",
        "Not imputed. Modelling starts 2022-08-04 for all streams (listwise deletion of the block)"],
       ["AQ after 4 Aug 2022", "Short gaps", "0", "Rule kept for 2024: linear interpolation of gaps up to 6 h; a day needs ≥ 18 valid hours"],
       ["Weather raw", "Any variable", "0 of 433,728 rows", "Nothing to impute"],
       ["Fire raw", "Cone counts on days without wind direction (Jan 2022)", "178 city-days", "Left empty (0 would claim 'no upwind fire'); all fall before the window"],
       ["Fire grid", "Days without any detection", "-", "Coded 0 (a real zero), never missing"],
       ["Master, predictors", "Any of 278 predictor/key/encoding columns", "0", "-"],
       ["Master, targets", "target_index_h1/h2/h3 and target_spike_h1/h2/h3", "11 / 22 / 33 (0.19% / 0.39% / 0.58%)", "Target day falls in sealed 2024: left missing, rows excluded per horizon"],
       ["Master, baselines", "index_lag1/2/3", "11 / 22 / 33", "AQ has no day before 2022-08-04: left missing"]],
      [1500, 3100, 2000, 3038])
p(f"In total {complete} of the 287 master columns have no missing value. **Why not impute?** The AQ gap is not random. The source has no values before August 2022 "
  "in any city. Filling seven months by interpolation or copying would invent the seasonal pattern the model must learn. The 2022 rows were therefore removed "
  "from every stream (the team's decision), and the window starts on 2022-08-04.")
p("**Selection bias.** (i) The training period contains **one** harvest season (October–December 2022) and one January–March, while August–December appears twice in the window. "
  "Any seasonal estimate rests on one winter. This is why the Week 14 plan retrains with the first half of 2024 and tests on the second half. "
  "(ii) 44 city-days on 13–16 December 2022 have near-zero values for every pollutant in all cities at once, a likely source error. They are flagged (suspect_day = 1) and, by team decision, kept in all statistics. "
  "They are the reason the index has a skewness of −1.15 on training days (+0.26 without them). "
  "(iii) The satellite cannot see fires under thick cloud or fog, which is most common on the worst smog days, so fire–smog associations are likely underestimated. "
  "(iv) Islamabad and Rawalpindi share one AQ series, so there are 10 independent AQ series, not 11.")

h2("D. Transformations and scaling")
fs = tab("fire_setting_skew", index_col=0)
table("Right-skewed variables before and after log(1 + x), training days. Air-quality values are from air_quality.ipynb, weather from weather.ipynb, fire from merge_analysis.ipynb.",
      ["Variable", "Skew raw", "Skew after log1p", "Note"],
      [["PM2.5 daily mean (µg/m³)", "1.95", "0.37", "10 of 13 AQ columns had skew > 1 and were logged"],
       ["PM10 daily mean (µg/m³)", "1.75", "0.35", ""],
       ["CO daily mean (µg/m³)", "3.18", "0.37", ""],
       ["Dust daily mean (µg/m³)", "5.76", "0.81", "not in the index"],
       ["Rain total (mm)", "6.46", "1.79", "61% of days are 0 mm, so skew stays > 1"],
       ["Fires in upwind ±45° cone, 300 km", f(fs.loc['fire_cnt_up45_r300_all', 'skew_raw']), f(fs.loc['fire_cnt_up45_r300_all', 'skew_log1p']), f"{f(fs.loc['fire_cnt_up45_r300_all','share_zero_days_pct'],1)}% zero days"],
       ["India-origin fires in the cone", f(fs.loc['fire_cnt_up45_r300_in', 'skew_raw']), f(fs.loc['fire_cnt_up45_r300_in', 'skew_log1p']), f"{f(fs.loc['fire_cnt_up45_r300_in','share_zero_days_pct'],1)}% zero days"],
       ["Fires within 300 km, no cone", f(fs.loc['fire_cnt_r300_all', 'skew_raw']), f(fs.loc['fire_cnt_r300_all', 'skew_log1p']), f"{f(fs.loc['fire_cnt_r300_all','share_zero_days_pct'],1)}% zero days"]],
      [3300, 1200, 1500, 3638],
      note="Air-quality rows exclude the 44 flagged suspect days (13–16 December 2022), so their raw skew differs slightly from Table 9, which keeps them (PM2.5 1.95 vs 1.91, PM10 1.75 vs 1.71, CO 3.18 vs 3.17).")
p("**Standardisation.** Continuous predictors and pollutants were converted to z-scores, z = (x − mean)/SD, using the **training-period** mean and SD only, "
  "after log1p where applied. One set of parameters per variable is used for all cities, so real differences between cities remain. The parameters are saved "
  "(aq_params.json, weather_zscore_params.json, fire_zscore_params.json, role2_params.json) and will be reused unchanged for 2024. Min-Max scaling was not used: "
  "with a few extreme fire and rain days it would squash almost every other day towards 0.")
p("**Target.** Composite Smog Index = 0.40·z(PM2.5) + 0.12·[z(PM10) + z(NO2) + z(SO2) + z(O3) + z(CO)], from daily means (dust excluded). "
  "A **spike** is a day whose index is at or above the 90th percentile of that city's training October–March days. Thresholds run from 0.36 (Rahim Yar Khan) to 2.18 (Lahore), "
  "giving 297 spike city-days (5.2%) in the window. A max-based label differs on 118 days (2.1%).")

h2("E. Categorical encoding")
table("Nominal variables converted to 0/1 dummy flags in the master (one category dropped as reference).",
      ["Variable", "Dummy columns", "Reference"],
      [["City (11)", "city_faisalabad … city_jalandhar (10)", "Lahore"],
       ["Country", "is_india", "Pakistan"],
       ["Border group", "near_border (Lahore, Sialkot)", "other cities"],
       ["Season", "harvest_season (Oct–Dec)", "Jan–Sep"],
       ["Month", "month_02 … month_12 (11)", "January"],
       ["Wind-from sector (8 + calm)", "wind_from_n, _ne, _e, _se, _s, _sw, _w, _nw (8)", "calm (stagnant) days"],
       ["Already binary", "stagnant, rain_day, smog_spike, suspect_day, outlier flags", "-"],
       ["Fire detections (point level)", "is_night, conf_high, conf_low (fire.ipynb)", "day, nominal"]],
      [2300, 4800, 2538])
p("The checks in the notebook confirm that every row belongs to at most one category of each variable, that Lahore rows have all city dummies at 0, and that the eight "
  "wind-sector dummies are all 0 on exactly the 631 stagnant city-days. A numeric code (0 to 7 for sectors, 1 to 11 for cities) would impose a false order, so dummies are used.")

h2("F. Spatial feature engineering")
p("For each city (coordinates from the weather-file headers) the great-circle (Haversine) distance and the compass bearing to every fire within 300 km were computed once. "
  "Radius counts (50, 100, 150, 200, 300 km) are then filters. A fire is **upwind** when its bearing is within the cone half-angle (±30°, ±45°, ±60°) of the direction "
  "the daily vector-mean wind comes from, with the angle difference taken around the circle (350° and 10° are 20° apart). A ±45° **downwind** cone is kept as a placebo. "
  "On stagnant days (vector-mean wind < 2 km/h, 10.9% of training city-days) the direction is noise, so the cone keeps every fire in the radius. Every count is split by origin "
  "(fires detected in India or Pakistan), which is what lets us examine the cross-border claim, and fire radiative power (FRP, MW) is summed alongside the count. "
  "Automatic tests confirm that a north wind keeps fires to the north, that no cone holds more fires than its circle, and that wider cones hold at least as many fires as narrower ones.")
figure("figures/fig_fire_study_area.png",
       "Crop-fire detections (NASA VIIRS NOAA-20, vegetation fires, nominal or high confidence) around the 11 study cities, October–November 2023. Blue = India-origin, orange = Pakistan-origin. "
       "The circle is the 150 km radius around Lahore and the wedges are the ±30°, ±45° and ±60° upwind cones for Lahore's daily wind on 29 October 2023 (from 80°). "
       "Grey lines: Natural Earth 1:10m borders. Produced by fire.ipynb.", 5.6)
p("**Choosing the default setting (training data only).** The master carries one default cone/radius, chosen from the training harvest season as the highest median "
  "Spearman correlation between fires on day *t* and the index on day *t + 1* over the 7 Pakistani cities. The chosen setting is the ±45° upwind cone at 300 km "
  "(Section III-C). This replaces the provisional 150 km of the work plan; Person C's 150 km columns stay in the master for comparison, together with the 300 km circle and the 300 km downwind placebo.")

# =====================================================================
# III. EDA
# =====================================================================
h1("III. Exploratory Data Analysis")
p("Unless stated, statistics use the 4,323 training city-days (1,012 in October–December 2022). The validation period is only described in Milestone 3, and 2024 is never used.")
h2("A. Univariate summary statistics")
s = exact("summary_train", tab("summary_train", index_col=0))
rows = [[v, f(r['mean']), f(r['median']), f(r['sd']), f(r['iqr']), f(r['skew']), f(r['share_zero_pct'], 1)] for v, r in s.iterrows()]
table("Central tendency and spread of the key variables, training period (n = 4,323 city-days).",
      ["Variable (unit)", "Mean", "Median", "SD", "IQR", "Skew", "Zero days (%)"], rows, [3300, 1000, 1000, 1000, 1000, 1000, 1338])
p("**Resistant vs non-resistant.** For the weather variables the mean and median nearly coincide (temperature range: 11.26 vs 11.30 °C, skew 0.02), so mean and SD describe them well. "
  "Pollutants are moderately right-skewed (PM2.5 mean 54.4 vs median 46.1 µg/m³), and fire counts and rain are zero-inflated and extremely skewed. Fires in the cone have a mean of 43.3 but a median of 4. "
  "India-origin fires in the cone have a median of 0 and are absent on 61% of days. Rain has a median of 0 mm and a mean of 2.2 mm. "
  "For these variables the median and IQR describe a typical day, the mean describes the total load, and the SD (4 to 51 times the IQR for the fire counts) is driven by a handful of days. "
  "Daily mean PM2.5 exceeds the WHO 24-hour guideline of 15 µg/m³ on 99.5% of training city-days (air_quality.ipynb). These are model estimates, so this is an indication, not an official exceedance count.")
figure("figures/fig_a1_pm25_log_transform.png",
       "Daily mean PM2.5 across the 11 cities on training days, before (a) and after (b) the log(1 + x) transform. Dashed line: mean; solid line: median. "
       "The raw values have a long right tail (mean above median); after the transform mean and median nearly coincide. Produced by air_quality.ipynb (flagged December days left out).", 6.0)

h2("B. Outlier diagnostic")
o = exact("outlier_audit_train", tab("outlier_audit_train", index_col=0))
rows = [[v, int(r['z_outliers']), int(r['iqr_outliers']), f(r['iqr_pct'], 1), int(r['z_new_after_removal (masking)']), f(r['sd_all']), f(r['sd_without_iqr_outliers']), f(r['sd_inflation_pct'], 0)]
        for v, r in o.iterrows()]
table("Outliers by the z-score rule (|z| > 3) and the quartile rule (beyond Q1 − 1.5·IQR or Q3 + 1.5·IQR), training period. "
      "'Masked' = additional points the z-rule flags once the first-pass z-outliers are removed. SD inflation = SD with all days relative to SD without the IQR outliers.",
      ["Variable (unit)", "z-rule", "IQR rule", "IQR %", "Masked", "SD all", "SD w/o IQR outl.", "SD inflation %"], rows,
      [2900, 800, 900, 800, 900, 1000, 1200, 1138], font=8)
p("**Masking.** The IQR rule flags far more days than the z-rule in every skewed variable (rain 823 vs 89; fires in the cone 534 vs 63; PM2.5 292 vs 96). "
  "The extreme days inflate the SD, which widens the 3-SD limit and hides other extreme days. Removing the first-pass z-outliers and applying the rule again finds 144 more rain days, 101 more fire days and 63 more PM2.5 days. "
  "**Variance inflation.** Without the IQR outliers the SD of rain falls from 6.26 to 0.43 mm and that of fires in the cone from 177 to 14.6. For zero-inflated variables the SD is mostly made of the outliers, so the z-rule is a weak detector there. "
  "On the log scale fires in the cone have no IQR outliers at all, which supports modelling on the log scale. "
  "**Decision.** No outlier was deleted, winsorised or capped. They are real smog episodes, storms and fire outbreaks, the events the project predicts. Each stream carries 0/1 flag columns instead "
  "(…_iqr_outlier for AQ, …_outlier_z / _iqr for weather, out_z_ / out_iqr_ for fire).")

h2("C. Bivariate and multivariate exploration")
h3("1. When do spikes happen? Group-by and contingency tables")
mo = tab("groupby_month", index_col=0)
se = tab("groupby_season", index_col=0)
st = tab("groupby_stagnant", index_col=0)
ra = tab("groupby_rain", index_col=0)
co = tab("groupby_country", index_col=0)
rows = []
for name, t in [("Season", se), ("Wind", st), ("Rain", ra), ("Country", co)]:
    for k, r in t.iterrows():
        rows.append([name, k, f"{int(r['city_days']):,}", f(r['mean_index']), f(r['median_index']), f(r['spike_share_pct'], 1)])
table("Mean Composite Smog Index and share of spike days by group, training period.",
      ["Grouping", "Group", "City-days", "Mean index", "Median index", "Spike days (%)"], rows, [1300, 2600, 1300, 1400, 1500, 1538])
p(f"By month, spikes are concentrated in **December ({f(mo.loc[12,'spike_share_pct'],1)}% of city-days) and January ({f(mo.loc[1,'spike_share_pct'],1)}%)**, against "
  f"{f(mo.loc[10,'spike_share_pct'],1)}% in October and {f(mo.loc[11,'spike_share_pct'],1)}% in November, while fires in the cone peak in October and November (57,087 and 50,062 detections in training). "
  "The second burning season, the wheat harvest of May 2023 (30,235 cone detections), produced **no** spike. Fires alone do not make a spike: the smoke must be trapped by winter weather (Figures 3 and 4). "
  "The spike label is defined on October–March, so it captures mainly the December–January fog-season episodes. This motivates the interaction hypothesis H3, and Milestone 3 will also model the continuous index, which rises from October.")
figure("figures/fig_a3_index_over_time.png",
       "Composite Smog Index over time (7-day centred average) for Lahore, Faisalabad, Rahim Yar Khan and Amritsar (Indian Punjab), 4 August 2022 to 31 December 2023. "
       "The index has no unit (0 = average training day). Grey bands mark October–December; the dashed and dotted lines mark the end of training and the start of validation. "
       "The break in December 2022 is the flagged suspect days. Produced by air_quality.ipynb.", 6.3)
figure("figures/fig_fire_monthly_by_origin.png",
       "Monthly crop-fire detections inside the study area (26–37°N, 68–79°E) by country of origin, January 2022 to December 2023 (UTC+5 dates). "
       "Shaded bands mark the April–May wheat and October–November rice residue-burning seasons. Produced by fire.ipynb.", 6.0)
cs = tab("contingency_stagnant", index_col=0)
cf = tab("contingency_fire_in_cone", index_col=0)
rows = [[k, int(r.iloc[0]), int(r.iloc[1]), f(r['spike_rate_pct'], 1)] for k, r in cs.iterrows()] + \
       [[k, int(r.iloc[0]), int(r.iloc[1]), f(r['spike_rate_pct'], 1)] for k, r in cf.iterrows()]
table("Contingency tables, training harvest season: today's condition vs a spike tomorrow (target_spike_h1). "
      "Stagnant: χ² = 24.4, odds ratio 3.61 (95% CI 2.15–6.06). At least one fire in the cone: χ² = 8.3, odds ratio 5.11 (1.60–16.37). "
      "Consecutive days of a city are not independent, so the p-values (< 0.01) overstate certainty; the tables describe association.",
      ["Today", "No spike tomorrow", "Spike tomorrow", "Spike rate (%)"], rows, [3800, 1900, 1900, 2038])

h3("2. Correlation structure")
figure("figures/fig_m2_correlation_harvest.png",
       "Spearman rank correlations between the next-day Composite Smog Index, today's index, fire counts (±45° upwind cone at 300 km, split by origin, and the plain 300 km circle) "
       "and daily weather on the 1,012 training harvest city-days. Temperature range = daily max − min (°C); rain = daily total (mm); wind speed = mean of hourly speeds; "
       "vector-mean wind = length of the averaged wind vector (km/h); stagnant = vector-mean wind < 2 km/h. Diverging blue–red scale centred on 0. Produced by merge_analysis.ipynb.", 5.6)
p("Today's index is by far the strongest single correlate of tomorrow's (ρ = 0.82), which makes persistence the baseline every model must beat. "
  "Among the predictors, wind speed (−0.38), humidity (0.32), vector-mean wind (−0.31), temperature range (0.30), rain (−0.29) and fires in the upwind cone (0.34) are related to the next-day index. "
  "The plain 300 km circle is weaker (0.19). Wind speed and vector-mean wind are nearly redundant (0.85), as are mean, minimum and maximum temperature in the weather table (r = 0.91–0.98), "
  "so models will use one of each pair. Fires in the cone are higher on stagnant days (0.32) because on those days the cone keeps every fire in the circle. This is why the fire × stagnation interaction (H3) is tested explicitly.")

h3("3. Cone and radius sensitivity (instructor's request)")
figure("figures/fig_m1_cone_radius_sensitivity.png",
       "Median Spearman correlation between the fire count on day t (all origins) and the Composite Smog Index on day t + 1, for every cone and radius. Correlations are computed inside each city and the median over the group is shown. "
       "Top: training harvest season (92 days per city), used to choose the setting (black box). Bottom: full training year (393 days per city), where the shared seasonal cycle inflates every setting, including the downwind placebo. "
       "Near border = Lahore, Sialkot; Far = Multan, Rahim Yar Khan, Islamabad, Rawalpindi. Produced by merge_analysis.ipynb.", 6.5)
cvr = exact("cone_vs_radius", tab("cone_vs_radius", index_col=[0, 1])).reset_index()
rows = [[r['period'].replace(' (headline)', ''), r['group'], f(r.iloc[2]), f(r.iloc[3]), f(r.iloc[4]), f(r.iloc[5]), f(r.iloc[6])] for _, r in cvr.iterrows()]
table("Median Spearman ρ (fires on day t vs index on day t + 1) at 300 km: chosen cone, plain circle, downwind placebo and the other two angles.",
      ["Period", "City group", "Upwind ±45°", "No cone", "Downwind ±45°", "Upwind ±30°", "Upwind ±60°"], rows,
      [2300, 1800, 1100, 1000, 1200, 1100, 1138])
p("**Findings.** (i) In the harvest season the cone matters more than the circle. At 300 km the ±45° upwind cone gives a median ρ of 0.23 (positive in all 7 Pakistani cities), the plain circle −0.06 and the downwind placebo 0.01. "
  "A large circle counts as many fires downwind as upwind and so carries no signal. (ii) Inside the cone, ρ grows with the radius (about 0 at 50 km to 0.23 at 300 km): the smoke that matters is regional. "
  "(iii) At **30° and 60°** the results are close (0.19 and 0.20 over all 7 cities). The near-border cities favour the narrow ±30° cone (0.28) and the far cities the wide ±60° cone (0.32), where the wind direction is less certain along a longer path. "
  "With 92 days per city a correlation has a standard error of about 0.10, so the angle choice is within noise; ±45° is the middle setting. "
  "(iv) Over the full training year every setting looks good (0.19–0.35), **including the placebo**. Pooled-year correlations mostly measure the shared season, which is why the selection used the harvest season only. "
  "(v) For Indian Punjab cities the cone adds little (0.06): fires burn all around them.")
figure("figures/fig_m3_lagged_fire.png",
       "Spearman correlation between the fire count k days earlier (k = 0 to 3) and the Composite Smog Index of the day, median over the 7 Pakistani cities (lines), with the range across cities shaded for the upwind cone; training harvest season. Produced by merge_analysis.ipynb.", 5.4)
p("The upwind-cone count is most related to smog **one day later** (median ρ = 0.24, against 0.16 on the same day, 0.11 after two days and 0.05 after three). The 0.24 differs from the 0.23 in Table 13 only because the 92-day window is set on the smog day here and on the fire day there. The plain circle and the placebo stay near zero at every lag. "
  "At the median vector-mean wind of about 5 km/h, smoke covers roughly 120 km a day, so fires 100–300 km upwind arrive after one to two days. This supports lags of 1–3 days and a 1-day-ahead horizon as the most predictable.")

h3("4. Weather traps")
tr = tab("weather_trap_harvest", index_col=0)
rows = [[k, int(r['days_with']), f(r['spike_rate_with_pct'], 1), f"{f(r['ci95_low_pct'],1)}–{f(r['ci95_high_pct'],1)}", f(r['spike_rate_without_pct'], 1),
         ("–" if pd.isna(r['risk_ratio']) else f(r['risk_ratio']))] for k, r in tr.iterrows()]
table("Next-day spike rate after each weather condition vs all other days, training harvest season (1,012 city-days). Cut-offs are training-period quartiles pooled over the 11 cities (role2_params.json).",
      ["Condition on day t", "Days", "Spike rate next day (%)", "95% CI (Wilson)", "Other days (%)", "Risk ratio"], rows,
      [3600, 800, 1500, 1400, 1200, 1138])
figure("figures/fig_m6_weather_trap.png",
       "Share of next days that are smog spikes when today has each weather condition (filled circles, 95% Wilson intervals) and on all other days (hollow diamonds), training harvest season. "
       "Dashed line: rate over all harvest days (11.0%). n = city-days with the condition. Produced by merge_analysis.ipynb.", 6.4)
p("Stagnant days are followed by a spike 27.3% of the time (9.4% otherwise) and humid days 22.0% (8.5%). No rain day was followed by a spike (0 of 72). "
  "When stagnation, no rain and high humidity coincide, 45% of next days are spikes (9 of 20), a risk ratio of 4.4. "
  "**The temperature-range proxy points the other way from the work plan.** None of the 61 small-range days was followed by a spike, while large-range days (> 13.6 °C) were followed by 15.4% (risk ratio 1.77). "
  "A small day–night range indicates cloud or rain, which mix and wash out the air. Surface inversions form on clear, calm nights with strong radiative cooling, which produce a large range. "
  "We therefore use a **large** temperature range as the inversion proxy in H2. On stagnant harvest days mean PM2.5 is 96.4 µg/m³, against 74.3 µg/m³ on ventilated harvest days.")
figure("figures/fig_m4_index_by_weather.png",
       "Composite Smog Index on the next day by today's weather (rain day ≥ 1 mm; stagnant = vector-mean wind < 2 km/h; ventilated = other dry days) for three Pakistani cities and Amritsar, training harvest season. "
       "Boxes show median and IQR, whiskers 1.5 × IQR; n = city-days per box. Produced by merge_analysis.ipynb.", 6.0)
p("In all four cities rain days are followed by the cleanest next day (pooled median −0.06, against 0.46 after ventilated and 0.80 after stagnant dry days). "
  "After stagnant days the median next-day index is highest in Lahore (2.36 vs 1.38), Amritsar (1.63 vs 0.78) and Multan (0.91 vs 0.64), and about the same in Faisalabad. "
  "The rain and stagnant boxes hold only 2–9 days per city, so the figure describes the pattern rather than testing it.")

h3("5. Cross-border check")
xb = tab("cross_border", index_col=0)
rows = [[c, r['group'].replace(' (PK)', ''), f"{int(r['IN_fires']):,}", int(r['IN_fire_days']), f(r['rho_IN_next_day']),
         f"{int(r['PK_fires']):,}", int(r['PK_fire_days']), f(r['rho_PK_next_day']),
         ("yes" if str(r['can_test_cross_border']) == "True" else "no" if str(r['can_test_cross_border']) == "False" else "n/a")] for c, r in xb.iterrows()]
table("Fires in each city's ±45° upwind cone (300 km) by origin, training harvest season (92 days): totals, days with at least one fire, and Spearman ρ with the next-day index. "
      "A Pakistani city can test the cross-border claim if India-origin fires reach its cone on at least 20 days.",
      ["City", "Group", "IN fires", "IN days", "ρ IN", "PK fires", "PK days", "ρ PK", "Can test"], rows,
      [1500, 1300, 1000, 800, 800, 1000, 800, 800, 1638], font=8)
figure("figures/fig_m5_cross_border.png",
       "Spearman correlation between the number of fires inside each city's upwind cone (300 km) on day t and the next-day index, by origin (circles: India; squares: Pakistan), training harvest season. "
       "Marker area grows with the number of days with at least one such fire; hollow markers mark fewer than 20 days (cannot test). Produced by merge_analysis.ipynb.", 6.2)
p("Only Lahore (54 days with India-origin fires in the cone), Sialkot (45) and Faisalabad (40) can test the cross-border claim. In Sialkot India-origin fires go with higher next-day smog (ρ = 0.33, against 0.10 for Pakistan-origin fires). "
  "In Lahore it is the other way round (−0.04 vs 0.23), although 70% of the fires in Lahore's cone are Indian. In Multan, Rahim Yar Khan, Islamabad and Rawalpindi India-origin fires reach the cone on 1 to 18 days only, "
  "so for them only Pakistan-origin fires can be studied. The cross-border signal is therefore mixed and rests on one season; H4 tests it with controls. For the Indian cities the question is reversed: "
  "Pakistan-origin smoke shows a positive association in Ferozepur (0.30) and Amritsar (0.19).")

h3("6. Robustness of the index weights")
w = tab("weight_check_train", index_col=0)
rows = [[k, f(r['spearman_with_main'], 3), int(r['spike_days']), int(r['labels_changed']), f(r['main_spikes_kept_pct'], 1)] for k, r in w.iterrows()]
table("Index rebuilt with other weights on the 4,323 training days (spike thresholds re-learned on training October–March for each version).",
      ["Index version", "Spearman with main", "Spike days", "Labels changed", "Main spikes kept (%)"], rows, [3600, 1600, 1300, 1500, 1638],
      note="For all four versions the thresholds here are re-learned on every training October–March day, including the 44 flagged suspect days. "
           "Person A's thresholds, used for the master label, leave those days out, so the main version has 219 spike days here and 208 in the master label (Table 11).")
p("All versions rank days almost identically (ρ ≥ 0.979). Dropping ozone changes the most labels (76) because winter ozone moves opposite to NO2. "
  "None of the conclusions above depends on these changes: they rest on the continuous index or on 200+ spike days. The main weights are kept and the ozone sensitivity is listed as a limitation.")

# =====================================================================
# IV. Hypotheses
# =====================================================================
h1("IV. Hypotheses and Analytical Plan")
p("Each hypothesis starts from a pattern in Section III. The response is always defined on day t + 1 (t + 1 to t + 3 for H5), using only information known on day t. "
  "Models are fitted on the training period, compared on validation in Milestone 3, and re-run on 2024 in Week 14. No target score is set.")
hm = tab("hypothesis_mapping", index_col=0)
table("Formal hypotheses (H0 = null, H1 = alternative) and the SDG targets they inform.",
      ["ID (owner)", "H0", "H1", "SDG"],
      [["H1 Cone vs radius (C)", "Adding the upwind-cone fire count to a model that already has the plain 300 km count and the controls does not improve the explanation of the next-day index: β_cone = 0 (ΔR² = 0).",
        "The upwind-cone count is positively associated with the next-day index beyond the plain radius count: β_cone > 0.", "11.6, 13"],
       ["H2 Weather trap (B)", "Stagnation, humidity, absence of rain and a large temperature range do not change the odds of a next-day spike: OR = 1 for each.",
        "Stagnant, humid, rain-free and large-range (clear-night inversion) days raise the odds of a next-day spike: OR > 1.", "3.9, 11.6"],
       ["H3 Fire × stagnation (A)", "The fire effect on the next-day index is the same on stagnant and ventilated days: β_fire×stagnant = 0.",
        "The fire effect is stronger on stagnant days: β_fire×stagnant > 0.", "3.9, 13.1"],
       ["H4 Cross-border (C)", "In Pakistani cities the India-origin upwind fire count is not associated with the next-day index once Pakistan-origin fires and weather are controlled for, and the association is the same in near-border and far cities: β_IN = 0 and β_IN×near = 0.",
        "India-origin upwind fires raise next-day smog in the near-border cities (Lahore, Sialkot) more than in far cities: β_IN + β_IN×near > 0 and β_IN×near > 0.", "13, 17, 11.6"],
       ["H5 Forecast value (A)", "A model with the fire and weather features does not beat the persistence baseline or a weather-only model on validation: ΔPR-AUC ≤ 0 and ΔMAE ≥ 0.",
        "The full model beats both baselines on validation (higher PR-AUC and ROC-AUC, lower Brier score and MAE) for at least one horizon of 1 to 3 days.", "3.d, 3.9"]],
      [1500, 3500, 3200, 1438])
# harvest_season is left out of the controls: it equals month_10 + month_11 + month_12, so next to the month dummies
# it is perfectly collinear. H4 uses Pakistani cities only, so only the 6 Pakistani city dummies vary there.
hm["controls"] = hm["controls"].str.replace("harvest_season, ", "", regex=False).str.replace("month_*, city_*,", "month_02..month_12, city_* (10),", regex=False)
hm.loc["H4", "controls"] = hm.loc["H4", "controls"].replace("city_* (10)", "city_* (6 Pakistani)")
rows = [[i, r['Y'], r['X'], r['controls'], r['test']] for i, r in hm.iterrows()]
table("Variable mapping: every name is a column (or column family) of master_daily.parquet, checked in the notebook (merge_analysis.ipynb, Hypotheses).",
      ["ID", "Response (Y)", "Main predictors (X)", "Controls / confounders", "Planned test"], rows,
      [450, 1500, 2900, 2700, 2088], font=7.5)
p("**Analytical plan.** Consecutive days of a city are correlated, and Islamabad and Rawalpindi share AQ values, so H1–H4 use regression with city-clustered standard errors "
  "or a block bootstrap, not plain standard errors. Logistic regression is used for the spike label and OLS for the index. Interaction terms test H3 and H4. "
  "Non-linear effects will be checked with gradient-boosted trees and permutation importance. For H5, models are compared on the validation season (1,309 city-days, 1,012 of them in October–December 2023) against two baselines: persistence "
  "(persist_index, persist_spike) and a weather-only model. Spikes are rare (5.2%), so we report PR-AUC, recall and precision as well as ROC-AUC and the Brier score, and MAE for the index. "
  "In Week 14 the same code is rerun with the date window extended: retrain with the first half of 2024 added, then test on the second half.")
p("**Open modelling question raised by the EDA.** The spike label falls mostly in December–January, after the burning peak. Milestone 3 will therefore report results for the continuous index alongside the label. "
  "It will also compare a label with thresholds learned within each month, so that a null fire effect cannot be an artefact of the label's timing.")

# =====================================================================
# V. Limitations and reproducibility
# =====================================================================
h1("V. Limitations")
bullets(["**Air quality is model output.** Open-Meteo air quality is CAMS global model output on a coarse grid, not monitor data. Neighbouring cities can share values (Islamabad = Rawalpindi), and a 4-day source error (13–16 December 2022) is flagged but kept.",
         "**One training winter.** Every learned threshold, scaling parameter and the cone selection rest on one harvest season (92 days per city). Differences in ρ of about 0.1 are within noise.",
         "**No pressure and no direct inversion measure.** Surface pressure was not in the exported files and was dropped for this milestone. Temperature range and stagnation are proxies.",
         "**Satellite fire detection.** VIIRS misses fires under thick cloud or fog (common on smoggy days) and between its two daily passes; counts are detections, not fires.",
         "**City-centre approximation.** Each city is one point. The cone uses the city's daily mean wind, while smoke may follow a curved path over 300 km.",
         "**One clock.** UTC+5 is used for the Indian cities as well (IST is UTC+5:30).",
         "**Observed vs forecast weather.** Observed daily weather stands in for the forecast weather an operational system would use.",
         "**Dependence.** City-days are not independent (multi-day episodes, shared regional weather), so group comparisons and contingency p-values are descriptive."])
h1("VI. Reproducibility")
p("Code: GitHub repository (private), notebooks run top to bottom with Restart and Run All, in this order: air_quality.ipynb (A), weather.ipynb (B), fire.ipynb (C), merge_analysis.ipynb (Role 2). "
  "Shared settings, file names, city coordinates and dates are in src/config.py; merge and EDA functions in src/merge.py and src/eda.py; one figure style in src/plotting.py. "
  "Outputs: Dataset/clean/master_daily.parquet, master_data_dictionary.csv, the parameter files, figures/ and docs/tables/. Every removal of data is logged with row counts in DECISIONS.md.")
h1("References")
refs = ["Hersbach, H., et al. (2020). The ERA5 global reanalysis. Quarterly Journal of the Royal Meteorological Society, 146(730), 1999–2049.",
        "Inness, A., et al. (2019). The CAMS reanalysis of atmospheric composition. Atmospheric Chemistry and Physics, 19, 3515–3556.",
        "NASA (2024). Fire Information for Resource Management System (FIRMS), VIIRS 375 m active fire product. https://firms.modaps.eosdis.nasa.gov",
        "Okabe, M., & Ito, K. (2008). Color Universal Design (CUD): How to make figures and presentations that are friendly to colorblind people. https://jfly.uni-koeln.de/color/",
        "Schroeder, W., Oliva, P., Giglio, L., & Csiszar, I. A. (2014). The New VIIRS 375 m active fire detection data product: Algorithm description and initial assessment. Remote Sensing of Environment, 143, 85–96.",
        "Tukey, J. W. (1977). Exploratory Data Analysis. Addison-Wesley.",
        "Wickham, H. (2010). A layered grammar of graphics. Journal of Computational and Graphical Statistics, 19(1), 3–28.",
        "Wilson, E. B. (1927). Probable inference, the law of succession, and statistical inference. Journal of the American Statistical Association, 22(158), 209–212.",
        "World Health Organization (2021). WHO global air quality guidelines: particulate matter (PM2.5 and PM10), ozone, nitrogen dioxide, sulfur dioxide and carbon monoxide. Geneva: WHO.",
        "Zippenfenig, P. (2023). Open-Meteo.com Weather API [Computer software]. Zenodo. https://doi.org/10.5281/zenodo.7970649"]
blocks.append({"t": "refs", "items": refs})

OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps({"blocks": blocks}, ensure_ascii=False, indent=1))
print(f"{OUT}: {len(blocks)} blocks, {counters['table']} tables, {counters['figure']} figures")
