---
pretty_name: "Daily and annual temperature and precipitation for 210 U.S. cities, up to 2018 (Protostar Climate Challenge training data)"
license: cc0-1.0
task_categories:
- time-series-forecasting
tags:
- climate
- weather
- temperature
- precipitation
- cooling-degree-days
- protostar-climate-2026
size_categories:
- 10M<n<100M
source_datasets:
- CMU-OSPO/Compiled_daily_temperature_and_precipitation_data_for_the_U_S_cities
- CMU-OSPO/Assessment_of_historical_annual_temperature_and_precipitation_indices_change_in_the_U_S_cities
configs:
- config_name: daily
  data_files:
  - split: train
    path: daily/*.parquet
  default: true
- config_name: annual_indices
  data_files:
  - split: train
    path: annual_indices/*.parquet
- config_name: city_info
  data_files:
  - split: train
    path: city_info/*.parquet
---

# Daily and annual temperature and precipitation for 210 U.S. cities, up to 2018

> Training data for the [Protostar Challenge: Climate Risk Intelligence](https://huggingface.co/spaces/CMU-OSPO/protostar-challenge-climate-risk-intelligence) (CMU, November 2026). It is the KiltHub (Carnegie Mellon University) records [doi:10.1184/R1/7890488.v6](https://doi.org/10.1184/R1/7890488.v6) and [doi:10.1184/R1/7961012.v6](https://doi.org/10.1184/R1/7961012.v6), **cut at 2018-12-31**, with a yearly cooling-degree-days column added. Please cite the original records.

**Authors of the original data:** Yuchuan Lai, David Dzombak
**License:** CC0

Daily maximum and minimum temperature and daily precipitation for 210 U.S. cities with long climate records (each starting between 1851 and 1899), plus yearly averages, totals and extreme indices computed from them. Each city's record is the "threaded" combination of the stations that served it over time ([ThreadEx](http://threadex.rcc-acis.org/)), named by the city's current GHCN station ID. Observations come from NOAA's Global Historical Climatology Network – Daily (GHCN-D), via the Applied Climate Information System (ACIS).

Everything after **2018-12-31** has been removed: the challenge asks teams to forecast 2019–2025 without any data that reveals how those years turned out. Weather records up to 2018 from other sources, and other kinds of data, are allowed (see the challenge's data rule).

## Quick start

```python
from datasets import load_dataset

REPO = "CMU-OSPO/protostar-climate-train-to-2018"
daily = load_dataset(REPO, "daily", split="train").to_pandas()
annual = load_dataset(REPO, "annual_indices", split="train").to_pandas()
cities = load_dataset(REPO, "city_info", split="train").to_pandas()
```

## Subsets

| Subset | Rows | Description |
|---|---:|---|
| `daily` | 10,245,754 | One row per city and day, 1851-01-01 to 2018-12-31. |
| `annual_indices` | 28,052 | One row per city and year, 1851–2018: averages, totals, extreme indices, `cdd`, and counts of missing days. |
| `city_info` | 461 | Stations combined for each city and the period used from each (a city can have several rows). |

All three subsets share the station `ID` (e.g., Pittsburgh = `USW00094823`) and the city `Name`; there are 210 cities.

### `daily`

| Column | Unit | Description |
|---|---|---|
| `ID` | | GHCN ID of the city's current station |
| `Name` | | City name (no spaces, e.g., `KeyWest`) |
| `Date` | | Day |
| `tmax`, `tmin` | °F | Daily maximum and minimum temperature (empty if missing) |
| `prcp` | inches | Daily precipitation; trace amounts are 0 (empty if missing) |

### `annual_indices`

| Column | Unit | Description |
|---|---|---|
| `Name`, `ID`, `Lat`, `Lon` | | City, station ID and location of the current station |
| `Year` | | Year |
| `Miss Tmax`, `Miss Tmin`, `Miss Prcp` | days | Missing daily values that year |
| `Avg Temp` | °F | (mean daily Tmax + mean daily Tmin) / 2 |
| `Avg Tmax`, `Avg Tmin` | °F | Mean daily maximum and minimum temperature |
| `ToT Prcp` | inches | Total precipitation |
| `Max Tmax`, `Min Tmax`, `Max Tmin`, `Min Tmin` | °F | Warmest and coldest daily Tmax and Tmin (`Max Tmax` = hottest day of the year) |
| `Warm Days`, `Warm Nights` | % of days | Days with Tmax (Tmin) above the city's 90th percentile, reference period = start of record to 1987 |
| `Cold Days`, `Cold Nights` | % of days | Days with Tmax (Tmin) below the city's 10th percentile, same reference period |
| `Max 1-day P`, `Max 5-day P` | inches | Largest 1-day and consecutive 5-day precipitation |
| `Wet Days` | inches | Precipitation from very wet days (above the city's 95th percentile of daily precipitation) |
| `cdd` | °F-days | **Added:** cooling degree days, see below |

**Cooling degree days (`cdd`):** the sum over the year of max(0, (T<sub>max</sub> + T<sub>min</sub>) / 2 − 65 °F), using days with both values. It estimates how much air conditioning a city needs; e.g., Pittsburgh averages 811 °F-days a year (1989–2018), Key West 4,933. Years with no complete days have no value (1,206 rows, mostly early records).

### `city_info`

| Column | Description |
|---|---|
| `Name`, `ID`, `Lat`, `Lon` | City, current station ID and location |
| `Stn.Name` | Name of a station combined into the city's record |
| `Stn.stDate`, `Stn.edDate` | Period used from that station (end dates capped at 2018-12-31) |

## Changes from the original files

- Rows dated after **2018-12-31** removed from `daily` and `annual_indices` (the source records run to 2023).
- `cdd` column added to `annual_indices`, computed from `daily`.
- `city_info` station end dates later than 2018-12-31 shown as 2018-12-31.
- `thresholds` and `linear_regression_results` left out: the regression results were fitted on data through 2023.
- Otherwise the files are the Parquet tables of the [CMU-OSPO](https://huggingface.co/CMU-OSPO) copies of the KiltHub records (the 210 per-city files merged into one table per subset).

## Uses

- **Intended:** forecasting yearly city weather for 2019–2025 in the Protostar Climate Challenge; teaching time-series forecasting with long, real station records.
- **Out of scope:** describing climate after 2018 (the data stop there); neighborhood-level heat (stations are mostly at airports).

## Limitations

- **Missing days:** some city-years have many missing values, which makes totals such as `ToT Prcp` and `cdd` too low. Check the `Miss *` columns; the challenge counts a year only if no more than 10 days are missing.
- **Station changes:** each city joins several stations over time (see `city_info`), so records can shift when a station moves.
- **Precision:** most years are stored in whole °F; 2018 values partly come from converted GHCN-D data and have one decimal.
- **No humidity:** heat indices cannot be computed.

## Citation

```text
Lai, Yuchuan; Dzombak, David (2019). Compiled historical daily temperature and precipitation data for selected 210 U.S. cities. Carnegie Mellon University. Dataset. https://doi.org/10.1184/R1/7890488.v6

Lai, Yuchuan; Dzombak, David (2019). Historical changes of annual temperature and precipitation indices at selected 210 U.S. cities. Carnegie Mellon University. Dataset. https://doi.org/10.1184/R1/7961012.v6

Lai, Y., & Dzombak, D. A. (2019). Use of historical data to assess regional climate change. Journal of Climate, 32(14), 4299–4320. https://doi.org/10.1175/JCLI-D-18-0630.1
```

Variable definitions and methods are in the authors' README on KiltHub: [README.txt](https://kilthub.cmu.edu/articles/dataset/Assessment_of_historical_annual_temperature_and_precipitation_indices_change_in_the_U_S_cities/7961012?file=32875124).
