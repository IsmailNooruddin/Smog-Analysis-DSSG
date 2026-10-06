"""Builds the Milestone 2 report (Sections 1-6) as a JSON content model.

Tables are read from docs/tables/*.csv, which merge_analysis.ipynb writes, so the numbers in
the report are the numbers the notebook printed. render_docx.js turns the JSON into Word, in the
layout of the team's stream reports (Report_Weather.docx).

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


def p(text):
    """Paragraph; **bold** and *italic* are rendered."""
    blocks.append({"t": "p", "text": text})


def bullets(items):
    blocks.append({"t": "bullets", "items": items})


def table(caption, header, rows, widths, note=None, font=8):
    counters["table"] += 1
    blocks.append({"t": "table", "caption": f"**Table {counters['table']}.** {caption}", "header": header,
                   "rows": [[str(c) for c in r] for r in rows], "widths": widths, "note": note, "font": font})
    return counters["table"]


def figure(path, caption, width_in=6.0):
    counters["figure"] += 1
    blocks.append({"t": "figure", "path": str(ROOT / path), "caption": f"**Figure {counters['figure']}.** {caption}",
                   "width_in": width_in})
    return counters["figure"]


def f(x, d=2):
    out = f"{x:,.{d}f}"
    return out[1:] if out.startswith("-") and float(out) == 0 else out    # no "-0.00"


# Tables written by merge_analysis.ipynb
ov = tab("master_overview", index_col=0)["value"]
sp = tab("split_counts", index_col=0)
fs = tab("fire_setting_skew", index_col=0)
s = tab("summary_train", index_col=0)
o = tab("outlier_audit_train", index_col=0)
mo = tab("groupby_month", index_col=0)
cs = tab("contingency_stagnant", index_col=0)
cvr = tab("cone_vs_radius", index_col=[0, 1])
lag = tab("lagged_fire_correlation")
tr = tab("weather_trap_harvest", index_col=0)
xb = tab("cross_border", index_col=0)
w = tab("weight_check_train", index_col=0)
hm = tab("hypothesis_mapping", index_col=0)
HEAD = "Training Oct-Dec (headline)"
up_lag = lag[lag["setting"].str.startswith("Upwind")].set_index("lag_days")["median_rho"]

# =====================================================================
# Front matter
# =====================================================================
blocks.append({"t": "title", "text": "Crop Fires, Weather Traps and Smog across Punjab: Data Preparation and Exploratory Analysis"})
blocks.append({"t": "subtitle", "text": "Trans-Boundary Smog Prediction: Milestone 02, Draft Sections II and III, Merged Master Dataset"})
blocks.append({"t": "authors", "text": "Munir Tariq (10067)  |  Ismail Nooruddin (09958)  |  Bilal Ayub (09716)  |  "
                                         "Data Science for Social Good, Habib University  |  October 2026"})

h2("Abstract")
p("Every winter, smoke from crop-residue burning and city emissions is trapped over the Punjab plain shared by Pakistan and India. "
  "This report describes how three independent data streams were cleaned and merged into one master dataset, and what the first analysis of that dataset shows. "
  "Hourly Open-Meteo air quality (CAMS model output), hourly Open-Meteo weather and 1.28 million NASA VIIRS fire detections were aligned to one UTC+5 clock "
  "and joined one-to-one into a table of 5,665 city-days (11 cities, 4 August 2022 to 31 December 2023) and 287 columns, with no missing predictor value. "
  "The target is a Composite Smog Index built from six standardised pollutants, with a city-specific spike label. "
  "On the training period, four results stand out. First, fires inside a ±45° upwind cone within 300 km track next-day smog "
  "(median Spearman ρ = 0.23 over the Pakistani cities in the harvest season), while a plain 300 km circle (−0.06) and a downwind placebo cone (0.01) do not. "
  "Second, the association is strongest one day after the fires. Third, stagnant and humid days roughly triple the next-day spike rate, and no rain day was followed by a spike. "
  "Fourth, spikes occur mainly in December and January, after the October–November burning peak, so fires alone do not make a spike: the weather must trap the smoke. "
  "Five formal hypotheses, mapped to columns of the master dataset, set up the modelling in Milestone 3.")

# =====================================================================
# 1. Project alignment
# =====================================================================
h1("1. Project Alignment and Master Dataset Overview")
p("The project predicts hazardous smog spikes in Pakistani Punjab cities one to three days in advance from upwind crop-fire detections and from weather "
  "conditions that trap pollution. **Research question:** which fire and weather predictors, available on day *t*, explain Composite Smog Index spikes "
  "on days *t* + 1 to *t* + 3, and how much better than a persistence baseline and a weather-only baseline can they forecast those spikes? "
  "The work supports SDG 3 (targets 3.9 and 3.d: illness from air pollution and early warning), SDG 11 (target 11.6: urban air quality) and SDG 13 "
  "(regional climate action); the cross-border analysis also relates to SDG 17 (cooperation between countries). "
  "Following the instructor's feedback, the proposal's fixed target score (ROC-AUC above 0.88) has been dropped: the aim is to identify sound predictors and report the best honest performance.")
table("Team members, disciplinary background and Milestone 2 roles.",
      ["Member", "ID", "Background", "Role 1 (own data stream)", "Role 2 (merged data)"],
      [["Munir Tariq", "10067", "Computer Science (minor: Social Development and Policy)", "Person B: weather and wind",
        "Leads the merge; master overview, summary tables, correlations, weather traps"],
       ["Ismail Nooruddin", "09958", "Computer Science", "Person A: air quality and target",
        "Group-by and contingency tables, index figure, index weight check"],
       ["Bilal Ayub", "09716", "Computer Science", "Person C: NASA VIIRS fire",
        "Cone and radius sensitivity, cross-border check"]],
      [1500, 650, 2400, 2000, 3242])
table("Overview of the master analytical dataset (Dataset/clean/master_daily.parquet; first sheet of the submitted workbook).",
      ["Item", "Description"],
      [["Size", f"{ov['Rows (observations)']} rows × {ov['Columns (variables)']} columns; no missing value in any predictor"],
       ["Observational unit", "1 row = 1 city on 1 local (UTC+5) day; keys: city, country, date"],
       ["Cities (11)", "Pakistan: Lahore, Faisalabad, Multan, Rawalpindi, Sialkot, Rahim Yar Khan, Islamabad. Indian Punjab: Amritsar, Ferozepur, Ludhiana, Jalandhar"],
       ["Period and split", f"{ov['Period']}. Training 4 Aug 2022 to 31 Aug 2023 ({sp.loc['train', 'rows']:,} city-days); "
                            f"3-day gap; validation 4 Sep to 31 Dec 2023 ({sp.loc['validation', 'rows']:,} city-days)"],
       ["Sources (3)", "Open-Meteo Air Quality API, hourly, CAMS model output (Person A); Open-Meteo Historical Weather API, hourly, reanalysis-based (Person B); "
                       "NASA FIRMS archive, VIIRS 375 m active fires from NOAA-20, point detections (Person C)"],
       ["Columns by origin", "Air quality 52; weather 58; fire 128; keys, targets, lags, baselines, dummies and split built in the merge 49"],
       ["Targets", "Composite Smog Index and spike label on days t+1, t+2 and t+3 (target_index_h1..h3, target_spike_h1..h3)"],
       ["Sealed data", "All 2024 files, kept for the final out-of-time test and never read in this milestone"]],
      [2200, 7592])

# =====================================================================
# 2. Data and preprocessing
# =====================================================================
h1("2. Data and Preprocessing (Draft Section II)")
h2("2.1 Collection audit")
p("Each stream was collected and cleaned by one team member in its own notebook, then handed over as a clean daily table with its saved settings (Table 3). "
  "Air quality and weather were exported per city centre from Open-Meteo as hourly files in GMT. Both are gridded model estimates rather than station readings, "
  "so they suit comparisons between days and cities. Fire detections were downloaded from the NASA FIRMS archive as one file per country and year.")
table("Raw data collected for each stream and the main audit findings.",
      ["Stream", "Collection", "Raw records", "Audit findings"],
      [["Air quality (A)", "Open-Meteo Air Quality API; 11 city files (10 CSV, Ludhiana XLSX), hourly, GMT; CAMS model output on a grid of about 0.4°",
        "453,192 hourly rows", "No duplicate or skipped hours. No pollutant value before 4 Aug 2022 in any city. Islamabad and Rawalpindi identical (same grid cell)."],
       ["Weather (B)", "Open-Meteo Historical Weather API; 11 city files (10 CSV, Ludhiana XLSX), hourly, GMT",
        "433,728 hourly rows", "No missing value, duplicate or skipped hour. No surface-pressure column in the export."],
       ["Fire (C)", "NASA FIRMS archive; VIIRS 375 m (NOAA-20); 4 files (India and Pakistan, 2022 and 2023); 2024 files sealed",
        "1,284,773 detections", "No duplicates; one satellite; times in UTC; acquisition time read as text to keep leading zeros."]],
      [1300, 3500, 1500, 3492])

h2("2.2 Alignment, reshaping and merge")
p("All raw times are in GMT. Each stream added 5 hours to the full timestamp **before** taking the calendar date, so that evening hours fall on the correct local day "
  "(26,626 fire detections moved to the next date). The same UTC+5 clock was used for the Indian cities so that all streams share day boundaries. "
  "The reshaping steps were: stacking the 11 city files of each stream (concat); aggregating hourly rows to one row per city-day (group-by with mean, maximum, total and "
  "vector-mean rules); building a long table of fire counts for every city, cone, radius and origin (602,250 rows) and pivoting the chosen settings into columns; "
  "and joining the three streams. City names come from one shared dictionary, so the keys are spelled identically in every table.")
p("The merge started from an empty calendar of 11 cities × 515 days (5,665 rows), so that a missing day in any stream would remain visible. "
  "Air quality, weather and fire were then left-joined on city, country and date with a one-to-one check; the row count stayed at 5,665 after every join and every row "
  "found a partner. Lags of 1 to 3 days and the targets for days t+1 to t+3 were computed **within each city**, so that the last days of one city cannot leak into the "
  "first days of the next. Table 4 traces every row from the raw files to the master table.")
table("Row bookkeeping from the raw files to the master table (each step is logged in the workbook sheet Decisions_Log).",
      ["Stream", "Steps and row counts"],
      [["Air quality", "453,192 hourly rows → 191,153 in 2022–2023 → 135,905 after removing the empty Jan–Aug 2022 block → 5,665 city-days (each with ≥ 18 valid hours)"],
       ["Weather", "433,728 hourly rows → 188,393 in 2022–2023 → 7,852 city-days → 5,665 in the modelling window"],
       ["Fire", "1,284,773 detections → 287,323 in the study box (26–37°N, 68–79°E) → 279,968 vegetation fires → 238,796 with nominal or high confidence "
                "→ 238,756 on 2022–2023 local dates → 8,030 city-days (days without fires = 0) → 5,665 in the window"],
       ["Master", "calendar 5,665 → air-quality join 5,665 → weather join 5,665 → fire join 5,665 (all rows matched); 287 columns"]],
      [1300, 8492])

h2("2.3 Missing data and selection bias")
mis = tab("master_missing_all_columns", index_col=0)
complete = int((mis["missing_count"] == 0).sum())
table("Missing values by stage (counts and percentages for all 287 columns are in the workbook sheet Missing_All_Columns).",
      ["Where", "What is missing", "Count (%)", "Decision"],
      [["Air quality, raw 2022–2023", "All pollutants, one continuous block from 6 Jan to 4 Aug 2022, same hours in every city", "55,248 of 191,153 hourly rows (28.9%)",
        "Not imputed; the modelling window starts on 4 Aug 2022 for all streams"],
       ["Weather, raw", "Any variable", "0 of 433,728 rows", "Nothing to impute"],
       ["Fire, daily grid", "Days without any detection", "–", "Coded 0 (a real zero), never missing"],
       ["Master, predictors", f"Any of the {complete} key, predictor and dummy columns", "0", "–"],
       ["Master, targets and lags", "Targets for days t+1 to t+3; index lags 1 to 3", "11 / 22 / 33 rows (0.19% / 0.39% / 0.58%)",
        "Target day in sealed 2024, or lag day before 4 Aug 2022: left missing and excluded per horizon"]],
      [1700, 3000, 2000, 3092])
p("**Why no imputation.** The air-quality gap is not random: the source has no pollutant values before August 2022 in any city. Filling seven months by interpolation "
  "would invent the seasonal pattern the model must learn, so those rows were removed from every stream (listwise deletion of the block). "
  f"In total {complete} of the 287 master columns have no missing value.")
p("**Selection bias.** (i) The training period contains only **one** harvest season (October–December 2022), so every seasonal estimate rests on one winter; the final "
  "test therefore retrains with the first half of 2024 and tests on the second half. (ii) On 13–16 December 2022 every pollutant is near zero in all cities at once, a likely "
  "source error. These 44 city-days are flagged (suspect_day = 1) and kept as rows: removing them would break each city's unbroken daily calendar, which the lags and targets "
  "rely on, and the flag lets Milestone 3 drop them in one step. They are already left out of the air-quality scaling and the spike thresholds. Their effect is reported: "
  "the index has a skewness of −1.15 on training days with them and +0.26 without them. (iii) The satellite cannot see fires under thick cloud or fog, which is common on "
  "the worst smog days, so fire–smog associations are likely underestimated. (iv) Islamabad and Rawalpindi share one air-quality series, so there are 10 independent "
  "air-quality series, not 11.")

h2("2.4 Transformations, scaling and the target")
p("Variables with strong right skew were transformed with log(1 + x), which keeps zero values at zero (Table 6, Figure 1).")
table("Skewness before and after log(1 + x), training period. Air-quality rows leave out the 44 flagged days, so they differ slightly from Table 9 (PM2.5 1.91, CO 3.17 with them).",
      ["Variable", "Skew, raw", "Skew, log(1 + x)", "Note"],
      [["PM2.5 daily mean (µg/m³)", "1.95", "0.37", "10 of 13 air-quality columns had skew > 1 and were logged"],
       ["CO daily mean (µg/m³)", "3.18", "0.37", ""],
       ["Rain total (mm)", "6.46", "1.79", "61% of days have 0 mm, so the skew stays above 1"],
       ["Fires in the upwind cone, 300 km", f(fs.loc['fire_cnt_up45_r300_all', 'skew_raw']), f(fs.loc['fire_cnt_up45_r300_all', 'skew_log1p']),
        f"{f(fs.loc['fire_cnt_up45_r300_all', 'share_zero_days_pct'], 1)}% zero days"],
       ["India-origin fires in the cone", f(fs.loc['fire_cnt_up45_r300_in', 'skew_raw']), f(fs.loc['fire_cnt_up45_r300_in', 'skew_log1p']),
        f"{f(fs.loc['fire_cnt_up45_r300_in', 'share_zero_days_pct'], 1)}% zero days"]],
      [3000, 1300, 1600, 3892])
figure("figures/fig_a1_pm25_log_transform.png",
       "Daily mean PM2.5 across the 11 cities on training days, (a) before and (b) after the log(1 + x) transform; dashed line = mean, solid line = median. "
       "The long right tail disappears after the transform. Produced by air_quality.ipynb (flagged December days left out).", 5.0)
p("**Standardisation.** Continuous predictors and pollutants were converted to z-scores, z = (x − mean)/SD, after the log transform where applied, using the mean and SD of the "
  "**training period only**. One set of parameters per variable is used for all cities, so real differences between cities remain, and the parameters are saved for reuse "
  "on 2024. Min-Max scaling was not used: a few extreme fire and rain days would squeeze almost every other day towards 0.")
p("**Target.** Composite Smog Index = 0.40·z(PM2.5) + 0.12·[z(PM10) + z(NO2) + z(SO2) + z(O3) + z(CO)], computed from daily means. A **spike** is a day whose index is at or "
  "above the 90th percentile of that city's training October–March days. The thresholds run from 0.36 (Rahim Yar Khan) to 2.18 (Lahore) and give 297 spike city-days "
  "(5.2%) in the window.")

h2("2.5 Categorical encoding")
p("Nominal variables were converted into 0/1 dummy columns, with one category dropped as the reference so that a regression with an intercept stays identifiable (Table 7). "
  "A numeric code (for example 0 to 7 for wind sectors) would impose a false order. The notebook confirms that every row belongs to exactly one category of each variable "
  "and that the eight wind-sector dummies are all 0 on exactly the 631 stagnant city-days. The workbook sheet Encoding_Example shows real rows next to their dummies.")
table("Nominal variables converted to 0/1 dummy columns.",
      ["Variable", "Dummy columns", "Reference category"],
      [["City (11 categories)", "city_faisalabad … city_jalandhar (10)", "Lahore"],
       ["Country; border group", "is_india; near_border (Lahore, Sialkot)", "Pakistan; other cities"],
       ["Month (12 categories)", "month_02 … month_12 (11); harvest_season (Oct–Dec) for group summaries", "January"],
       ["Wind-from sector (8 + calm)", "wind_from_n, _ne, _e, _se, _s, _sw, _w, _nw (8)", "Calm (stagnant) days"],
       ["Already binary", "stagnant, rain_day, smog_spike, suspect_day, outlier flags", "–"]],
      [2400, 4900, 2492])

h2("2.6 Spatial fire features")
p("For each city, the great-circle distance and the compass bearing to every fire within 300 km were computed. A fire is **upwind** when its bearing lies within the cone "
  "half-angle (±30°, ±45° or ±60°) of the direction the daily wind comes from; a ±45° **downwind** cone is kept as a placebo. On stagnant days (daily vector-mean wind "
  "below 2 km/h, 10.9% of training city-days) the wind direction is unreliable, so the cone keeps every fire in the radius. Every count is split by origin (fires detected "
  "in India or in Pakistan), which makes the cross-border question testable (Figure 2). Automatic tests confirm that a north wind keeps fires to the north and that no cone "
  "holds more fires than its circle. The default setting, the ±45° upwind cone at 300 km, was chosen on the training harvest season only (Section 3.3).")
figure("figures/fig_fire_study_area.png",
       "Crop-fire detections (NASA VIIRS NOAA-20, vegetation fires, nominal or high confidence) around the 11 study cities, October–November 2023. Blue = India-origin, "
       "orange = Pakistan-origin. The circle is the 150 km radius around Lahore; the wedges are the ±30°, ±45° and ±60° upwind cones for Lahore's wind on 29 October 2023. "
       "Produced by fire.ipynb.", 4.1)

h2("2.7 Summary of preprocessing decisions")
table("Preprocessing decisions, alternatives considered and justification.",
      ["Decision", "Alternative", "Justification"],
      [["Add 5 h (UTC+5) before taking the date, for all cities", "Keep GMT dates; +5:30 for India", "Day boundaries must match across streams; one clock keeps the cross-border design consistent"],
       ["Modelling window from 4 Aug 2022", "Impute the empty air-quality block", "Seven months of invented pollution would create the pattern the model must learn"],
       ["Lags and targets within each city", "Shift the whole table", "Prevents one city's last days leaking into the next city's first days"],
       ["log(1 + x) for skewed variables", "No transform", "Removes the long right tail and keeps zeros at zero"],
       ["Z-scores from the training period, one set for all cities", "Fit on all data; one set per city", "Prevents leakage from validation and test data; keeps real city differences"],
       ["Keep outliers and add flags", "Delete, cap or winsorise", "Extreme days are the smog episodes and fire outbreaks the project studies"],
       ["Dummy columns with a reference category", "Numeric codes", "Categories are nominal; codes would imply a false order"],
       ["Upwind cone ±45° at 300 km", "Plain radius; 150 km", "Highest median correlation with next-day smog on training data; the plain circle carries no signal"]],
      [2900, 2300, 4592])

# =====================================================================
# 3. EDA
# =====================================================================
h1("3. Exploratory Data Analysis (Draft Section III)")
p(f"Unless stated otherwise, statistics use the {sp.loc['train', 'rows']:,} training city-days ({sp.loc['train', 'oct_dec_rows']:,} in October–December 2022). "
  "The validation period is not analysed until Milestone 3, and 2024 is never used. All figures have a title, axes labelled with units, a legend where several series "
  "are shown, and a colour-blind-safe palette.")

h2("3.1 Univariate analysis")
KEEP = ["Composite Smog Index (z units)", "PM2.5 daily mean (µg/m³)", "CO daily mean (µg/m³)",
        "Temperature range (°C)", "Relative humidity (%)", "Rain total (mm)", "Vector-mean wind (km/h)",
        "Fires in upwind cone, 300 km (count)", "India-origin fires in cone (count)", "Fires within 300 km, no cone (count)"]
table(f"Summary statistics of the key variables, training period (n = {sp.loc['train', 'rows']:,} city-days).",
      ["Variable (unit)", "Mean", "Median", "SD", "IQR", "Skew", "Zero days (%)"],
      [[v, f(s.loc[v, 'mean']), f(s.loc[v, 'median']), f(s.loc[v, 'sd']), f(s.loc[v, 'iqr']), f(s.loc[v, 'skew']), f(s.loc[v, 'share_zero_pct'], 1)] for v in KEEP],
      [3300, 1050, 1050, 1050, 1050, 1000, 1292])
p("**Resistant and non-resistant measures.** The weather variables are nearly symmetric (temperature range: mean 11.26 °C, median 11.30 °C, skew 0.02), so the mean and SD "
  "describe them well. The pollutants are moderately right-skewed (PM2.5 mean 54.4 µg/m³ against a median of 46.1 µg/m³). Fire counts and rain are zero-inflated and extremely skewed: "
  "fires in the cone have a mean of 43.3 but a median of 4, India-origin fires reach the cone on only 39% of days, and rain has a median of 0 mm against a mean of 2.2 mm. "
  "For these variables the median and IQR describe a typical day, while the mean describes the total load; the SD (4 to 51 times the IQR for the fire counts) is driven by a "
  "handful of days. Daily mean PM2.5 is above the WHO 24-hour guideline of 15 µg/m³ on 99.4% of training city-days outside the flagged days; as these are model estimates, "
  "this is an indication rather than an official exceedance count.")

h2("3.2 Outlier diagnostic")
table("Outliers by the z-score rule (|z| > 3) and the quartile rule (beyond Q1 − 1.5·IQR or Q3 + 1.5·IQR), training period. Masked = extra points the z-rule finds "
      "once the first-pass z-outliers are removed. SD inflation = SD of all days relative to the SD without the IQR outliers.",
      ["Variable (unit)", "z-rule", "IQR rule", "IQR (%)", "Masked", "SD, all", "SD w/o IQR outliers", "SD inflation (%)"],
      [[v, int(o.loc[v, 'z_outliers']), int(o.loc[v, 'iqr_outliers']), f(o.loc[v, 'iqr_pct'], 1), int(o.loc[v, 'z_new_after_removal (masking)']),
        f(o.loc[v, 'sd_all']), f(o.loc[v, 'sd_without_iqr_outliers']), f(o.loc[v, 'sd_inflation_pct'], 0)] for v in KEEP],
      [3000, 800, 900, 850, 850, 1000, 1250, 1142])
p("**Masking.** The quartile rule flags far more days than the z-rule in every skewed variable (rain 823 against 89; fires in the cone 534 against 63; PM2.5 292 against 96). "
  "Extreme days inflate the SD, which widens the 3-SD limit and hides other extreme days: removing the first-pass z-outliers and applying the rule again finds 144 more rain days, "
  "101 more fire days and 63 more PM2.5 days. **Variance inflation.** Without the quartile-rule outliers, the SD of rain falls from 6.26 to 0.43 mm and that of fires in the cone "
  "from 177 to 14.6, so for zero-inflated variables the SD consists mostly of the outliers. On the log scale, fires in the cone have no quartile-rule outliers at all. "
  "**Decision.** No outlier was deleted, capped or winsorised: they are real smog episodes, storms and fire outbreaks, the events the project predicts. Each stream carries "
  "0/1 flag columns instead.")

h2("3.3 Bivariate and multivariate analysis")
se = tab("groupby_season", index_col=0)
st = tab("groupby_stagnant", index_col=0)
ra = tab("groupby_rain", index_col=0)
co = tab("groupby_country", index_col=0)
rows = []
for name, t in [("Season", se), ("Wind", st), ("Rain", ra), ("Country", co)]:
    for k, r in t.iterrows():
        rows.append([name, k, f"{int(r['city_days']):,}", f(r['mean_index']), f(r['median_index']), f(r['spike_share_pct'], 1)])
p("**When do spikes happen?** Table 11 groups the training days by season, wind, rain and country. By month, spikes are concentrated in "
  f"**December ({f(mo.loc[12, 'spike_share_pct'], 1)}% of city-days) and January ({f(mo.loc[1, 'spike_share_pct'], 1)}%)**, against "
  f"{f(mo.loc[10, 'spike_share_pct'], 1)}% in October and {f(mo.loc[11, 'spike_share_pct'], 1)}% in November, while fires in the cone peak in October and November "
  "(57,087 and 50,062 detections). The wheat-burning season of May 2023 (30,235 cone detections) produced **no** spike. Fires alone therefore do not make a spike: the smoke "
  "must be trapped by winter weather (Figure 3).")
table("Mean Composite Smog Index and share of spike days by group, training period.",
      ["Grouping", "Group", "City-days", "Mean index", "Median index", "Spike days (%)"], rows, [1300, 2700, 1300, 1400, 1500, 1592])
figure("figures/fig_a3_index_over_time.png",
       "Composite Smog Index over time (7-day centred average; no unit, 0 = average training day) for Lahore, Faisalabad, Rahim Yar Khan and Amritsar, "
       "4 August 2022 to 31 December 2023. Grey bands mark October–December; dashed and dotted lines mark the end of training and the start of validation. "
       "The break in December 2022 is the flagged suspect days. Produced by air_quality.ipynb.", 5.6)
p(f"**Contingency tables.** On the training harvest days, {f(cs.loc['stagnant today', 'spike_rate_pct'], 1)}% of days after a stagnant day were spikes, against "
  f"{f(cs.loc['ventilated today', 'spike_rate_pct'], 1)}% after a ventilated day (χ² = 24.4, odds ratio 3.61, 95% CI 2.15–6.06). After a day with at least one fire in the "
  "cone, 12.0% of next days were spikes, against 2.6% after a day with none (χ² = 8.3, odds ratio 5.11, 95% CI 1.60–16.37). Consecutive days of a city are not independent, "
  "so these p-values (< 0.01) overstate certainty and the tables describe association only.")
figure("figures/fig_m2_correlation_harvest.png",
       "Spearman rank correlations between the next-day Composite Smog Index, today's index, fire counts (±45° upwind cone at 300 km, by origin, and the plain 300 km circle) "
       "and daily weather, 1,012 training harvest city-days. Temperature range = daily max − min (°C); rain = daily total (mm); vector-mean wind = length of the averaged "
       "wind vector (km/h). Diverging scale centred on 0. Produced by merge_analysis.ipynb.", 3.9)
p("**Correlations (Figure 4).** Today's index is by far the strongest correlate of tomorrow's (ρ = 0.82), which makes persistence the baseline every model must beat. "
  "Among the predictors, wind speed (−0.38), fires in the upwind cone (0.34), humidity (0.32), vector-mean wind (−0.31), temperature range (0.30) and rain (−0.29) relate to "
  "the next-day index, while the plain 300 km circle is weaker (0.19). Wind speed and vector-mean wind are nearly redundant (0.85), as are mean, minimum and maximum "
  "temperature (r = 0.91–0.98), so models will use one of each pair.")
p("**Fire cone and radius (Figure 5).** In the harvest season the cone matters more than the circle. At 300 km the ±45° upwind cone gives a median ρ of "
  f"{f(cvr.loc[(HEAD, 'All Pakistani (7)'), 'upwind cone (up45, 300 km)'])} (positive in all 7 Pakistani cities), the plain circle "
  f"{f(cvr.loc[(HEAD, 'All Pakistani (7)'), 'no cone (300 km)'])} and the downwind placebo {f(cvr.loc[(HEAD, 'All Pakistani (7)'), 'downwind placebo (down45, 300 km)'])}: "
  "a large circle counts as many fires downwind as upwind and so carries no signal. Inside the cone, ρ grows with the radius, so the smoke that matters is regional. "
  "The ±30° and ±60° cones give similar values; with 92 days per city a correlation has a standard error of about 0.10, so ±45° was kept as the middle setting. "
  "Over the full training year every 300 km setting looks good (0.16–0.35), **including the placebo**, because fires and smog share a seasonal cycle; this is why the "
  "selection used the harvest season only. The cone count is most related to smog **one day later** "
  f"(median ρ = {f(up_lag[1])}, against {f(up_lag[0])} on the same day, {f(up_lag[2])} after two days and {f(up_lag[3])} after three; the window here is set on the smog day, "
  "hence the small difference from 0.23). At the median vector-mean wind of about 5 km/h, smoke travels roughly 120 km a day, consistent with a one-to-two-day delay.")
figure("figures/fig_m1_cone_radius_sensitivity.png",
       "Median Spearman correlation between the fire count on day t and the Composite Smog Index on day t + 1, for every cone and radius, computed within each city. "
       "Top: training harvest season (92 days per city), used to choose the setting (black box). Bottom: full training year (393 days per city), where the shared seasonal "
       "cycle inflates every setting, including the placebo. Near border = Lahore, Sialkot; Far = Multan, Rahim Yar Khan, Islamabad, Rawalpindi. Produced by merge_analysis.ipynb.", 5.7)
p(f"**Weather traps (Figure 6).** Stagnant days are followed by a spike {f(tr.iloc[0]['spike_rate_with_pct'], 1)}% of the time "
  f"({f(tr.iloc[0]['spike_rate_without_pct'], 1)}% otherwise) and humid days {f(tr.iloc[1]['spike_rate_with_pct'], 1)}% "
  f"({f(tr.iloc[1]['spike_rate_without_pct'], 1)}%). No rain day was followed by a spike (0 of {int(tr.iloc[2]['days_without'])}). When stagnation, no rain and high humidity coincide, "
  f"{f(tr.iloc[5]['spike_rate_with_pct'], 0)}% of next days are spikes (9 of 20, risk ratio {f(tr.iloc[5]['risk_ratio'], 1)}). "
  "The temperature-range proxy points the other way from the work plan: none of the 61 small-range days was followed by a spike, while large-range days (> 13.6 °C) were "
  f"followed by {f(tr.iloc[3]['spike_rate_with_pct'], 1)}% (risk ratio {f(tr.iloc[3]['risk_ratio'])}). A small day–night range signals cloud or rain, which mix and wash the air, "
  "whereas surface inversions form on clear, calm nights with strong cooling, so a **large** range is used as the inversion proxy.")
figure("figures/fig_m6_weather_trap.png",
       "Share of next days that are smog spikes when today has each weather condition (filled circles, 95% Wilson intervals) and on all other days (hollow diamonds), "
       "training harvest season. Dashed line: rate over all harvest days (11.0%); n = city-days with the condition. Produced by merge_analysis.ipynb.", 5.4)
lah, sia, fai = xb.loc["Lahore"], xb.loc["Sialkot"], xb.loc["Faisalabad"]
p(f"**Cross-border check.** Only Lahore ({int(lah['IN_fire_days'])} days with India-origin fires in the cone), Sialkot ({int(sia['IN_fire_days'])}) and Faisalabad "
  f"({int(fai['IN_fire_days'])}) receive India-origin fires often enough to test the cross-border claim; in Multan, Rahim Yar Khan, Islamabad and Rawalpindi this happens on 1 to 18 days only. "
  f"In Sialkot, India-origin fires go with higher next-day smog (ρ = {f(sia['rho_IN_next_day'])}, against {f(sia['rho_PK_next_day'])} for Pakistan-origin fires); "
  f"in Lahore it is the other way round ({f(lah['rho_IN_next_day'])} against {f(lah['rho_PK_next_day'])}), although {f(lah['IN_share_pct'], 0)}% of the fires in Lahore's cone are Indian. "
  "The cross-border signal is therefore mixed and rests on one season; hypothesis H4 tests it with controls.")
p(f"**Robustness of the index weights.** Rebuilding the index with equal weights, without ozone or without PM10 ranks the days almost identically (Spearman ρ ≥ "
  f"{f(w['spearman_with_main'].min(), 3)}). Dropping ozone changes the most spike labels ({int(w.loc['without ozone', 'labels_changed'])} city-days, "
  f"against {int(w.iloc[0]['spike_days'])} training spikes in the main index), because winter ozone moves opposite to NO2. The main weights are kept and the ozone sensitivity is listed as a limitation.")

# =====================================================================
# 4. Hypotheses
# =====================================================================
h1("4. Hypotheses and Analytical Plan")
p("Each hypothesis starts from a pattern in Section 3 and is mapped to columns of the master dataset (Table 12). The response is always measured on day t + 1 "
  "(t + 1 to t + 3 for H5) and uses only information known on day t. The full mapping, with the planned test for each hypothesis, is in the workbook sheet Hypothesis_Mapping.")
H = [("H1 Cone vs radius (C)", "**H0:** adding the upwind-cone fire count to a model with the plain 300 km count and the controls does not improve the explanation of the next-day index (β_cone = 0). "
      "**H1:** the cone count is positively associated with the next-day index beyond the plain count (β_cone > 0).", "11.6, 13"),
     ("H2 Weather trap (B)", "**H0:** stagnation, humidity, absence of rain and a large temperature range do not change the odds of a next-day spike (OR = 1). "
      "**H1:** each raises the odds (OR > 1).", "3.9, 11.6"),
     ("H3 Fire × stagnation (A)", "**H0:** the fire effect on the next-day index is the same on stagnant and ventilated days (β_fire×stagnant = 0). "
      "**H1:** it is stronger on stagnant days (β_fire×stagnant > 0).", "3.9, 13.1"),
     ("H4 Cross-border (C)", "**H0:** in Pakistani cities, India-origin upwind fires are not associated with the next-day index once Pakistan-origin fires and weather are "
      "controlled, and the association is the same near the border and far from it (β_IN = 0, β_IN×near = 0). **H1:** India-origin fires raise next-day smog, more in "
      "Lahore and Sialkot than in far cities (β_IN×near > 0).", "13, 17, 11.6"),
     ("H5 Forecast value (A)", "**H0:** a model with the fire and weather features does not beat persistence or a weather-only model on validation (ΔPR-AUC ≤ 0, ΔMAE ≥ 0). "
      "**H1:** it beats both for at least one horizon of 1 to 3 days.", "3.d, 3.9")]
# The shared control set C is written once; the table shows what each hypothesis adds to it (full lists: hypothesis_mapping.csv)
CTRL = "month_02..month_12, city_* (10), temp_mean_c, temp_range_c, rh_mean_pct, precip_sum_mm, vec_len_kmh (those not used as X)"
assert hm.loc["H1", "controls"] == CTRL and hm.loc["H3", "controls"] == CTRL
assert hm.loc["H4", "controls"] == "fire_cnt_up45_r300_pk_log1p_z, " + CTRL.replace("city_* (10)", "city_* (6 Pakistani)")
short = {"H1": "C", "H2": hm.loc["H2", "controls"], "H3": "C",
         "H4": "C with city_* for the 6 Pakistani cities, plus fire_cnt_up45_r300_pk_log1p_z", "H5": hm.loc["H5", "controls"]}
table("Formal hypotheses with variable mapping (Y = response, X = main predictors) and the SDG targets they inform. Owners in brackets.",
      ["ID", "Hypotheses", "Response (Y)", "Predictors (X)", "Controls", "SDG"],
      [[hid, txt, hm.loc[hid.split()[0], "Y"], hm.loc[hid.split()[0], "X"], short[hid.split()[0]], sdg] for hid, txt, sdg in H],
      [1050, 3250, 1250, 2000, 1550, 692],
      note=f"C = {CTRL.replace(' (those not used as X)', '')}, excluding any column already used as X.", font=7)
p("**Analytical plan.** Consecutive days of a city are correlated, and Islamabad and Rawalpindi share air-quality values, so H1–H4 use regressions with city-clustered "
  "standard errors or a block bootstrap: logistic regression for the spike label and linear regression for the index, with interaction terms for H3 and H4. "
  "Non-linear effects will be checked with gradient-boosted trees and permutation importance. For H5, models are compared on the validation season (1,309 city-days, "
  "1,012 of them in October–December 2023) against persistence (persist_index, persist_spike) and a weather-only model. Because spikes are rare (5.2%), results are "
  "reported as PR-AUC, recall and precision as well as ROC-AUC and the Brier score, and as MAE for the index. Because the spike label falls mainly in December–January, "
  "after the burning peak, Milestone 3 will also report results for the continuous index and compare a label with month-specific thresholds.")

# =====================================================================
# 5. Limitations and 6. Reproducibility
# =====================================================================
h1("5. Limitations")
bullets(["**Model-based air quality.** Open-Meteo air quality is CAMS model output on a coarse grid, not monitor data; neighbouring cities can share values (Islamabad = Rawalpindi).",
         "**One training winter.** Every learned threshold, scaling parameter and the cone choice rest on one harvest season (92 days per city); differences in ρ of about 0.1 are within noise.",
         "**No pressure and no direct inversion measure.** Surface pressure was not in the exported files; temperature range and stagnation are proxies.",
         "**Satellite fire detection.** VIIRS misses fires under thick cloud or fog and between its overpasses; counts are detections, not fires.",
         "**Simplifications.** Each city is one point, the cone uses one daily wind direction, one UTC+5 clock is used for India (IST is UTC+5:30), and observed weather stands in for forecast weather.",
         "**Dependence.** City-days are not independent (multi-day episodes, shared regional weather), so group comparisons and contingency p-values are descriptive."])
h1("6. Reproducibility and Deliverables")
p("The notebooks air_quality.ipynb (A), weather.ipynb (B), fire.ipynb (C) and merge_analysis.ipynb (Role 2) run top to bottom with Restart and Run All, in this order, "
  "from the project root, and keep all their printed outputs and figures. They share one settings file (src/config.py: cities, coordinates, dates, file names) and helper "
  "modules for the merge, the EDA and one figure style. Every setting is learned on the training period and saved, so the final run on 2024 only changes the dates in the "
  "settings file. The last cell of merge_analysis.ipynb writes the workbook Milestone2_Final_Master_and_EDA.xlsx: its first sheet is the master table (5,665 × 287), and "
  "its Contents sheet lists the other sheets (data dictionary, missing values for every column, decisions log, saved parameters, encoding example, the final table of each "
  "stream, and every EDA table of this report) together with the table or figure that uses each one.")

h2("References")
refs = ["Hersbach, H., et al. (2020). The ERA5 global reanalysis. Quarterly Journal of the Royal Meteorological Society, 146(730), 1999–2049.",
        "Inness, A., et al. (2019). The CAMS reanalysis of atmospheric composition. Atmospheric Chemistry and Physics, 19, 3515–3556.",
        "NASA (2024). Fire Information for Resource Management System (FIRMS), VIIRS 375 m active fire product. https://firms.modaps.eosdis.nasa.gov",
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
