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

Known gap (no rows removed): detections from 31 Dec 2021 (UTC 19:00–24:00) would belong to 1 Jan 2022 local time, but 2021 files were not downloaded, so the first local day is missing up to 5 hours of fires. This is irrelevant for modeling, which starts on 2022-08-04.

Settings fixed for the daily features (not removals, recorded for consistency):
- City coordinates come from the weather file headers (`CITY_COORDS` in `src/config.py`).
- Radii: 50, 100, 150, 200, 300 km. Cones: ±30/45/60° upwind and ±45° downwind (placebo). Default for the merge: 150 km.
- Days with no fires are 0, never missing (8,030-row city-day grid).
- Stagnant days (flag from Person B): the cone count equals the radius count.
- Outliers are flagged (`out_z_*`, `out_iqr_*`), never deleted.
