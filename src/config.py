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