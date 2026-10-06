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
