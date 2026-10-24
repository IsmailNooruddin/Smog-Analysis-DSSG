from pathlib import Path

DATASET_DIR = Path("Dataset")
COUNTRY_FOLDER = {"PK": "Pakistan", "IN": "India"}

CITY_COUNTRY = {
    "Lahore": "PK", "Faisalabad": "PK", "Multan": "PK", "Rawalpindi": "PK",
    "Sialkot": "PK", "Rahim Yar Khan": "PK", "Islamabad": "PK",
    "Amritsar": "IN", "Ferozepur": "IN", "Ludhiana": "IN", "Jalandhar": "IN",
}

# city -> weather file name (exactly as it appears in the folder)
WEATHER_FILES = {
    "Lahore": "Lahore - Weather.csv",
    "Faisalabad": "Faisalabad - Weather.csv",
    "Multan": "Multan - Weather.csv",
    "Rawalpindi": "Rawalpindi weather.csv",
    "Sialkot": "Sailkot-Weather.csv",          # typo is in the original file name
    "Rahim Yar Khan": "Rahim Yar Khan - Weather.csv",
    "Islamabad": "Islamabad - Weather.csv",
    "Amritsar": "Amritsar - Weather.csv",
    "Ferozepur": "Ferozepur - Weather.csv",
    "Ludhiana": "Ludhiana - Weather.xlsx",     # the only Excel file
    "Jalandhar": "Jalandhar - Weather.csv",
}

def weather_path(city):
    """Builds Dataset/<Country>/Weather/<file> for a city."""
    return DATASET_DIR / COUNTRY_FOLDER[CITY_COUNTRY[city]] / "Weather" / WEATHER_FILES[city]

# ------------------------------------------------------------
# NASA VIIRS fire files (Person C)
# Only 2022 and 2023 are listed on purpose: 2024 is kept sealed for the
# Week 14 extension, so it can never be read by accident.
# ------------------------------------------------------------
NASA_FILES = {
    ("IN", 2022): "NASA - 2022 - India.csv",
    ("IN", 2023): "NASA - 2023 - India.csv",
    ("PK", 2022): "NASA - 2022.csv",
    ("PK", 2023): "NASA - 2023.csv",
}

def nasa_path(country, year):
    """Builds Dataset/<Country>/NASA/<file> for a country code and year."""
    return DATASET_DIR / COUNTRY_FOLDER[country] / "NASA" / NASA_FILES[(country, year)]

# city -> (latitude, longitude), copied from the header block of each weather file
# (same points weather.ipynb reads as `centroid`)
CITY_COORDS = {
    "Lahore":         (31.528997, 74.38995),
    "Faisalabad":     (31.458698, 73.11828),
    "Multan":         (30.123022, 71.49533),
    "Rawalpindi":     (33.56766,  73.048325),
    "Sialkot":        (32.51318,  74.56204),
    "Rahim Yar Khan": (28.435852, 70.26136),
    "Islamabad":      (33.63796,  73.0273),
    "Amritsar":       (31.669594, 74.89208),
    "Ferozepur":      (30.966606, 74.64455),
    "Ludhiana":       (30.8963,   75.8343),
    "Jalandhar":      (31.3181,   75.62575),
}

TRAIN_START = "2022-08-04"
TRAIN_END = "2023-08-31"
VALID_START = "2023-09-04"
VALID_END = "2023-12-31"
# ------------------------------------------------------------
# Role 2: merge and analysis (merge_analysis.ipynb, src/merge.py)
# ------------------------------------------------------------
# Modelling window: AQ data starts 2022-08-04, so every stream is cut to this
# window before the merge (11 cities x 515 days = 5,665 rows). For Week 14,
# change these dates and rerun; nothing else is hard-coded.
WINDOW_START = "2022-08-04"
WINDOW_END = "2023-12-31"
SKIP_START = "2023-09-01"   # 3-day gap between train and validation (= longest horizon)
SKIP_END = "2023-09-03"

CLEAN_DIR = DATASET_DIR / "clean"
FIG_DIR = Path("figures")

# City groups for the cross-border analysis (Pakistani cities only)
NEAR_BORDER = ["Lahore", "Sialkot"]                                 # border cities, most India-origin fires
INTERMEDIATE = ["Faisalabad"]                                       # some India-origin fires within 150 km
FAR_PK = ["Multan", "Rahim Yar Khan", "Islamabad", "Rawalpindi"]    # almost no India-origin fires
IN_CITIES = ["Amritsar", "Ferozepur", "Ludhiana", "Jalandhar"]
