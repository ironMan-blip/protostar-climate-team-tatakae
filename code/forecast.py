"""Forecast yearly weather for 210 U.S. cities, 2019-2025, using only data up to 2018-12-31.

Method ("recent normal + regional warming"):
  annual_avg_temp   = city's last-10-year mean + regional warming rate x years since the
                      middle of that 10-year window. Regional warming rate = average 40-year
                      temperature trend of the city's 32 nearest cities (pooling cancels
                      station noise; single-city trends are too noisy to extrapolate).
  cdd               = city's last-10-year mean CDD + (city's CDD-per-degree sensitivity,
                      fitted over the last 30 years) x the same regional warming.
  total_precip_in,  = city's 30-year mean (1989-2018). Every recent-mean, trend, median and
  hottest_day_temp    pooled-regression variant we backtested failed to beat it reliably.
Only valid years (<= 10 missing days, the challenge's scoring rule) enter any statistic.
Choices were made by replaying the method at past origins (1990, 1997, 2004, 2010, 2011),
each time using only the years before the origin.

Usage:  python code/forecast.py [--data DIR]
        DIR holds annual_indices.parquet (downloaded from the Hub if omitted).
        Writes submission.csv and code/backtest.csv.
"""

import argparse
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

REPO = "CMU-OSPO/protostar-climate-train-to-2018"
METRICS = {  # challenge code -> annual_indices column, missing-day columns that invalidate a year
    "annual_avg_temp": ("Avg Temp", ["Miss Tmax", "Miss Tmin"]),
    "total_precip_in": ("ToT Prcp", ["Miss Prcp"]),
    "hottest_day_temp": ("Max Tmax", ["Miss Tmax"]),
    "cdd": ("cdd", ["Miss Tmax", "Miss Tmin"]),
}
LAST_YEAR = 2018
MAX_MISSING = 10      # the challenge scores a year only if <= 10 days are missing
RECENT = 10           # years in the "recent normal"
TREND_YEARS = 40      # window for each city's warming trend
NEIGHBOURS = 32       # cities pooled into the regional warming rate (incl. the city itself)
ROOT = Path(__file__).resolve().parent.parent

warnings.simplefilter("ignore", RuntimeWarning)  # nanmean over all-missing rows -> NaN, handled below


def load(data_dir):
    if data_dir is None:
        from huggingface_hub import hf_hub_download
        path = hf_hub_download(REPO, "annual_indices/train-00000-of-00001.parquet", repo_type="dataset")
    else:
        path = Path(data_dir) / "annual_indices.parquet"
    annual = pd.read_parquet(path)
    return annual[annual["Year"] <= LAST_YEAR]  # data rule: nothing after 2018-12-31


def panels(annual):
    """metric -> DataFrame (city x year) of valid values only; plus the neighbour index."""
    ids = np.sort(annual["ID"].unique())
    pan = {}
    for code, (col, miss) in METRICS.items():
        ok = (annual[miss] <= MAX_MISSING).all(axis=1)
        pan[code] = (annual.assign(v=annual[col].where(ok))
                     .pivot_table(index="ID", columns="Year", values="v", aggfunc="first", dropna=False)
                     .reindex(index=ids))
    loc = annual.groupby("ID")[["Lat", "Lon"]].first().reindex(ids)
    lat, lon = np.radians(loc["Lat"].values), np.radians(loc["Lon"].values)
    cos_dist = np.sin(lat[:, None]) * np.sin(lat) + np.cos(lat[:, None]) * np.cos(lat) * np.cos(lon[:, None] - lon)
    nearest = np.argsort(-cos_dist, axis=1)[:, :NEIGHBOURS]  # each city is its own nearest
    return pan, nearest


def window(p, T, n):
    """Values (cities x years) for years T-n+1..T, and the matching year numbers."""
    w = p.reindex(columns=range(T - n + 1, T + 1))
    return w.values, np.array(w.columns, dtype=float)


def mean_and_centre(p, T, n):
    v, yrs = window(p, T, n)
    x = np.where(np.isfinite(v), yrs, np.nan)
    return np.nanmean(v, 1), np.nanmean(x, 1)  # mean value, mean year of the valid values


def regression_slope(x, y):
    """Row-wise OLS slope of y on x, ignoring pairs where either is missing."""
    ok = np.isfinite(x) & np.isfinite(y)
    x, y = np.where(ok, x, np.nan), np.where(ok, y, np.nan)
    dx = x - np.nanmean(x, 1, keepdims=True)
    dy = y - np.nanmean(y, 1, keepdims=True)
    return np.nansum(dx * dy, 1) / np.nansum(dx * dx, 1)


def fill(a, fallback):
    return np.where(np.isfinite(a), a, fallback)


def forecast(pan, nearest, T, years):
    """metric -> array (cities x len(years)) of forecasts made with data up to year T only."""
    years = np.asarray(years, dtype=float)
    temp, cdd = pan["annual_avg_temp"], pan["cdd"]

    v, yrs = window(temp, T, TREND_YEARS)
    slope = regression_slope(np.broadcast_to(yrs, v.shape), v)
    regional_warming = np.nanmean(slope[nearest], 1)  # °F per year

    out = {}
    m30 = {code: mean_and_centre(p, T, 30)[0] for code, p in pan.items()}

    t10, t_centre = mean_and_centre(temp, T, RECENT)
    t10 = fill(t10, m30["annual_avg_temp"])
    t_centre = fill(t_centre, T - 14.5)
    out["annual_avg_temp"] = t10[:, None] + regional_warming[:, None] * (years - t_centre[:, None])

    # CDD per °F of annual temperature, fitted on the city's last 30 years; never negative
    tv, _ = window(temp, T, 30)
    cv, _ = window(cdd, T, 30)
    sens = np.clip(regression_slope(tv, cv), 0, None)
    sens = fill(sens, np.nanmedian(sens[nearest], 1))
    c10, c_centre = mean_and_centre(cdd, T, RECENT)
    c10 = fill(c10, m30["cdd"])
    c_centre = fill(c_centre, T - 14.5)
    out["cdd"] = np.clip(c10[:, None] + (sens * regional_warming)[:, None] * (years - c_centre[:, None]), 0, None)

    for code in ("total_precip_in", "hottest_day_temp"):
        out[code] = np.repeat(m30[code][:, None], len(years), axis=1)
    # NaN only where a city has no valid year in its 30-year window (a few cities at early
    # backtest origins, never at 2018); those rows have no baseline and are not scored
    return out


def baselines(p, T, years):
    """The challenge's three reference forecasts, each from data up to year T."""
    n = len(years)
    m30, _ = mean_and_centre(p, T, 30)
    last = p.reindex(columns=range(p.columns.min(), T + 1)).ffill(axis=1).iloc[:, -1].values
    v, yrs = window(p, T, 30)
    s = regression_slope(np.broadcast_to(yrs, v.shape), v)
    _, centre = mean_and_centre(p, T, 30)
    trend = m30[:, None] + s[:, None] * (np.asarray(years) - centre[:, None])
    return {"30yr_avg": np.repeat(m30[:, None], n, 1), "last_year": np.repeat(last[:, None], n, 1),
            "linear_trend": trend}


def backtest(pan, nearest, T, horizon=7):
    years = list(range(T + 1, T + 1 + horizon))
    pred = forecast(pan, nearest, T, years)
    rows = []
    for code, p in pan.items():
        actual = p.reindex(columns=years).values
        cands = {**baselines(p, T, years), "model": pred[code]}
        ok = np.isfinite(actual)
        for c in cands.values():
            ok &= np.isfinite(c)
        mae = {k: float(np.abs(actual - c)[ok].mean()) for k, c in cands.items()}
        rows.append({"test_years": f"{years[0]}-{years[-1]}", "metric": code, "rows_scored": int(ok.sum()),
                     **{f"MAE_{k}": round(m, 3) for k, m in mae.items()},
                     "S_model": round(1 - mae["model"] / mae["30yr_avg"], 3),
                     "S_linear_trend": round(1 - mae["linear_trend"] / mae["30yr_avg"], 3)})
    return pd.DataFrame(rows)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default=None, help="folder with annual_indices.parquet (default: download)")
    args = ap.parse_args()

    pan, nearest = panels(load(args.data))
    ids = pan["cdd"].index

    # practice runs: same code, earlier origins; the organisers' own run is 2010 -> 2011-2018
    bt = pd.concat([backtest(pan, nearest, 2010, horizon=8)] +
                   [backtest(pan, nearest, T) for T in (1990, 1997, 2004, 2011)], ignore_index=True)
    bt.to_csv(ROOT / "code" / "backtest.csv", index=False)
    pd.set_option("display.width", 220, "display.max_columns", 20)
    print(bt.to_string(index=False))
    for period, g in bt.groupby("test_years", sort=False):
        print(f"challenge-style score {period}: model {100 * max(0, g['S_model'].mean()):.1f}, "
              f"linear trend {100 * max(0, g['S_linear_trend'].mean()):.1f}")

    years = list(range(LAST_YEAR + 1, LAST_YEAR + 8))
    pred = forecast(pan, nearest, LAST_YEAR, years)
    long = pd.concat([pd.DataFrame(a, index=ids, columns=years).stack().rename("predicted_value")
                      .rename_axis(["city_id", "year"]).reset_index().assign(metric=code)
                      for code, a in pred.items()], ignore_index=True)

    template = pd.read_csv(ROOT / "submission.csv", dtype={"city_id": str})
    sub = template.drop(columns="predicted_value").merge(long, on=["city_id", "year", "metric"], how="left")
    assert len(sub) == 5880 and sub["predicted_value"].notna().all(), "every template row needs a forecast"
    sub["predicted_value"] = sub["predicted_value"].round(2)
    sub.to_csv(ROOT / "submission.csv", index=False)
    print(f"wrote {ROOT / 'submission.csv'} ({len(sub)} rows)")


if __name__ == "__main__":
    main()
