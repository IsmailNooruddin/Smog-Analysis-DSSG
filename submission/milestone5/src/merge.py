"""Role 2, Part 2A: merge the three daily streams into one master table.

Every function takes the date window as an argument, so the Week 14 run with 2024
data only changes WINDOW_START / WINDOW_END in src/config.py and reruns
merge_analysis.ipynb. Nothing here looks at dates outside the window it is given.

Observational unit of every table: 1 row = 1 city on 1 local (UTC+5) day.
"""
import json

import numpy as np
import pandas as pd

from src.config import CITY_COUNTRY, CLEAN_DIR, NEAR_BORDER

KEYS = ["city", "country", "date"]
CITIES = list(CITY_COUNTRY)

# Key predictors that get lags of 1, 2 and 3 days (computed in the source table,
# with a 3-day lead-in before the window so the first rows are complete).
WEATHER_LAG_COLS = ["temp_mean_c", "temp_range_c", "rh_mean_pct", "precip_sum_mm",
                    "wind_speed_mean_kmh", "vec_len_kmh", "stagnant"]
FIRE_LAG_COLS = ["fire_cnt_r150_all", "fire_cnt_r150_in", "fire_cnt_r150_pk",
                 "fire_cnt_up45_r150_all", "fire_cnt_up45_r150_in", "fire_cnt_up45_r150_pk",
                 "fire_frp_up45_r150_all"]
LAGS = (1, 2, 3)
HORIZONS = (1, 2, 3)

# 8 compass sectors of the daily wind-from direction (calm days = reference)
SECTORS = ["n", "ne", "e", "se", "s", "sw", "w", "nw"]


# ------------------------------------------------------------------
# Loading and key checks
# ------------------------------------------------------------------
def normalise_keys(df):
    """Same key types in every table: clean text city/country, date as datetime64[ns] at midnight."""
    df = df.copy()
    df["city"] = df["city"].astype(str).str.strip()
    df["country"] = df["country"].astype(str).str.strip().str.upper()
    df["date"] = pd.to_datetime(df["date"]).dt.normalize().astype("datetime64[ns]")
    return df


def cut_window(df, start, end, lead_in_days=0):
    """Keep rows from (start - lead_in_days) to end, inclusive."""
    lo = pd.Timestamp(start) - pd.Timedelta(days=lead_in_days)
    return df[(df["date"] >= lo) & (df["date"] <= pd.Timestamp(end))].reset_index(drop=True)


def load_aq(start, end, clean_dir=CLEAN_DIR):
    """Person A's daily AQ table (index, spike label, z-scores) cut to the window."""
    return cut_window(normalise_keys(pd.read_parquet(clean_dir / "aq_daily.parquet")), start, end)


def load_aq_params(clean_dir=CLEAN_DIR):
    """Training-period settings saved by Person A (z-score params, spike thresholds)."""
    with open(clean_dir / "aq_params.json") as f:
        return json.load(f)


def load_weather(start, end, lead_in_days=0, clean_dir=CLEAN_DIR):
    """Person B's daily weather table (it already contains the daily wind columns)."""
    return cut_window(normalise_keys(pd.read_parquet(clean_dir / "wx_daily.parquet")),
                      start, end, lead_in_days)


def load_fire_wide(start, end, lead_in_days=0, clean_dir=CLEAN_DIR):
    """Person C's wide fire table (150 km default settings). Its 'stagnant' column is a
    copy of Person B's flag (checked identical), so it is dropped to avoid a name clash."""
    df = normalise_keys(pd.read_parquet(clean_dir / "fire_daily.parquet")).drop(columns="stagnant")
    df = cut_window(df, start, end, lead_in_days)
    count_cols = [c for c in df.columns if c.startswith("fire_cnt_")]
    assert df[count_cols].notna().all().all(), "fire counts must never be missing"
    df[count_cols] = df[count_cols].astype("int64")   # nullable Int64 -> plain int64
    return df


def load_fire_long(start, end, lead_in_days=0, clean_dir=CLEAN_DIR):
    """Person C's long fire table: every cone x radius x origin setting."""
    return cut_window(normalise_keys(pd.read_parquet(clean_dir / "fire_daily_long.parquet")),
                      start, end, lead_in_days)


SEALED_FROM = "2024-01-01"     # Milestone 5 passes a later seal on purpose


def check_keys(df, name, start, end, n_cities=11, sealed_from=SEALED_FROM):
    """Swap-and-check (2A step 1). Returns a one-row summary and raises if a rule is broken."""
    days = (pd.Timestamp(end) - pd.Timestamp(start)).days + 1
    inside = df[(df["date"] >= pd.Timestamp(start)) & (df["date"] <= pd.Timestamp(end))]
    res = {
        "table": name,
        "rows_in_window": len(inside),
        "key_columns_present": all(k in df.columns for k in KEYS),
        "cities": inside["city"].nunique(),
        "city_names_match_config": set(inside["city"]) == set(CITIES),
        "country_matches_config": bool((inside["country"] == inside["city"].map(CITY_COUNTRY)).all()),
        "duplicate_city_date": int(inside.duplicated(["city", "date"]).sum()),
        "first_date": inside["date"].min().date(),
        "last_date": inside["date"].max().date(),
        "full_calendar": len(inside) == n_cities * days,
        "date_dtype": str(df["date"].dtype),
        "city_dtype": str(df["city"].dtype),
    }
    assert res["key_columns_present"] and res["cities"] == n_cities, name
    assert res["city_names_match_config"] and res["country_matches_config"], name
    assert res["duplicate_city_date"] == 0 and res["full_calendar"], name
    assert inside["date"].max() < pd.Timestamp(sealed_from), f"{name}: dates from {sealed_from} are sealed"
    return res


# ------------------------------------------------------------------
# Spine and joins
# ------------------------------------------------------------------
def build_spine(start, end):
    """Every city x every date in the window, built from scratch (not from a data table)."""
    dates = pd.date_range(start, end, freq="D")
    spine = pd.MultiIndex.from_product([CITIES, dates], names=["city", "date"]).to_frame(index=False)
    spine["country"] = spine["city"].map(CITY_COUNTRY)
    spine["date"] = spine["date"].astype("datetime64[ns]")
    return spine[KEYS]


def join_one_to_one(left, right, name):
    """Left-join on city, country, date with pandas' one-to-one check; row count must not change."""
    clash = (set(left.columns) & set(right.columns)) - set(KEYS)
    assert not clash, f"{name}: column name clash {clash}"
    out = left.merge(right, on=KEYS, how="left", validate="one_to_one", indicator=True)
    matched = int((out["_merge"] == "both").sum())
    out = out.drop(columns="_merge")
    assert len(out) == len(left), f"{name}: row count changed {len(left)} -> {len(out)}"
    return out, matched


# ------------------------------------------------------------------
# Lags, targets and baselines (always grouped by city)
# ------------------------------------------------------------------
def _assert_daily(df):
    gaps = df.sort_values(["city", "date"]).groupby("city")["date"].diff().dropna()
    assert (gaps == pd.Timedelta(days=1)).all(), "lags need a complete daily calendar per city"


def add_lags(df, cols, lags=LAGS):
    """value of `col` on day t-k, as `col_lag{k}`, within each city (never across cities)."""
    df = df.sort_values(["city", "date"]).reset_index(drop=True)
    _assert_daily(df)
    g = df.groupby("city", sort=False)
    new = {f"{c}_lag{k}": g[c].shift(k) for c in cols for k in lags}
    return pd.concat([df, pd.DataFrame(new)], axis=1)


def add_targets(df, thresholds, horizons=HORIZONS, index_col="composite_smog_index"):
    """Targets for day t+h and the two baselines, within each city.

    target_index_h{h}: index on day t+h.  target_spike_h{h}: 1 if that index is at or
    above the city's spike threshold (Person A's saved training thresholds, not new ones).
    Rows whose t+h falls after the window end get NaN (2024 stays sealed).
    persist_index / persist_spike: today's values ("tomorrow = today" baseline).
    index_lag1..3: yesterday's smog and the two days before.
    """
    df = df.sort_values(["city", "date"]).reset_index(drop=True)
    _assert_daily(df)
    g = df.groupby("city", sort=False)
    thr = df["city"].map(thresholds)
    for h in horizons:
        future = g[index_col].shift(-h)
        df[f"target_index_h{h}"] = future
        df[f"target_spike_h{h}"] = (future >= thr).astype("Int64").where(future.notna())
    df["persist_index"] = df[index_col]
    df["persist_spike"] = df["smog_spike"]
    for k in LAGS:
        df[f"index_lag{k}"] = g[index_col].shift(k)
    return df


# ------------------------------------------------------------------
# Encoding and split
# ------------------------------------------------------------------
def wind_sector(deg, stagnant):
    """8-sector label of the wind-from direction; 'calm' on stagnant days (direction is noise)."""
    idx = (((deg % 360) + 22.5) // 45).astype(int) % 8
    lab = pd.Series(np.array(SECTORS)[idx], index=deg.index)
    return lab.where(stagnant == 0, "calm")


def encode(df, reference_city="Lahore"):
    """0/1 dummy columns: city (Lahore = reference), country, harvest season, month
    (January = reference) and wind sector (calm = reference)."""
    df = df.copy()
    for c in CITIES:
        if c != reference_city:
            df["city_" + c.lower().replace(" ", "_")] = (df["city"] == c).astype("int8")
    df["is_india"] = (df["country"] == "IN").astype("int8")
    df["near_border"] = df["city"].isin(NEAR_BORDER).astype("int8")
    df["harvest_season"] = df["date"].dt.month.isin([10, 11, 12]).astype("int8")
    for m in range(2, 13):
        df[f"month_{m:02d}"] = (df["date"].dt.month == m).astype("int8")
    df["wind_sector"] = wind_sector(df["wind_dir_daily_deg"], df["stagnant"])
    for s in SECTORS:
        df[f"wind_from_{s}"] = (df["wind_sector"] == s).astype("int8")
    return df


def add_split(df, train_start, train_end, skip_start, skip_end, valid_start, valid_end):
    """split = train / skip / validation (shared rules). The 3-day skip equals the longest
    horizon, so no training target falls inside the validation period."""
    d = df["date"]
    split = pd.Series("outside", index=df.index)
    split[(d >= train_start) & (d <= train_end)] = "train"
    split[(d >= skip_start) & (d <= skip_end)] = "skip"
    split[(d >= valid_start) & (d <= valid_end)] = "validation"
    assert (split != "outside").all(), "every row in the window must be train, skip or validation"
    df = df.copy()
    df["split"] = split
    df["is_train"] = (split == "train").astype("int8")
    return df


def order_rows(df):
    """Final row order: cities in the shared-dictionary order (Pakistan first), then date."""
    rank = df["city"].map({c: i for i, c in enumerate(CITIES)})
    return df.assign(_r=rank).sort_values(["_r", "date"]).drop(columns="_r").reset_index(drop=True)


def build_master(start, end, train_start, train_end, skip_start, skip_end,
                 valid_start, valid_end, clean_dir=CLEAN_DIR, verbose=True, sealed_from=SEALED_FROM):
    """Whole of Part 2A in one call. Returns (master, log) where log holds the checks."""
    aq = load_aq(start, end, clean_dir)
    wx = load_weather(start, end, lead_in_days=max(LAGS), clean_dir=clean_dir)
    fire = load_fire_wide(start, end, lead_in_days=max(LAGS), clean_dir=clean_dir)
    params = load_aq_params(clean_dir)

    # lags of weather and fire use the 3 days before the window, then the lead-in is cut
    wx = cut_window(add_lags(wx, WEATHER_LAG_COLS), start, end)
    fire = cut_window(add_lags(fire, FIRE_LAG_COLS), start, end)

    checks = [check_keys(t, n, start, end, sealed_from=sealed_from) for t, n in [(aq, "AQ (A)"), (wx, "weather (B)"), (fire, "fire (C)")]]

    spine = build_spine(start, end)
    log = {"checks": pd.DataFrame(checks), "spine_rows": len(spine), "joins": []}
    master = spine
    for table, name in [(aq, "AQ"), (wx, "weather"), (fire, "fire")]:
        master, matched = join_one_to_one(master, table, name)
        log["joins"].append({"join": name, "rows_after": len(master), "rows_matched": matched,
                             "columns_after": master.shape[1]})
    log["joins"] = pd.DataFrame(log["joins"])

    master = add_targets(master, params["spike_threshold_mean_index"])
    master = encode(master)
    master = add_split(master, train_start, train_end, skip_start, skip_end, valid_start, valid_end)
    master = order_rows(master)
    if verbose:
        print(f"master: {master.shape[0]:,} rows x {master.shape[1]} columns")
    return master, log


# ------------------------------------------------------------------
# Data dictionary
# ------------------------------------------------------------------
def _describe(col):
    """(meaning, unit, source, owner) for one master column, from its name."""
    A, B, C, M = "Open-Meteo Air Quality API", "Open-Meteo Historical Weather API", "NASA FIRMS VIIRS (NOAA-20)", "derived in merge"
    base = col.split("_lag")[0]
    lag = f" on day t-{col.split('_lag')[1]}" if "_lag" in col and col.split("_lag")[1].isdigit() else ""
    if col in KEYS:
        return {"city": ("City name (11 cities)", "-", "shared dictionary", "B"),
                "country": ("Country code: PK = Pakistan, IN = India", "-", "shared dictionary", "B"),
                "date": ("Local date (UTC+5)", "date", "all streams", "B")}[col]
    if col.startswith("target_index_h"):
        return (f"Composite Smog Index on day t+{col[-1]} (response)", "z-score units", M, "B")
    if col.startswith("target_spike_h"):
        return (f"Spike label on day t+{col[-1]} with A's training thresholds (response)", "0/1", M, "B")
    if col == "persist_index":
        return ("Baseline: today's index used as the forecast", "z-score units", M, "B")
    if col == "persist_spike":
        return ("Baseline: today's spike label used as the forecast", "0/1", M, "B")
    if col.startswith("index_lag"):
        return (f"Composite Smog Index{lag}", "z-score units", M, "B")
    if col.startswith("city_"):
        return (f"1 if city is {col[5:].replace('_', ' ').title()} (reference: Lahore)", "0/1", M, "B")
    if col == "is_india":
        return ("1 if the city is in Indian Punjab", "0/1", M, "B")
    if col == "near_border":
        return ("1 if the city is a Pakistani border city (Lahore, Sialkot)", "0/1", M, "B")
    if col == "harvest_season":
        return ("1 if the date is in October-December", "0/1", M, "B")
    if col.startswith("month_"):
        return (f"1 if the month is {col[-2:]} (reference: January)", "0/1", M, "B")
    if col == "wind_sector":
        return ("Wind-from sector (8 compass sectors, 'calm' on stagnant days)", "category", M, "B")
    if col.startswith("wind_from_"):
        return (f"1 if the daily wind comes from {col[10:].upper()} (reference: calm)", "0/1", M, "B")
    if col == "split":
        return ("train / skip / validation (shared rules)", "category", M, "B")
    if col == "is_train":
        return ("1 if the row is in the training period", "0/1", M, "B")
    # ---- AQ (A)
    aq_meaning = {"composite_smog_index": "Composite Smog Index (weighted z-scores, daily means)",
                  "composite_smog_index_max": "Composite Smog Index from daily maxima",
                  "spike_threshold": "City spike threshold (P90 of training Oct-Mar index)",
                  "spike_threshold_max": "City spike threshold for the max-based index",
                  "smog_spike": "1 if index >= city threshold", "smog_spike_max": "1 if max-based index >= its threshold",
                  "valid_hours": "Hours with AQ data in the day", "suspect_day": "1 if the day was flagged suspect (PM2.5 < 2 ug/m3)"}
    if base in aq_meaning:
        unit = "hours" if base == "valid_hours" else "0/1" if "spike" in base and "threshold" not in base or base == "suspect_day" else "z-score units"
        return (aq_meaning[base] + lag, unit, A, "A")
    pol = {"pm10": "PM10", "pm2_5": "PM2.5", "no2": "NO2", "so2": "SO2", "o3": "O3", "co": "CO", "dust": "Dust"}
    p = col.split("_")[0] if not col.startswith("pm2_5") else "pm2_5"
    if p in pol:
        stat = "daily mean" if "_mean" in col else "daily max"
        if col.endswith("_ugm3"):
            return (f"{pol[p]} {stat}", "ug/m3", A, "A")
        if col.endswith("_log"):
            return (f"log1p of {pol[p]} {stat}", "log(1+ug/m3)", A, "A")
        if col.endswith("_z"):
            return (f"{pol[p]} {stat}, z-score (training mean/SD, after log1p if skewed)", "z-score", A, "A")
        if col.endswith("_iqr_outlier"):
            return (f"1 if {pol[p]} {stat} is outside the 1.5xIQR fences", "0/1", A, "A")
    if col == "composite_smog_index_iqr_outlier":
        return ("1 if the index is outside the 1.5xIQR fences", "0/1", A, "A")
    # ---- weather (B)
    wx = {"temp_mean_c": ("Daily mean 2 m temperature", "deg C"), "temp_min_c": ("Daily min temperature", "deg C"),
          "temp_max_c": ("Daily max temperature", "deg C"), "temp_range_c": ("Daily temperature range (inversion proxy)", "deg C"),
          "rh_mean_pct": ("Daily mean relative humidity", "%"), "precip_sum_mm": ("Daily rainfall total", "mm"),
          "precip_log1p": ("log1p of daily rainfall", "log(1+mm)"), "rain_day": ("1 if rainfall >= 1 mm", "0/1"),
          "wind_speed_mean_kmh": ("Mean of hourly wind speeds", "km/h"), "n_hours": ("Hours of weather data in the day", "hours"),
          "u_mean": ("Daily mean east-west wind component (+ = towards east)", "km/h"),
          "v_mean": ("Daily mean north-south wind component (+ = towards north)", "km/h"),
          "vec_len_kmh": ("Length of the daily mean wind vector", "km/h"),
          "wind_dir_daily_deg": ("Daily wind-from direction (vector mean)", "deg from N"),
          "stagnant": ("1 if vec_len_kmh < 2 km/h (stagnation proxy)", "0/1")}
    root = base[:-2] if base.endswith("_z") else base
    if root in wx:
        meaning, unit = wx[root]
        if base.endswith("_z"):
            return (meaning + ", z-score (training mean/SD)" + lag, "z-score", B, "B")
        return (meaning + lag, unit, B, "B")
    if "_outlier_" in col:
        return (f"1 if {col.split('_outlier_')[0]} is an outlier ({col.split('_outlier_')[1]} rule)", "0/1", B, "B")
    # ---- fire (C)
    if col.startswith("out_z_") or col.startswith("out_iqr_"):
        rule = "|z| > 3" if col.startswith("out_z_") else "1.5xIQR"
        return (f"1 if {col.split('_', 2)[2]} is an outlier ({rule} rule)", "0/1", C, "C")
    if col.startswith("fire_"):
        parts = base.replace("_log1p", "").replace("_z", "").split("_")
        kind = "Number of fire detections" if parts[1] == "cnt" else "Sum of fire radiative power"
        origin = {"all": "all origins", "in": "India-origin", "pk": "Pakistan-origin"}[parts[-1]]
        setting = parts[2:-1]                       # e.g. ['up45', 'r300'] or ['r150', 'conf', 'h']
        radius = next(p[1:] for p in setting if p.startswith("r") and p[1:].isdigit())
        ring = f"within {radius} km"
        first = setting[0]
        cone = (f"{ring}, inside the +-{first[2:]} deg upwind cone" if first.startswith("up")
                else f"{ring}, inside the +-{first[4:]} deg downwind cone (placebo)" if first.startswith("down")
                else f"{ring}, high confidence only" if setting[-1] == "h"
                else f"{ring}, all confidence levels" if setting[-1] == "nhl"
                else f"{ring}, any direction")
        unit = "count" if parts[1] == "cnt" else "MW"
        if base.endswith("_log1p_z"):
            unit = "z-score"
            kind = "z-score of log1p of " + kind.lower()
        elif base.endswith("_log1p"):
            unit = "log(1+" + unit + ")"
            kind = "log1p of " + kind.lower()
        return (f"{kind}, {origin}, {cone}{lag}", unit, C, "C")
    return ("", "", "", "")


def data_dictionary(df):
    """One row per master column: meaning, unit, source, owner, dtype, missing count."""
    rows = []
    for col in df.columns:
        meaning, unit, source, owner = _describe(col)
        rows.append({"column": col, "meaning": meaning, "unit": unit, "source": source, "owner": owner,
                     "dtype": str(df[col].dtype), "missing": int(df[col].isna().sum())})
    out = pd.DataFrame(rows)
    assert (out["meaning"] != "").all(), f"undocumented columns: {out.loc[out['meaning'] == '', 'column'].tolist()}"
    return out


# ------------------------------------------------------------------
# Fire setting chosen in 2B step 6 (added to the master after the choice)
# ------------------------------------------------------------------
def setting_tag(cone, radius_km):
    """Column tag in Person C's naming style: 'up45_r300', 'down45_r300' or 'r300' (no cone)."""
    return f"r{radius_km}" if cone == "none" else f"{cone}_r{radius_km}"


def fire_setting_wide(long_df, cone, radius_km):
    """One cone/radius setting from the long table as wide columns
    fire_cnt_<tag>_{all,in,pk} and fire_frp_<tag>_{all,in,pk}."""
    sub = long_df[(long_df["cone"] == cone) & (long_df["radius_km"] == radius_km)]
    tag = setting_tag(cone, radius_km)
    wide = sub.pivot(index=KEYS, columns="origin", values=["fire_count", "frp_sum_mw"])
    wide.columns = [f"fire_{'cnt' if v == 'fire_count' else 'frp'}_{tag}_{o.lower()}" for v, o in wide.columns]
    wide = wide.reset_index()
    cnt = [c for c in wide.columns if c.startswith("fire_cnt_")]
    return wide, cnt


def add_fire_setting(master, cone, radius_km, start, end, lag_origins=("all", "in", "pk"),
                     clean_dir=CLEAN_DIR):
    """Join one fire setting onto the master (one-to-one) with lags 1-3 of its counts."""
    long_df = load_fire_long(start, end, lead_in_days=max(LAGS), clean_dir=clean_dir)
    wide, cnt = fire_setting_wide(long_df, cone, radius_km)
    assert wide[cnt].notna().all().all(), "fire counts must never be missing"
    wide[cnt] = wide[cnt].astype("int64")
    lag_cols = [c for c in cnt if c.rsplit("_", 1)[1] in lag_origins]
    wide = cut_window(add_lags(wide, lag_cols), start, end)
    keep = [c for c in wide.columns if c not in master.columns or c in KEYS]
    out, matched = join_one_to_one(master, wide[keep], f"fire {setting_tag(cone, radius_km)}")
    assert matched == len(master)
    return out


def add_log_z(df, cols, train_mask):
    """log1p, then z-score with training-period mean and SD only. Returns (df, params)."""
    df = df.copy()
    params = {}
    for c in cols:
        lg = np.log1p(df[c].astype(float))
        mu, sd = lg[train_mask].mean(), lg[train_mask].std()
        df[c + "_log1p"] = lg
        df[c + "_log1p_z"] = (lg - mu) / sd
        params[c + "_log1p"] = {"mean": float(mu), "std": float(sd)}
    return df, params
