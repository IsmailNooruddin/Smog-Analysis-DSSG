"""Milestone 5: automated ingestion of the raw Open-Meteo and NASA VIIRS files.

The Role 1 notebooks (air_quality.ipynb, weather.ipynb, fire.ipynb) hold their logic inline
and stop at 2023-12-31. This module ports that logic, step for step, into functions that take
the date window as an argument, so the 2024 wave goes through exactly the same cleaning.

Rules:
- Nothing is re-learned. Every scaling parameter, log decision and spike threshold comes from
  the JSON files saved in Milestones 2 (learned on 2022-08-04 to 2023-08-31). The learn_* helpers
  exist only to check that the frozen values are what the training rows give.
- Outlier fences (not saved in Milestone 2) are recomputed on the same reference rows the Role 1
  notebooks used, so the 2022-23 rows get the same flags.
- data_extension.ipynb checks that a run over 2022-01-01 to 2023-12-31 reproduces the committed
  Dataset/clean tables (section M5.2).

Observational unit of every daily table: 1 row = 1 city on 1 local (UTC+5) day.
"""
import json
import shutil
from pathlib import Path

import numpy as np
import pandas as pd

from src.config import (CITY_COORDS, CITY_COUNTRY, CLEAN_DIR, NASA_FILES, NASA_FILES_M5,
                        TRAIN_END, TRAIN_START, aq_path, nasa_path_m5, weather_path)

LOCAL_OFFSET = pd.Timedelta(hours=5)          # UTC+5 for every city (known limitation for India)

# ------------------------------------------------------------------
# Air quality (port of air_quality.ipynb, cells 0-42)
# ------------------------------------------------------------------
# File order of the AQ notebook (Pakistan alphabetical, then India); it sets the row order
AQ_ORDER = ["Faisalabad", "Islamabad", "Lahore", "Multan", "Rahim Yar Khan", "Rawalpindi", "Sialkot",
            "Amritsar", "Ferozepur", "Jalandhar", "Ludhiana"]
AQ_SHORT = {"pm10": "pm10_ugm3", "pm2_5": "pm2_5_ugm3", "nitrogen_dioxide": "no2_ugm3",
            "sulphur_dioxide": "so2_ugm3", "ozone": "o3_ugm3", "carbon_monoxide": "co_ugm3",
            "dust": "dust_ugm3"}
POLLUTANTS = ["pm10_ugm3", "pm2_5_ugm3", "no2_ugm3", "so2_ugm3", "o3_ugm3", "co_ugm3", "dust_ugm3"]
MAX_POLLUTANTS = POLLUTANTS[:-1]               # no daily maximum for dust
MIN_VALID_HOURS = 18
GLITCH_PM25 = 2.0                              # PM2.5 below 2 ug/m3 in any hour -> suspect date
WINTER_MONTHS = [10, 11, 12, 1, 2, 3]


def _read_table(path, **kw):
    path = Path(path)
    return pd.read_excel(path, **kw) if path.suffix == ".xlsx" else pd.read_csv(path, **kw)


def read_aq_raw(city):
    """One city's hourly AQ file: rename by name prefix, time_utc sorted, city and country added."""
    df = _read_table(aq_path(city), skiprows=3)
    new = []
    for col in df.columns:
        name = col
        for start, short in AQ_SHORT.items():
            if col.startswith(start):
                name = short
        new.append(name)
    df.columns = new
    df["time"] = pd.to_datetime(df["time"])
    df = df.rename(columns={"time": "time_utc"}).sort_values("time_utc").reset_index(drop=True)
    df["city"] = city
    df["country"] = CITY_COUNTRY[city]
    return df


def aq_hourly(raw_start, raw_end):
    """All 11 AQ files stacked, local time added (+5 h, then the date), cut to the raw window."""
    aq = pd.concat([read_aq_raw(c) for c in AQ_ORDER], ignore_index=True)
    aq["time_local"] = aq["time_utc"] + LOCAL_OFFSET
    aq["date"] = aq["time_local"].dt.normalize()
    aq["hour"] = aq["time_local"].dt.hour
    keep = (aq["date"] >= pd.Timestamp(raw_start)) & (aq["date"] <= pd.Timestamp(raw_end))
    aq = aq[keep].reset_index(drop=True)
    return aq[["city", "country", "time_utc", "time_local", "date", "hour"] + POLLUTANTS]


def aq_clean_hourly(aq):
    """Negative values -> 0, hours with every pollutant empty dropped, gaps of <= 6 h interpolated."""
    out = aq.copy()
    out[POLLUTANTS] = out[POLLUTANTS].clip(lower=0)
    out = out.dropna(subset=POLLUTANTS, how="all").reset_index(drop=True)
    for city in out["city"].unique():
        m = out["city"] == city
        out.loc[m, POLLUTANTS] = out.loc[m, POLLUTANTS].interpolate(limit=6, limit_area="inside")
    return out


def aq_daily_raw(aq_clean):
    """Daily mean (7 pollutants) and max (6), valid hours, the 18-hour rule and suspect_day."""
    g = aq_clean.groupby(["city", "date"], sort=False)
    mean = g[POLLUTANTS].mean()
    mx = g[MAX_POLLUTANTS].max()
    mean.columns = [c.replace("_ugm3", "_mean_ugm3") for c in mean.columns]
    mx.columns = [c.replace("_ugm3", "_max_ugm3") for c in mx.columns]
    daily = pd.concat([mean, mx], axis=1)
    daily["valid_hours"] = g["pm2_5_ugm3"].count()
    daily = daily.reset_index()
    daily["country"] = daily["city"].map(aq_clean.drop_duplicates("city").set_index("city")["country"])
    daily = daily[daily["valid_hours"] >= MIN_VALID_HOURS].reset_index(drop=True)
    first = ["city", "country", "date", "valid_hours"]
    daily = daily[first + [c for c in daily.columns if c not in first]]
    glitch = aq_clean[aq_clean["pm2_5_ugm3"] < GLITCH_PM25]
    daily["suspect_day"] = daily["date"].isin(glitch["date"].unique()).astype(int)
    return daily


def aq_train_mask(daily, train_start=TRAIN_START, train_end=TRAIN_END):
    """Training days of the AQ notebook: inside the training window and not a suspect day."""
    d = daily["date"]
    return (d >= pd.Timestamp(train_start)) & (d <= pd.Timestamp(train_end)) & (daily["suspect_day"] == 0)


def _index(daily, weights, kind):
    total = 0.0
    for name, w in weights.items():
        total = total + w * daily[f"{name}_{kind}_z"]
    return total


def aq_apply_params(daily, params, fence_mask):
    """Frozen log1p/z-scores, both indexes, thresholds and spike labels, then the IQR outlier flags.
    fence_mask = the reference rows for the IQR fences (the AQ notebook's training days)."""
    daily = daily.copy()
    transform = [c for c in daily.columns if c.endswith("_mean_ugm3")] + \
                [c for c in daily.columns if c.endswith("_max_ugm3")]
    for col in transform:
        p = params["zscore"][col]
        values = daily[col]
        if p["log1p"]:
            values = np.log1p(values)
            daily[col.replace("_ugm3", "_log")] = values
        daily[col.replace("_ugm3", "_z")] = (values - p["mean"]) / p["std"]
    w = params["index_weights"]
    daily["composite_smog_index"] = _index(daily, w, "mean")
    daily["spike_threshold"] = daily["city"].map(params["spike_threshold_mean_index"])
    daily["smog_spike"] = (daily["composite_smog_index"] >= daily["spike_threshold"]).astype(int)
    daily["composite_smog_index_max"] = _index(daily, w, "max")
    daily["spike_threshold_max"] = daily["city"].map(params["spike_threshold_max_index"])
    daily["smog_spike_max"] = (daily["composite_smog_index_max"] >= daily["spike_threshold_max"]).astype(int)
    ref = daily[fence_mask]
    for col in [c for c in daily.columns if c.endswith("_mean_ugm3")] + ["composite_smog_index"]:
        q1, q3 = ref[col].quantile(0.25), ref[col].quantile(0.75)
        iqr = q3 - q1
        flag = col.replace("_ugm3", "") + "_iqr_outlier"
        daily[flag] = ((daily[col] < q1 - 1.5 * iqr) | (daily[col] > q3 + 1.5 * iqr)).astype(int)
    return daily


def learn_aq_params(daily, train_start=TRAIN_START, train_end=TRAIN_END, skew_limit=1.0):
    """What the AQ notebook learns on its training days. Used only to check the frozen JSON."""
    tr = aq_train_mask(daily, train_start, train_end)
    winter = daily["date"].dt.month.isin(WINTER_MONTHS)
    transform = [c for c in daily.columns if c.endswith("_mean_ugm3")] + \
                [c for c in daily.columns if c.endswith("_max_ugm3")]
    z = {}
    for col in transform:
        use_log = bool(daily.loc[tr, col].skew() > skew_limit)
        v = np.log1p(daily[col]) if use_log else daily[col]
        z[col] = {"log1p": use_log, "mean": float(v[tr].mean()), "std": float(v[tr].std())}
    tmp = aq_apply_params(daily, {"zscore": z, "index_weights": {"pm2_5": .40, "pm10": .12, "no2": .12,
                                                                  "so2": .12, "o3": .12, "co": .12},
                                  "spike_threshold_mean_index": {}, "spike_threshold_max_index": {}}, tr)
    thr = tmp[tr & winter].groupby("city")["composite_smog_index"].quantile(0.90)
    thr_max = tmp[tr & winter].groupby("city")["composite_smog_index_max"].quantile(0.90)
    return {"zscore": z, "spike_threshold_mean_index": thr.to_dict(), "spike_threshold_max_index": thr_max.to_dict()}


def build_aq(raw_start, raw_end, params):
    """Raw files -> final daily AQ table (same 55 columns as Dataset/clean/aq_daily.parquet)."""
    hourly = aq_hourly(raw_start, raw_end)
    daily = aq_daily_raw(aq_clean_hourly(hourly))
    return aq_apply_params(daily, params, aq_train_mask(daily)), hourly


# ------------------------------------------------------------------
# Weather (port of weather.ipynb, cells 4-97)
# ------------------------------------------------------------------
WX_RENAME = {"temperature_2m (°C)": "temp_c", "relative_humidity_2m (%)": "rh_pct",
             "precipitation (mm)": "precip_mm", "wind_speed_10m (km/h)": "wind_speed_kmh",
             "wind_direction_10m (°)": "wind_dir_deg"}
WX_VALUES = ["temp_c", "rh_pct", "precip_mm", "wind_speed_kmh", "wind_dir_deg"]
STAGNANT_KMH = 2
RAIN_DAY_MM = 1
WX_Z_COLS = ["temp_mean_c", "temp_min_c", "temp_max_c", "temp_range_c", "rh_mean_pct",
             "precip_log1p", "wind_speed_mean_kmh", "vec_len_kmh", "u_mean", "v_mean"]
WX_AUDIT_COLS = ["temp_mean_c", "temp_range_c", "rh_mean_pct", "precip_sum_mm",
                 "wind_speed_mean_kmh", "vec_len_kmh"]


def read_weather_raw(city):
    """One city's hourly weather file, columns renamed by name (Ludhiana's order differs)."""
    df = _read_table(weather_path(city), skiprows=3).rename(columns=WX_RENAME)
    assert set(WX_RENAME.values()) <= set(df.columns), f"missing weather columns for {city}"
    df["time"] = pd.to_datetime(df["time"])
    df.insert(0, "country", CITY_COUNTRY[city])
    df.insert(0, "city", city)
    return df


def weather_hourly(raw_start, raw_end):
    """Every hour per city between its first and last record (missing hours become empty rows),
    local time (+5 h) and the date, cut to the raw window, plus the U/V wind components."""
    raw = pd.concat([read_weather_raw(c) for c in CITY_COUNTRY], ignore_index=True)
    frames = []
    for city, d in raw.groupby("city"):
        d = d.set_index("time")
        d = d.reindex(pd.date_range(d.index.min(), d.index.max(), freq="h"))
        d["city"], d["country"] = city, CITY_COUNTRY[city]
        d.index.name = "time"
        frames.append(d.reset_index())
    wx = pd.concat(frames, ignore_index=True)[raw.columns]
    wx = wx.rename(columns={"time": "time_gmt"})
    wx["datetime_pkt"] = wx["time_gmt"] + LOCAL_OFFSET
    wx["date"] = wx["datetime_pkt"].dt.normalize()
    wx["hour"] = wx["datetime_pkt"].dt.hour
    wx = wx[["city", "country", "datetime_pkt", "date", "hour", "time_gmt"] + WX_VALUES]
    wx = wx[(wx["date"] >= pd.Timestamp(raw_start)) & (wx["date"] <= pd.Timestamp(raw_end))].reset_index(drop=True)
    a = np.deg2rad(wx["wind_dir_deg"])
    wx["u_kmh"] = -wx["wind_speed_kmh"] * np.sin(a)
    wx["v_kmh"] = -wx["wind_speed_kmh"] * np.cos(a)
    return wx


def wind_daily(wx):
    """Daily vector-mean wind, its direction (FROM) and the stagnation flag (< 2 km/h)."""
    w = (wx.groupby(["city", "country", "date"])
         .agg(u_mean=("u_kmh", "mean"), v_mean=("v_kmh", "mean"), n_hours=("hour", "size")).reset_index())
    w["vec_len_kmh"] = np.hypot(w["u_mean"], w["v_mean"])
    w["wind_dir_daily_deg"] = (np.degrees(np.arctan2(-w["u_mean"], -w["v_mean"])) + 360) % 360
    w["stagnant"] = (w["vec_len_kmh"] < STAGNANT_KMH).astype(int)
    return w


def build_weather(raw_start, raw_end, zparams, train_start=TRAIN_START, train_end=TRAIN_END):
    """Raw files -> (wx_daily, wind_daily, hourly). Frozen z-scores; outlier fences from training rows."""
    wx = weather_hourly(raw_start, raw_end)
    wind = wind_daily(wx)
    d = (wx.groupby(["city", "country", "date"])
         .agg(temp_mean_c=("temp_c", "mean"), temp_min_c=("temp_c", "min"), temp_max_c=("temp_c", "max"),
              rh_mean_pct=("rh_pct", "mean"), precip_sum_mm=("precip_mm", "sum"),
              wind_speed_mean_kmh=("wind_speed_kmh", "mean")).reset_index())
    d["temp_range_c"] = d["temp_max_c"] - d["temp_min_c"]
    # The raw rain has 0.1 mm resolution; rounding the daily sum removes float noise such as
    # 0.1 + 0.3 + 0.6 = 0.9999999999999999, whose result depends on the summation order (decision N3)
    d["rain_day"] = (d["precip_sum_mm"].round(6) >= RAIN_DAY_MM).astype(int)
    d = d.merge(wind[["city", "date", "n_hours", "u_mean", "v_mean", "vec_len_kmh", "wind_dir_daily_deg",
                      "stagnant"]], on=["city", "date"], how="left", validate="one_to_one")
    d["precip_log1p"] = np.log1p(d["precip_sum_mm"])
    for c in WX_Z_COLS:
        d[f"{c}_z"] = (d[c] - zparams[c]["mean"]) / zparams[c]["std"]
    eda = d[d["date"].between(pd.Timestamp(train_start), pd.Timestamp(train_end))]
    for c in WX_AUDIT_COLS:
        x = eda[c]
        mean, std = x.mean(), x.std()
        q1, q3 = x.quantile(0.25), x.quantile(0.75)
        low, high = q1 - 1.5 * (q3 - q1), q3 + 1.5 * (q3 - q1)
        d[f"{c}_outlier_z"] = ((d[c] - mean).abs() > 3 * std).astype(int)
        d[f"{c}_outlier_iqr"] = ((d[c] < low) | (d[c] > high)).astype(int)
    d = d.sort_values(["city", "date"]).reset_index(drop=True)
    return d, wind, wx


def learn_weather_params(wx_daily, train_start=TRAIN_START, train_end=TRAIN_END):
    tr = wx_daily[wx_daily["date"].between(pd.Timestamp(train_start), pd.Timestamp(train_end))]
    return {c: {"mean": float(tr[c].mean()), "std": float(tr[c].std())} for c in WX_Z_COLS}


# ------------------------------------------------------------------
# Fire (port of fire.ipynb, cells 1-53)
# ------------------------------------------------------------------
BOX = (26, 37, 68, 79)                          # lat min, lat max, lon min, lon max
RADII_KM = [50, 100, 150, 200, 300]
CONES = {"up30": (0, 30), "up45": (0, 45), "up60": (0, 60), "down45": (180, 45)}
EARTH_R_KM = 6371.0
FIRE_TRANSFORM_COLS = ["fire_cnt_r150_in", "fire_cnt_r150_pk", "fire_cnt_r150_all",
                       "fire_frp_r150_in", "fire_frp_r150_pk", "fire_frp_r150_all",
                       "fire_cnt_up45_r150_in", "fire_frp_up45_r150_in",
                       "fire_cnt_down45_r150_in", "fire_frp_down45_r150_in"]


def haversine_km(lat1, lon1, lat2, lon2):
    lat1, lon1, lat2, lon2 = map(np.radians, (lat1, lon1, lat2, lon2))
    a = np.sin((lat2 - lat1) / 2) ** 2 + np.cos(lat1) * np.cos(lat2) * np.sin((lon2 - lon1) / 2) ** 2
    return 2 * EARTH_R_KM * np.arcsin(np.sqrt(a))


def bearing_deg(lat1, lon1, lat2, lon2):
    lat1, lon1, lat2, lon2 = map(np.radians, (lat1, lon1, lat2, lon2))
    x = np.sin(lon2 - lon1) * np.cos(lat2)
    y = np.cos(lat1) * np.sin(lat2) - np.sin(lat1) * np.cos(lat2) * np.cos(lon2 - lon1)
    return (np.degrees(np.arctan2(x, y)) + 360) % 360


def angle_diff(a, b):
    return np.abs((np.asarray(a) - np.asarray(b) + 180) % 360 - 180)


def cone_mask(bearing, wind_from, half_angle, offset=0):
    return angle_diff(bearing, (np.asarray(wind_from) + offset) % 360) <= half_angle


def fire_files(years):
    """(country, year) -> file name, in the order fire.ipynb reads them (2022-23 first)."""
    return {k: v for k, v in NASA_FILES_M5.items() if k[1] in years}


def read_fire_raw(files):
    tables = []
    for (country, year), name in files.items():
        df = pd.read_csv(nasa_path_m5(country, year), dtype={"acq_time": str})
        df["origin_country"] = country
        df["source_file"] = name
        tables.append(df)
    return pd.concat(tables, ignore_index=True)


def fire_gap_days(raw, years):
    """UTC dates with no detection at all in either country file (whole of India and Pakistan).
    Thousands of fires are detected on a normal day, so an empty day is a data gap, not 'no fires'."""
    rows = []
    for y in years:
        days = pd.date_range(f"{y}-01-01", f"{y}-12-31").strftime("%Y-%m-%d")
        seen = {c: set(raw.loc[(raw["origin_country"] == c), "acq_date"]) for c in ["IN", "PK"]}
        for d in days:
            rows.append({"date": pd.Timestamp(d), "no_detection_in": d not in seen["IN"],
                         "no_detection_pk": d not in seen["PK"]})
    out = pd.DataFrame(rows)
    out["fire_gap_day"] = (out["no_detection_in"] & out["no_detection_pk"]).astype(int)
    return out


def _to_local_date(df):
    utc = pd.to_datetime(df["acq_date"] + " " + df["acq_time"].str.zfill(4), format="%Y-%m-%d %H%M")
    df = df.copy()
    df["time_utc"] = utc
    df["time_local"] = utc + LOCAL_OFFSET
    df["date"] = df["time_local"].dt.normalize()
    return df


def filter_fires(raw, start, end):
    """Box, type 0 (vegetation), local date inside the window. Returns (all confidence levels, audit)."""
    audit = []
    lat0, lat1, lon0, lon1 = BOX
    f = raw[raw["latitude"].between(lat0, lat1) & raw["longitude"].between(lon0, lon1)].copy()
    audit.append(("bounding box 26-37 N, 68-79 E", len(raw), len(f)))
    n = len(f)
    f = f[f["type"] == 0].copy()
    audit.append(("type 0 (vegetation fire)", n, len(f)))
    n_conf = int(f["confidence"].isin(["n", "h"]).sum())
    audit.append(("confidence n and h (main version)", len(f), n_conf))
    f = _to_local_date(f)
    inside = f["date"].between(pd.Timestamp(start), pd.Timestamp(end))
    n_main = int((inside & f["confidence"].isin(["n", "h"])).sum())
    audit.append(("local date inside the window (main version)", n_conf, n_main))
    return f[inside].copy(), pd.DataFrame(audit, columns=["step", "rows_before", "rows_after"])


def city_fire_pairs(df, max_km=max(RADII_KM)):
    out = []
    lat, lon = df["latitude"].to_numpy(), df["longitude"].to_numpy()
    for city, (clat, clon) in CITY_COORDS.items():
        dist = haversine_km(clat, clon, lat, lon)
        near = dist <= max_km
        part = df.loc[near, ["date", "origin_country", "frp", "confidence"]].copy()
        part.insert(0, "city", city)
        part["dist_km"] = dist[near]
        part["bearing_deg"] = bearing_deg(clat, clon, lat[near], lon[near])
        out.append(part)
    return pd.concat(out, ignore_index=True)


def _daily_counts(p, cone_name, grid):
    rows = []
    for r in RADII_KM:
        sub = p[p["dist_km"] <= r]
        for origin in ["IN", "PK", "ALL"]:
            s = sub if origin == "ALL" else sub[sub["origin_country"] == origin]
            g = s.groupby(["city", "date"]).agg(fire_count=("frp", "size"), frp_sum_mw=("frp", "sum"))
            g = g.reindex(grid, fill_value=0).reset_index()
            g["radius_km"], g["origin"], g["cone"] = r, origin, cone_name
            rows.append(g)
    return pd.concat(rows, ignore_index=True)


def _wide_from(long, cone, radius, prefix, grid):
    s = long[(long["cone"] == cone) & (long["radius_km"] == radius)]
    w = s.pivot_table(index=["city", "date"], columns="origin", values=["fire_count", "frp_sum_mw"])
    w.columns = [f"{'fire_cnt' if v == 'fire_count' else 'fire_frp'}_{prefix}_{o.lower()}" for v, o in w.columns]
    return w.reindex(grid)


def build_fire(start, end, wind, zparams, years, outlier_ref_end="2023-12-31"):
    """Raw VIIRS files -> (fire_wide, fire_long, gaps, audit).

    wind: daily wind table (wind_daily). zparams: frozen fire_zscore_params.json.
    The outlier flags of fire.ipynb used the mean, SD and quartiles of every row it had
    (2022-01-01 to 2023-12-31); outlier_ref_end keeps that reference set fixed for 2024.
    """
    raw = read_fire_raw(fire_files(years))
    gaps = fire_gap_days(raw, years)
    nhl, audit = filter_fires(raw, start, end)
    pairs_nhl = city_fire_pairs(nhl)
    pairs = pairs_nhl[pairs_nhl["confidence"].isin(["n", "h"])].copy()
    pairs_h = pairs_nhl[pairs_nhl["confidence"] == "h"].copy()

    cities = list(CITY_COORDS)
    grid = pd.MultiIndex.from_product([cities, pd.date_range(start, end, freq="D")], names=["city", "date"])
    long_radius = _daily_counts(pairs, "none", grid)
    long_radius["fire_count"] = long_radius["fire_count"].astype(int)

    w = wind.copy()
    w["date"] = pd.to_datetime(w["date"]).dt.normalize()
    w = w.rename(columns={"wind_dir_daily_deg": "wind_dir_from_deg"})
    has_wind = pd.Series(True, index=pd.MultiIndex.from_frame(w[["city", "date"]])).reindex(grid, fill_value=False)
    p = pairs.merge(w[["city", "date", "wind_dir_from_deg", "stagnant"]], on=["city", "date"], how="inner")
    out = []
    for name, (offset, half) in CONES.items():
        keep = cone_mask(p["bearing_deg"], p["wind_dir_from_deg"], half, offset) | (p["stagnant"] == 1)
        out.append(_daily_counts(p[keep], name, grid))
    long_cone = pd.concat(out, ignore_index=True)
    no_wind = ~has_wind.reindex(pd.MultiIndex.from_frame(long_cone[["city", "date"]])).to_numpy()
    long_cone.loc[no_wind, ["fire_count", "frp_sum_mw"]] = np.nan
    stagnant = w.set_index(["city", "date"])["stagnant"].reindex(grid)

    fire_long = pd.concat([long_radius, long_cone], ignore_index=True)
    fire_long.insert(1, "country", fire_long["city"].map(CITY_COUNTRY))
    fire_long = fire_long[["city", "country", "date", "cone", "radius_km", "origin", "fire_count", "frp_sum_mw"]]

    parts = [_wide_from(fire_long, "none", 150, "r150", grid),
             _wide_from(fire_long, "up45", 150, "up45_r150", grid),
             _wide_from(fire_long, "down45", 150, "down45_r150", grid),
             _wide_from(_daily_counts(pairs_h[pairs_h["dist_km"] <= 150], "none", grid), "none", 150,
                        "r150_conf_h", grid),
             _wide_from(_daily_counts(pairs_nhl[pairs_nhl["dist_km"] <= 150], "none", grid), "none", 150,
                        "r150_conf_nhl", grid)]
    wide = pd.concat(parts, axis=1)
    wide["stagnant"] = stagnant
    wide = wide.reset_index()
    wide.insert(1, "country", wide["city"].map(CITY_COUNTRY))
    cnt = [c for c in wide.columns if c.startswith("fire_cnt")]
    wide[cnt] = wide[cnt].round().astype("Int64")
    wide["stagnant"] = wide["stagnant"].astype("Int64")

    ref = wide["date"] <= pd.Timestamp(outlier_ref_end)
    for col in ["fire_cnt_r150_all", "fire_frp_r150_all", "fire_cnt_r150_in"]:
        s = wide[col].astype(float)
        r = s[ref]
        z = (s - r.mean()) / r.std()
        q1, q3 = r.quantile([0.25, 0.75])
        iqr = q3 - q1
        wide[f"out_z_{col}"] = (z.abs() > 3).astype(int)
        wide[f"out_iqr_{col}"] = ((s < q1 - 1.5 * iqr) | (s > q3 + 1.5 * iqr)).astype(int)
    for col in FIRE_TRANSFORM_COLS:
        wide[f"{col}_log1p"] = np.log1p(wide[col].astype(float))
    for col in FIRE_TRANSFORM_COLS:
        lc = f"{col}_log1p"
        wide[f"{lc}_z"] = (wide[lc] - zparams[lc]["mean"]) / zparams[lc]["std"]
    return wide, fire_long, gaps, audit


def learn_fire_params(fire_wide, train_start=TRAIN_START, train_end=TRAIN_END):
    tr = fire_wide["date"].between(pd.Timestamp(train_start), pd.Timestamp(train_end))
    return {f"{c}_log1p": {"mean": float(fire_wide.loc[tr, f"{c}_log1p"].mean()),
                           "std": float(fire_wide.loc[tr, f"{c}_log1p"].std())} for c in FIRE_TRANSFORM_COLS}


# ------------------------------------------------------------------
# Frozen parameters, schema report, comparison and writing
# ------------------------------------------------------------------
def load_frozen_params(clean_dir=CLEAN_DIR):
    """The Milestone 2 parameters: AQ (z-scores, weights, thresholds), weather and fire z-scores,
    Role 2 (fire setting, fire log1p z-scores, weather-trap cut-offs)."""
    out = {}
    for key, name in [("aq", "aq_params.json"), ("weather", "weather_zscore_params.json"),
                      ("fire", "fire_zscore_params.json"), ("role2", "role2_params.json")]:
        with open(Path(clean_dir) / name, encoding="utf-8") as f:
            out[key] = json.load(f)
    return out


def _header(path):
    meta = _read_table(path, nrows=1)
    return {"latitude": float(meta["latitude"].iloc[0]), "longitude": float(meta["longitude"].iloc[0]),
            "timezone": str(meta["timezone"].iloc[0]), "utc_offset_seconds": int(meta["utc_offset_seconds"].iloc[0])}


def schema_report(new_wave_start="2024-01-01", new_wave_end="2024-12-31", fire_years=(2022, 2023, 2024)):
    """One row per raw file: format, header metadata, raw column order, rows, time range,
    duplicate and missing hours, and the share of the new wave the file covers."""
    lo, hi = pd.Timestamp(new_wave_start), pd.Timestamp(new_wave_end) + pd.Timedelta(hours=23)
    rows = []
    for stream, path_fn in [("air quality", aq_path), ("weather", weather_path)]:
        for city in CITY_COUNTRY:
            path = path_fn(city)
            df = _read_table(path, skiprows=3)
            t = pd.to_datetime(df["time"])
            vals = df.drop(columns="time")
            has = vals.notna().all(axis=1)
            hdr = _header(path)
            local = t + LOCAL_OFFSET
            nw = (local >= lo) & (local <= hi)
            expected = int(((hi - lo) / pd.Timedelta(hours=1)) + 1)
            rows.append({
                "stream": stream, "city": city, "country": CITY_COUNTRY[city], "file": path.name,
                "format": path.suffix.lstrip("."), "timezone": hdr["timezone"],
                "utc_offset_s": hdr["utc_offset_seconds"], "columns": len(df.columns),
                "column_order": " | ".join(df.columns[1:]),
                "rows": len(df), "first_hour_utc": t.min(), "last_hour_utc": t.max(),
                "first_hour_with_data_utc": t[has].min(), "last_hour_with_data_utc": t[has].max(),
                "duplicate_hours": int(t.duplicated().sum()),
                "new_wave_hours_expected": expected,
                "new_wave_hours_with_data": int((nw & has).sum()),
                "new_wave_coverage_pct": 100 * (nw & has).sum() / expected,
            })
    for (country, year), name in fire_files(fire_years).items():
        path = nasa_path_m5(country, year)
        df = pd.read_csv(path, dtype={"acq_time": str})
        days = pd.date_range(f"{year}-01-01", f"{year}-12-31")
        rows.append({
            "stream": "fire", "city": "(all)", "country": country, "file": name, "format": "csv",
            "timezone": "UTC (acq_date, acq_time)", "utc_offset_s": 0, "columns": len(df.columns),
            "column_order": " | ".join(df.columns), "rows": len(df),
            "first_hour_utc": pd.Timestamp(df["acq_date"].min()), "last_hour_utc": pd.Timestamp(df["acq_date"].max()),
            "first_hour_with_data_utc": pd.Timestamp(df["acq_date"].min()),
            "last_hour_with_data_utc": pd.Timestamp(df["acq_date"].max()),
            "duplicate_hours": int(df.duplicated(["latitude", "longitude", "acq_date", "acq_time"]).sum()),
            "new_wave_hours_expected": len(days), "new_wave_hours_with_data": int(df["acq_date"].nunique()),
            "new_wave_coverage_pct": 100 * df["acq_date"].nunique() / len(days),
        })
    out = pd.DataFrame(rows)
    out.loc[out["stream"] == "fire", ["new_wave_hours_expected", "new_wave_hours_with_data"]] = \
        out.loc[out["stream"] == "fire", ["new_wave_hours_expected", "new_wave_hours_with_data"]]
    return out


def compare_frames(new, old, keys=("city", "date"), atol=1e-9, skip=()):
    """Row-for-row comparison after sorting by the keys. Returns one row per shared column with the
    number of cells that differ (numbers beyond atol, or a different missing pattern)."""
    keys = list(keys)
    a = new.sort_values(keys).reset_index(drop=True)
    b = old.sort_values(keys).reset_index(drop=True)
    assert len(a) == len(b), f"row counts differ: {len(a)} vs {len(b)}"
    for k in keys:
        assert (pd.Series(a[k]).astype(str).values == pd.Series(b[k]).astype(str).values).all(), f"key {k} differs"
    rows = []
    for c in b.columns:
        if c in keys or c in skip:
            continue
        if c not in a.columns:
            rows.append({"column": c, "differing_cells": len(b), "max_abs_diff": np.nan, "note": "missing in new"})
            continue
        x, y = a[c], b[c]
        if pd.api.types.is_numeric_dtype(y) and pd.api.types.is_numeric_dtype(x):
            xf, yf = x.astype(float).to_numpy(), y.astype(float).to_numpy()
            both = ~np.isnan(xf) & ~np.isnan(yf)
            diff = np.zeros(len(xf), dtype=bool)
            diff[both] = np.abs(xf[both] - yf[both]) > atol * np.maximum(1, np.abs(yf[both]))
            diff |= np.isnan(xf) != np.isnan(yf)
            mad = float(np.nanmax(np.abs(xf[both] - yf[both]))) if both.any() else 0.0
        else:
            diff = (x.astype(str).to_numpy() != y.astype(str).to_numpy())
            mad = np.nan
        rows.append({"column": c, "differing_cells": int(diff.sum()), "max_abs_diff": mad, "note": ""})
    extra = [c for c in a.columns if c not in b.columns]
    for c in extra:
        rows.append({"column": c, "differing_cells": 0, "max_abs_diff": np.nan, "note": "new column"})
    return pd.DataFrame(rows)


def write_clean(out_dir, aq, wx, wind, fire_wide, fire_long, frozen):
    """Write the daily tables in the Dataset/clean layout, plus copies of the frozen JSON files,
    so src/merge.build_master(clean_dir=out_dir) runs unchanged."""
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    aq.to_parquet(out_dir / "aq_daily.parquet", index=False)
    wx.to_parquet(out_dir / "wx_daily.parquet", index=False)
    wind.to_parquet(out_dir / "wind_daily.parquet", index=False)
    fire_wide.to_parquet(out_dir / "fire_daily.parquet", index=False)
    fire_long.to_parquet(out_dir / "fire_daily_long.parquet", index=False)
    for name in ["aq_params.json", "weather_zscore_params.json", "fire_zscore_params.json", "role2_params.json"]:
        shutil.copy(CLEAN_DIR / name, out_dir / name)
    return sorted(p.name for p in out_dir.iterdir())
