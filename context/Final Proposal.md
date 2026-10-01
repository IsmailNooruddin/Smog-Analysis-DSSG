# Milestone 01: Problem Framing & Dataset Curation

**Trans-Boundary Smog Prediction: Tracking Cross-Border Crop Fires & Climate Traps across Punjab (Pakistan & India)**

## 1. Team Composition & Problem Framing

| Team Member | Student ID | Background |
|---|---|---|
| Munir Tariq | 10067 | Major: Computer Science – Minor: SDP |
| Ismail Nooruddin | 09958 | Major: Computer Science |
| Bilal Ayub | 09716 | Major: Computer Science |

### 1.1 Social Problem & SDG Alignment

Every winter, the contiguous Punjab plain spanning Pakistan and India acts as a shared atmospheric basin, trapping toxic agricultural smoke and urban pollution. Because wind and smoke ignore political borders, rural crop fires burning in Indian Punjab blow directly across the border into Pakistani cities. Most existing models fail because they only count local fires or rely on single pollutants. Our project builds a trans-boundary machine learning model targeting a Composite Smog Index (integrating PM2.5, PM10, CO, NO2, SO2, and O3) by tracking cross-border upwind satellite fires alongside a complete set of climate factors. While piloted on the Punjab epicenter, this architecture is designed as a scalable blueprint for nationwide deployment across all of Pakistan.

- **SDG 3 (Good Health & Well-being):** Gives hospitals and emergency rooms in Pakistani cities a 24-to-72-hour advance alert to prepare for sudden surges in pediatric and adult respiratory admissions.
- **SDG 11 (Sustainable Cities & Communities):** Equips environmental protection agencies with data-driven evidence to separate local urban emissions from incoming cross-border agricultural smoke.
- **SDG 13 (Climate Action):** Demonstrates the necessity of regional, cross-border climate data modeling to protect public health rather than relying on ineffective localized lockdowns.

### 1.2 Research Question & Hypotheses

**Research Question:** How accurately can a machine learning model predict hazardous Composite Smog spikes (aggregated PM2.5, PM10, CO, NO2, SO2, O3) in Pakistani cities by combining trans-boundary upwind satellite fire trajectories with multi-variate climate trap conditions (temperature, humidity, precipitation, wind speed, and pressure) 1 to 3 days in advance?

- **Main Hypothesis (H1):** The convergence of cross-border upwind farm fires and specific meteorological trap conditions (thermal inversions, zero rainfall, high humidity, and high pressure) accounts for the vast majority of variance in severe composite smog events across Pakistani border cities during the harvest season (Oct–Dec).
- **Secondary Hypothesis (H2):** A multi-variate machine learning model utilizing these combined trans-boundary spatial and climate features will achieve an Out-of-Time ROC-AUC score above 0.88 in forecasting severe multi-pollutant smog emergencies 24 to 72 hours in advance.
- **Null Hypothesis (H0):** Tracking cross-border wind trajectories and multi-variate climate variables provides no statistically significant improvement in predicting composite city smog over basic localized weather forecasts.

## 2. Dataset Scope & Data Curation Effort

To ensure genuine data curation, we will construct our baseline dataset by combining 26 separate files across 2 independent sources, covering 7 key Pakistani Punjab cities (Lahore, Faisalabad, Multan, Rawalpindi, Sialkot, Rahim Yar Khan, Islamabad) as the initial pilot scope, alongside 4 Indian border hubs (Amritsar, Ferozepur, Ludhiana, Jalandhar) to track incoming transport. The baseline training scope covers 2022–2023.

| Dataset Stream | Primary Source | Coverage & Granularity | Total Records |
|---|---|---|---|
| Air Quality Stream (11 CSVs) | Open-Meteo Air Quality API | Hourly (PM2.5, PM10, CO, NO2, SO2, O3) for 11 Indo-Pak Punjab Cities \| 2022–2023 | 192,000+ rows |
| Weather Stream (11 CSVs) | Open-Meteo Historical Weather | Hourly (Temp, Wind Speed/Dir, Rain, Humidity, Pressure) \| 2022–2023 | 192,000+ rows |
| Satellite Fire Hotspots (4 CSVs) | NASA VIIRS FIRMS | Satellite Pixel fire points across Pakistan & Indian Punjab \| 2022–2023 | 250,000+ points |

### 2.1 Data Curation & Merging Challenges

1. **Trans-Boundary Spatial Merging:** NASA satellite fire logs record individual GPS point coordinates across Pakistan and India, while Open-Meteo gives hourly weather for city centers. We will write custom Python scripts to convert scattered point detections into daily radial counts around each city center regardless of national borders.
2. **Vectorized Haversine Distance Matrix:** Calculating pairwise distances between 11 city centroids and over 250,000 fire points across multi-year spans presents significant memory overhead. We will implement a vectorized NumPy Haversine formula to compute point-to-city distances within 150 km in seconds.
3. **Dynamic Trigonometric Wind Trajectory Cones:** A simple distance radius is inaccurate because smoke moves with the wind. We will calculate the compass bearing angle (atan2) from every fire point to each city center and filter for fires falling inside the city's prevailing 10m wind direction cone (±45°).
4. **Multi-Variate Climate & Smog Feature Integration:** We will engineer a Composite Smog target variable from raw pollutants (PM2.5, PM10, CO, NO2, SO2, O3) while extracting temperature (thermal inversion proxy), rainfall (atmospheric washing), humidity (fog/smog formation), and surface pressure alongside rolling upwind fire lags.

### 2.2 Data Limitations

- **Satellite Cloud & Fog Masking:** NASA optical satellites (VIIRS) may under-count thermal anomalies during heavy overcast or dense winter fog layers in the Punjab basin.
- **Centroid Weather Approximation:** Open-Meteo weather and air quality metrics represent city-center coordinates, which average out micro-variations across expansive urban perimeters.

## 3. Future Extension Plan (Week 14 Readiness)

Our datasetstructure is designed for seamless prospective extension around Week 14 through two planned additions:

- **Extension 1: Prospective Out-of-Time Testing (Complete 2024 Dataset):** We will add the complete 2024 data stream—including 2024 NASA VIIRS fire logs for both Pakistan and India alongside 2024 Open-Meteo weather and air quality files for all 11 cities. Evaluating a model trained purely on 2022–2023 data against an unseen 2024 harvest season will prove its true real-world prospective forecasting utility.
- **Extension 2: WorldPop Population Density Risk Mapping:** We will integrate WorldPop 1 km² grid census data for Pakistan. Overlaying our model's predicted Composite Smog spikes onto high-resolution population maps will quantify the 'Human Exposure Risk Index' (estimating the exact number of vulnerable citizens exposed to hazardous multi-pollutant air quality for over 12 consecutive hours).
