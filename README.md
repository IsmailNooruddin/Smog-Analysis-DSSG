# Trans-Boundary Smog Prediction

Predicting composite smog spikes in Pakistani Punjab cities 1 to 3 days ahead from upwind
cross-border crop fires (NASA VIIRS) and weather (Open-Meteo), for 11 cities in Pakistan and Indian Punjab.

## Project structure
```
Smog-Analysis-DSSG/
├── air_quality.ipynb        Role 1, Person A: air quality, Composite Smog Index, spike label
├── weather.ipynb            Role 1, Person B: weather, daily wind, stagnation flag
├── fire.ipynb               Role 1, Person C: VIIRS fires, distance/bearing, wind cones
├── merge_analysis.ipynb     Role 2: merge into the master dataset (2A) and analysis (2B), hypotheses
├── src/
│   ├── config.py            shared rules: cities, files, coordinates, dates, folders
│   ├── merge.py             Part 2A functions (all take a date window, reusable for 2024)
│   ├── eda.py               Part 2B helpers (summary, outlier audit, rates, contingency)
│   └── plotting.py          one colorblind-safe figure style
├── Dataset/
│   ├── India/, Pakistan/    raw files (Air Quality, NASA, Weather); 2024 files are sealed
│   └── clean/               Role 1 outputs + master_daily.parquet, master_data_dictionary.csv, *_params.json
├── figures/                 all report figures (fig_a* AQ, fig_b* weather, fig_fire_* fire, fig_m* merged)
├── docs/
│   ├── tables/              every table quoted in the manuscript (written by merge_analysis.ipynb)
│   └── manuscript/          builds Milestone2_Manuscript_Draft.docx from docs/tables
├── DECISIONS.md             every data removal or change, with row counts
├── Milestone2_Manuscript_Draft.docx   combined Sections I–VI of the paper
└── Report_*.docx / Milestone_2_Report_*.docx   Role 1 stream reports
```

## Running everything
```
python -m venv venv
source venv/bin/activate            # Windows: venv\Scripts\activate.bat
pip install -r requirements.txt
```
From the repository root, run the notebooks in this order (Kernel → Restart and Run All):
1. `air_quality.ipynb`
2. `weather.ipynb`
3. `fire.ipynb`
4. `merge_analysis.ipynb`

Or headless: `jupyter nbconvert --to notebook --execute --inplace <notebook>.ipynb`.

To rebuild the manuscript after the notebooks (needs Node.js and `npm install docx`):
```
python docs/manuscript/build_manuscript.py
node docs/manuscript/render_docx.js
```

## Key settings (src/config.py)
- Modelling window: 2022-08-04 to 2023-12-31 (air quality starts 2022-08-04).
- Train 2022-08-04 to 2023-08-31, skip 2023-09-01 to 2023-09-03, validation 2023-09-04 to 2023-12-31.
- Week 14: change the window dates and rerun; 2024 is never read in Milestone 2.

## Data sources
- Air quality: Open-Meteo Air Quality API (CAMS global model output), hourly.
- Weather: Open-Meteo Historical Weather API, hourly.
- Fire hotspots: NASA FIRMS, VIIRS 375 m (NOAA-20).
