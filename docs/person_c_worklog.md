# Person C (Fire Stream) Work Log: Milestone 2

**Owner:** Bilal Ayub (Person C, fire data)
**Period:** 2 to 3 October 2026
**Scope:** everything done for Person C up to now, in the order it happened, with the reason behind each decision.

Related files:
- `fire.ipynb`: the fire-stream notebook (runs top to bottom).
- `DECISIONS.md`: bookkeeping table of every data removal, with exact row counts.
- `Milestone 2 Report - Fire.docx`: the fire part of the Milestone 2 report.
- `figures/fig_fire_study_area.png`, `figures/fig_fire_monthly_by_origin.png`: the two figures.
- `Dataset/clean/fire_daily.parquet`, `fire_daily_long.parquet`, `fire_zscore_params.json`: clean outputs for the merge.

---

## Step 1: Understanding where the project stood

**What was read:** the submitted proposal (`context/Final Proposal.md`), the Milestone 1 and 2 briefs, the instructor's feedback, and the AQ notebook already in the repo.

**The instructor's feedback had two points:**
1. They had doubts about the 45° wind cone and asked us to also run 30° and 60° and learn from the differences.
2. The study should not aim for a target score (the proposal promised ROC-AUC > 0.88). Aiming at a number invites overfitting. The aim is to find sensible predictors and patterns first, then report the best honest accuracy.

**Things found in the data and code that mattered later:**
- The AQ data has no values before 4 Aug 2022. That leaves two rice-burning seasons (Oct–Nov 2022 and 2023) and one wheat-burning season (Apr–May 2023).
- The Open-Meteo AQ data is output from the CAMS air-quality model (~40 km grid), not ground sensors. This is a limitation for the report.

## Step 2: Reviewing the team's Milestone 2 work plan

The team wrote a work plan (`Milestone2_Work_Plan.docx`) that splits the work into Person A (AQ), B (weather) and C (fire). It was checked against the feedback and the Milestone 2 marking scheme, and a review document was written: "Milestone 2 Work Plan: Review and Recommended Changes" (a Claude Doc).

**Verdict:** the plan is sound. It already answered both feedback points and covered every marking item. Eight changes were recommended. Those that affect Person C:

| Change | Why |
|---|---|
| Add a **downwind "placebo" cone** (wind direction + 180°) | Fires and smog both peak in Oct–Nov, so *any* fire count will correlate with smog. Downwind fires have the same seasonal pattern but cannot blow smoke to the city. If upwind fires beat downwind fires, the effect is real transport. If they don't, the link is just seasonal. This is the clearest answer to the instructor's doubt about the cone. |
| **Don't pick the cone or radius with the best correlation** | The grid is about 240 correlations on one training winter. The single best one will partly be luck, which is the same overfitting the instructor warned about. Keep 150 km / ±45° as a pre-set default and only switch if a whole region of settings does better. |
| On **stagnant days, cone count = radius count**, not missing | Stagnant days (almost no wind) are the worst smog days. Leaving cone counts empty would remove them from the model (and from the 1–3 day lags after them). With no wind, smoke drifts in from all sides, so the full circle is the right count. |
| **Move H4 (cross-border, near vs far cities) to Person C** | It is the same analysis as C's cross-border check (step 7). It also evened out workload, since Person B had the merge and the report assembly. |
| Test hypotheses on the **7 Pakistani cities** only | The research question is about Pakistani cities. Indian cities sit among the fires and would blur what "cross-border" means. |

## Step 3: Planning the Person C work (decisions agreed with Bilal)

Before planning, the 2022–2023 fire files were profiled (2024 was never opened). What the profiling showed:
- 4 files, **1,284,773** detections, all from one satellite (NOAA-20), **0 duplicates**.
- The India file covers all of India, so it needs a geographic filter.
- Confidence: `n` (nominal) 80%, `l` (low) 17%, `h` (high) 3%.
- Type 2 (static hot spots) ≈ 11% overall.
- India-origin fires within 150 km: Lahore ~62k, Sialkot ~25k, Faisalabad ~7k, but Multan 0 and Rahim Yar Khan ~80.

Decisions, each with its reason:

| # | Decision | Reason |
|---|---|---|
| Q1 | Scope = Role 1 only (clean data, daily features, own EDA). Bilal does the Role 2 analysis himself | His choice |
| Q2 | New notebook `fire.ipynb`. File list and city coordinates go in `src/config.py`. **2024 files are not listed in config at all** | Matches the teammates' notebooks. 2024 can't be loaded by accident because the code doesn't know it exists |
| Q3 | Keep confidence `n` + `h`, drop `l`. Keep `h`-only and `n+h+l` versions as sensitivity checks | `l` = daytime-only weak signals, often sun glint or hot bare ground. In the Punjab region they are 27–36% of Apr–May points but only 2–8% of Oct–Nov points. `h` doesn't mean "more certain": it means the sensor saturated (a very hot fire). Dropping `n` too would leave 3% of the data |
| Q4 | **Drop type 2 and 3** and record the removal in the bookkeeping file | Type 2 = 7,305 points at only **144 fixed locations** (brick kilns, factories), burning at a steady 500–1,000 per month all year. Something that never changes can't explain *which days* are smoggy, and the city's baseline already absorbs it. Satellites also see only the hottest kilns, so the count is not a real kiln inventory. Type 3 = offshore |
| Q5 | Country of a fire = the file it came from | The files are already split by country. This was later confirmed visually: the plotted border runs exactly where the two colours meet (Step 6) |
| Q6 | Time: join date + 4-digit time as UTC, **add 5 h, then take the date** | Same rule as AQ and weather. Shifting only the date column would put night detections on the wrong day |
| Q7 | City coordinates from the weather file headers | All three data streams then use identical points |
| Q8 | Wait for Person B's daily wind table rather than compute wind privately | Two separate wind calculations could quietly disagree |
| Q9 | Settings grid: radii 50/100/150/200/300 km × cones ±30/45/60°, no cone, downwind ±45°, each split by origin (IN/PK/all), count + FRP | Gives the full sensitivity analysis the instructor asked for. 300 km is included because far cities have no Indian fires within 150 km |
| Q10 | Stagnant days: cone = radius count + flag | See Step 2 |
| Q11 | Full city-day grid (11 cities × 730 days = 8,030 rows); no-fire day = 0; CSV outputs | A day with no fire is a real 0, not missing data. Starting from a full grid keeps every day visible |
| Q12 | EDA: summary table, outlier audit, two figures. **Figures only after asking Bilal**, made with the dataviz skill | His request |
| Q13 | A shared `DECISIONS.md` bookkeeping file with exact before/after counts | His request; it also feeds the report's data-audit section directly |
| Q14 | Build everything that doesn't need wind now. The cone cell runs once B's wind file exists | The risky geometry gets built and tested early |

## Step 4: Building the fire pipeline (first version)

**`src/config.py`:** added `NASA_FILES` (2022 and 2023 only), `nasa_path()` and `CITY_COORDS`.

**`fire.ipynb`:** each step is followed by a markdown note explaining it.

1. **Load and stack** the 4 files. `acq_time` is read as text, because "0833" read as a number becomes 833. Checks: 0 duplicates, one satellite, every time still has 4 digits.
2. **Study-area box** (26–37°N, 68–79°E): 1,284,773 → 287,323. The box keeps everything within 300 km (our largest radius) of every city.
3. **Type 0 only:** 287,323 → 279,968.
4. **Confidence n + h:** 279,968 → 238,796.
5. **Time conversion:** UTC + 5 h. 26,626 detections move to the next Pakistan date (mostly night passes), and 40 fall on 1 Jan 2024 and are dropped → **238,756**.
6. **Dummy columns** at detection level: `is_night` (reference: day), `conf_high`, `conf_low` (reference: nominal). These are needed because the marking scheme asks for 0/1 encoding of text categories.
7. **Distance and bearing:** Haversine distance and compass bearing from each city to every fire, computed for all fires at once (vectorised) with one loop over the 11 cities. This is ~1.4M city–fire pairs within 300 km. They are computed once and stored, so every radius is just a filter. One fire can count for several cities, which is correct because its smoke can reach any of them.
8. **Cone function** `cone_mask()`. Angles are compared around the circle, so 350° and 10° are 20° apart, not 340°. It was tested on toy cases:
    - wind from the north keeps fires to the north;
    - fires to the south are in the downwind cone;
    - the 0°/360° wrap-around works;
    - 44° counts as inside a ±45° cone and 46° doesn't.
9. **Radius features** on the full 8,030-row grid, with no-fire days = 0.
10. **Cone cell:** waits for B's wind file and skips with a clear message until then.
11. **Summary statistics and outlier audit** (z-score rule and IQR rule, raw and log scale). Outliers are *flagged, not deleted*, because huge fire days are the events being studied.

**Testing before B's file existed.** A temporary wind file was built from the raw hourly weather and the full notebook was run against it. All cone checks passed. The file was then **deleted and never committed**, so no stand-in data could leak into results.

**`DECISIONS.md`** created with rows F1–F5 (2024 excluded, box, type, confidence, time window).

## Step 5: Figures (made with the dataviz skill)

1. **Study-area map:** fire detections for Oct–Nov 2023 (blue = India, orange = Pakistan), the 11 cities, Lahore's 150 km ring, and the ±30/45/60° cones drawn on top of each other.
2. **Monthly detections by origin, 2022–2023**, with the two burning seasons shaded.

Design decisions:
- **Colours:** blue/orange was run through the colour-blindness validator and passed every check. Colours have fixed meanings across figures.
- **Map scale:** the map's aspect ratio is corrected for latitude, so distances look true at Punjab's latitude.
- **Checked by eye:** each figure was rendered and looked at, and overlapping city names and labels were fixed until nothing collided.
- **Captions:** every figure has units on the axes, a legend and a caption stating the data and filters.
- **The monthly chart's message:** the Oct–Nov fire peak lines up with the start of the smog season. That is exactly why the downwind control matters.

## Step 6: Country borders on the map

- Natural Earth 1:10m boundary lines were downloaded (from the Natural Earth GitHub repo, since the official CDN was blocked here).
- They were clipped to the study area and saved as `Dataset/NaturalEarth/ne_10m_boundary_lines_study_area.geojson` (69 KB), so the notebook runs **without internet** (e.g. on Colab).
- **Kashmir:** the north of the map includes disputed territory. Bilal chose Natural Earth's neutral de facto version: international border solid, Line of Control dashed and labelled as disputed.
- The legend moved outside the map so it no longer covers the Indian fires.
- **Useful finding:** the drawn border runs exactly where the blue and orange dots meet. That confirms labelling each fire by its source file is correct.

## Step 7: Git authorship and the first PR

- Bilal asked that commits appear as his. The repo's git identity was set to **Bilal Ayub \<bilelayub@gmail.com\>**.
- The two already-pushed commits were rebuilt with identical content under his name, without the Claude co-author lines, and force-pushed. That branch was only ours at that point, so nobody else's work was affected.
- PR #1 was opened from the Claude Code app. Its description included a Claude session link, which was **removed** at Bilal's request.
- The team then merged PR #1 into `main`.

## Step 8: Person B's wind table arrives, and the cone features are completed

Munir (Person B) pushed `Dataset/clean/wind_daily.parquet`. Because PR #1 was already merged, the branch was restarted from the latest `main`.

**Checks before using it:**
- **Direction convention.** B's code stores wind as "toward" vectors and converts back with `atan2(-u, -v)`, so `wind_dir_daily_deg` is the direction the wind comes **from**, which is what the cone needs. His toy test confirms it.
- **Coverage.** The wind table has 7,852 of 8,030 city-days. The 178 missing are all in January 2022 (1–11 Jan for Pakistani cities, up to 29 Jan for Indian cities), because the weather files start then.

**Decisions:**
- **Cone columns are left empty (NaN), not 0, on those 178 city-days.** Writing 0 would claim "no upwind fires" when we simply don't know. Radius columns stay complete. All 178 days are months before the modelling window (from 4 Aug 2022), so nothing is lost. Logged as **F6** in `DECISIONS.md`.
- **Stagnant days:** B's flag (daily vector-mean wind < 2 km/h) covers **10.7%** of city-days. There the cone keeps every fire in the radius, and the `stagnant` column is carried into the fire table so the merge can tell which cone counts are really radius counts.

**Automatic checks added (all pass):**
- no cone ever has more fires than the full circle;
- wider cones always have at least as many fires as narrower ones;
- on stagnant days the cone count equals the radius count.

The first run failed one of these checks. The cause was the empty January days: NaN compared with NaN is "false". This was a flaw in the check, not the data, so the check now skips the no-wind days.

**Map update:** the cones are now drawn for a **real day**, 29 Oct 2023 (wind from 80°): the Oct–Nov 2023 day with the most Indian fires inside Lahore's ±45° cone. Before this, the map used a made-up wind direction.

**What the cone table shows** (India-origin fires within 150 km of the 7 Pakistani cities, Oct–Nov):

| Cone | Share of the circle's fires | Days with zero fires |
|---|---|---|
| none (full circle) | 100% | 57% |
| ±60° upwind | 26% | 75% |
| ±45° upwind | 21% | 80% |
| ±30° upwind | 17% | 83% |
| ±45° downwind | 50% | 75% |

- Narrow cones are much sparser. Keep this in mind when comparing ±30° with ±60°.
- More Indian fires sit **downwind** than upwind. The most common Oct–Nov winds come from the north-west (33% of non-stagnant days) and north (18%), which carry Indian smoke away from Pakistan. Easterly winds (32% of days) are the ones that bring it in.
- This only describes the fire data. Whether those easterly days are the smoggy days is the Role 2 test.

## Step 9: Transformations and clean outputs for the merge

The AQ and weather notebooks both apply log transforms and training-period z-scores and save their tables to `Dataset/clean/`. The fire notebook was brought in line with them:
- **log1p** on the 150 km and ±45° cone count/FRP columns. log1p (log of 1 + x) handles the many zero days. Skewness drops from **4.2–13.6 to 0.1–2.2**.
- **z-scores of the log columns**, using the mean and SD of the **training period only** (4 Aug 2022 – 31 Aug 2023, from `src/config.py`). This way the validation period can't leak into the scaling. The values are saved in `fire_zscore_params.json`.
- **Min-max scaling was not used:** with a few enormous fire days, it would squash every other day close to 0.
- **Saved to `Dataset/clean/`:**
    - `fire_daily.parquet`: 8,030 × 60, the table to merge on `city` + `date`;
    - `fire_daily_long.parquet`: 602,250 rows, every cone × radius × origin, for the sensitivity analysis.

  These go to GitHub like B's tables, so the merge doesn't require rerunning the fire notebook.

## Step 10: Report section

`Milestone 2 Report - Fire.docx` follows the same layout as Ismail's AQ report (same headings, Arial, Letter size):

1. **Alignment and dataset overview:** what the fire stream does and its key numbers.
2. **Ingestion and cleaning:** collection checks, the filtering table, time conversion, how the distance and cone features are built, missing data and bias (cloud/fog hiding fires on the smoggiest days probably makes fire effects look *smaller*), and transformations.
3. **EDA:** summary statistics (mean vs median, SD vs IQR), the outlier audit and masking effect, and key findings.
4. **The two figures** with full captions.
5. **Limitations:**
    - cloud and fog hide fires from the satellite;
    - the satellite passes only twice a day;
    - each city is treated as a single centre point;
    - the wind is measured at the city, not along the smoke's path;
    - dropping low-confidence points may lose some small real fires;
    - only near-border cities can test the cross-border claim.

The file passed the Word format check. It couldn't be previewed as pages here because LibreOffice can't open any document in this environment, so open it in Word to check the layout.

## Step 11: Repository housekeeping

- The branch was renamed from `claude/keen-cannon-mv7k42` to **`feature/fire-stream`**.
- At Bilal's request, PRs are no longer used: work is **pushed directly to `main`** (`main` is at `4aff928`, which includes all fire work).
- Deleting the old `claude/keen-cannon-mv7k42` branch on GitHub was refused by this environment's git connection. It points to the same commit as `main`, so nothing is lost. Delete it from the repo's Branches page on GitHub if wanted.
- **Unverified commits:** GitHub marks commits "Verified" only when they are signed with a key registered to the author's account. Commits made here carry Bilal's name but no signature from his key. Bilal chose to leave this as is. To get Verified commits in future, set up SSH/GPG signing on his own machine.

## Commits by Person C (on `main`)

| Commit | Date | What |
|---|---|---|
| `d5c94fc` | 2 Oct | Fire notebook, config additions, `DECISIONS.md` |
| `6adc581` | 2 Oct | Study-area map and monthly figure |
| `1f3b401` | 2 Oct | Natural Earth borders on the map |
| `e59f0e2` | 3 Oct | Cone features using B's wind table, F6, real-day map |
| `2d58399` | 3 Oct | log1p, training-period z-scores, clean tables in `Dataset/clean/` |
| `4aff928` | 3 Oct | Milestone 2 report section (fire) |

## What is still open

1. **Role 2, step 6 (Bilal):** cone sensitivity. Compare upwind ±30/45/60° vs downwind vs no cone, using **partial correlations within Oct–Dec on the training period** with the 7 Pakistani cities. Use `Dataset/clean/fire_daily_long.parquet`. Keep 150 km / ±45° unless a whole region of settings does clearly better, and report the share of zero days next to each angle.
2. **Role 2, step 7 (Bilal):** cross-border check per city. Only Lahore, Sialkot and Faisalabad have enough India-origin fires to test it.
3. **H1 and H4 wording** (H0/H1 form) for the hypotheses table.
4. Open the report in Word to check the layout, and delete the old branch on GitHub if wanted.
