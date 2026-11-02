---
pretty_name: "Protostar Climate Challenge Submission: Team Tatakae"
license: cc-by-4.0
task_categories:
- time-series-forecasting
tags:
- climate
- forecasting
- protostar-climate-2026
configs:
- config_name: default
  data_files:
  - split: test
    path: submission.csv
---

# Team Tatakae: Protostar Climate Challenge Submission

**Negative result:** no

Forecasts of yearly weather for 210 U.S. cities, 2019–2025, made as of the end of 2018 (no data that reveals 2019–2025 weather), for the [Protostar Challenge: Climate Risk Intelligence](https://huggingface.co/spaces/CMU-OSPO/protostar-challenge-climate-risk-intelligence).

## Team

| Name | Hugging Face username | Program |
|---|---|---|
| Mashrafi Mahmud Rafi | [@ironMan334](https://huggingface.co/ironMan334) | CSE |

## Method

**"Recent normal + regional warming"**: a transparent statistical forecast. We chose it because it beat every heavier model we tried in the backtests below.

- **Model:**
  - **Average temperature:** the city's 2009–2018 mean, plus the *regional* warming rate times the years since 2013.5, the middle of that window. The regional warming rate is the average 1979–2018 temperature trend of the city's 32 nearest cities (median +0.52 °F/decade; range +0.33 to +0.63).
  - **Cooling degree days:** the city's 2009–2018 mean CDD, plus the city's *CDD sensitivity* (extra CDD per +1 °F of annual temperature, fitted on 1989–2018) times the same regional warming. Physically, CDD is driven by temperature, and the pooled temperature trend is far less noisy than any single city's CDD trend.
  - **Precipitation and hottest day:** the city's 1989–2018 mean.
- **Features:** only `annual_indices` up to 2018, plus station latitude/longitude to find neighbours. A year counts only if ≤ 10 days are missing, the same rule the challenge uses for scoring. We did not use any external data.
- **How we checked it:** we replayed the exact method at five past origins, each using only the years before them. Score = the challenge formula (vs the 30-year average):

| Test years (origin) | Temp S | Precip S | Hot day S | CDD S | **Score: ours** | Score: linear trend |
|---|---:|---:|---:|---:|---:|---:|
| 1991–1997 (1990) | 0.048 | 0 | 0 | 0.031 | **2.0** | 0.0 |
| 1998–2004 (1997) | 0.188 | 0 | 0 | 0.024 | **5.3** | 0.0 |
| 2005–2011 (2004) | 0.157 | 0 | 0 | 0.101 | **6.5** | 0.0 |
| 2011–2018 (2010, organisers' practice run) | 0.170 | 0 | 0 | 0.218 | **9.7** | 4.8 |
| 2012–2018 (2011) | 0.152 | 0 | 0 | 0.221 | **9.3** | 2.2 |

Per-metric MAEs for all four forecasters (ours, 30-year average, last year repeated, linear trend) are in `code/backtest.csv`. The skill grows in later windows as warming accelerates, and our model beats the linear-trend baseline in every window.

  In the organisers' practice run (data to 2010, forecast 2011–2018) we reproduce their reference numbers exactly: the 30-year average scores a CDD MAE of **212.6 °F-days** and the trend line **176.9**. Our model scores **166.2**, beating the trend line by more than the 10 °F-day tie margin (level 2). Temperature MAE: 1.38 °F, against 1.66 for the 30-year average and 1.43 for the trend line.

**What we learned (and why the model is this simple).** We backtested more than 100 variants: recent 5/10/15/20-year means, 30/40/50-year trends, medians (MAE favours medians), city-only vs 4/8/16/32/210-neighbour pooling, and a pooled Huber regression on all of these features.
1. **Pooling wins.** A single city's trend is mostly station noise. The more cities we averaged over, the better the extrapolation, up to about 32.
2. **The recent decade beats the 30-year normal for temperature and CDD**, because the climate has already moved away from the 1989–2018 average.
3. **Precipitation and hottest day are noise-dominated.** No variant beat the 30-year average in a consistent way across windows. Some won one window and lost the next, so we deliberately kept the baseline there instead of overfitting.

**Why it is useful in the real world.** The method needs only a station's own yearly record plus its neighbours. It runs in seconds, has no tuned black box, and gives planners a defensible "near-term normal" that any GHCN station can reproduce. In our backtests it is a better planning number than the 30-year normals that utilities and building codes still use.

## Policy Idea

1. **What risk did we notice?** Air-conditioning demand is rising fastest, in percentage terms, in cities that were not built for it. Across the 210 cities, CDD in 2009–2018 was already a median **16.6 % higher** than in 1959–1988. Our forecast puts 2025 a further **+12.8 %** above the 1989–2018 normal, with CDD rising in 98 % of cities. The biggest *relative* jumps are in the cool Northwest and the North: Seattle (+45 %), Salem (+37 %), Vancouver WA (+35 %), Reno (+31 %), Sault Ste. Marie (+39 %). Many homes there have no cooling, so heat becomes a health emergency (as in the 2021 Pacific Northwest heat dome). Meanwhile, 13 cities have crossed 1,000 CDD a year since 1959–1988, including Columbus OH, Dayton, Boise, Asheville and Reno.
2. **What would we do about it, and who would do it?** A **"Cooling-Ready Cities" heat-pump retrofit program**, run by state energy offices with electric utilities. Each year, a forecast like ours flags cities whose near-term CDD is projected to rise above **+25 %** of the official 30-year normal, or to cross 1,000 CDD. In flagged cities, rebates would replace furnaces and window AC units in low-income and elderly households with **cold-climate heat pumps**, paired with cool roofs and street-tree planting on the hottest blocks. Utilities would also use the forecast CDD instead of backward-looking 30-year normals in their summer peak-load planning.
3. **Why is it sustainable?** A heat pump is both the efficient air conditioner and the efficient heater: it cuts winter fossil-fuel heating emissions while adding cooling, so adaptation lowers emissions instead of raising them. Cool roofs and trees reduce cooling demand with no running cost. Targeting with a cheap, transparent forecast spends money where risk is actually rising, before the emergency.

## Feedback to the Ecosystem

- **What got in the way:**
  - **The challenge text is invisible to non-browser tools.** The Space renders its rules in JavaScript, so a plain HTTP fetch (or an AI agent) sees only "Fetching metadata…". We had to read `content/about.md` and `content/data.md` out of the Space's git repo to find the rules.
  - **The scoring "validity" rule is not machine-actionable.** "Years where the station missed more than 10 days" does not say which `Miss *` column applies to each metric (e.g., Tmax and Tmin for average temperature and CDD, or only Tmax for hottest day?). We had to infer it. We confirmed our reading only because our 30-year-average and trend MAEs reproduced the organisers' quoted 213 and 177 °F-days.
  - **The 30-year-average baseline is underspecified:** are invalid years included in the 1989–2018 mean? Four cities (Huntsville, Grand Island, Elko, Hayward) have whole 30-year windows with no valid years at earlier origins.
  - **No station-change flags in `annual_indices`.** Each record is "threaded" from several stations (in `city_info`), but there is no per-year flag for a station move. Such moves create step changes that look like climate trends.
  - **Precision changes in 2018** (one decimal from converted GHCN-D, whole °F before) are documented in the card, but not flagged per row.
- **What would fix it:**
  - Publish the rules as a plain Markdown file in the dataset or template repo, linked from the Space.
  - Ship the scorer (`score.py`) alongside `check_submission.py`, with explicit per-metric validity columns, e.g. a boolean `valid_<metric>` in `annual_indices`.
  - Add a `station_id_in_use` column per year so users can detect or adjust for breakpoints.
  - Release the organisers' practice-run baseline numbers per metric (not just CDD), so teams can verify their pipeline end to end.

## Files

| File | Content |
|---|---|
| `submission.csv` | Our forecasts: `city_id,year,metric,predicted_value` |
| `code/forecast.py` | The whole method: loads the data, runs the five backtests, writes `submission.csv` and `code/backtest.csv` |
| `code/backtest.csv` | MAE of our model and the three reference baselines, per metric and test window |
| `code/requirements.txt` | Python packages |
| `code/check_submission.py` | The template's format checker |

**Metric codes:** `annual_avg_temp` (°F), `total_precip_in` (inches), `hottest_day_temp` (°F), `cdd` (°F-days).
**City IDs:** the station `ID` from the `city_info` table of the training dataset (e.g., Pittsburgh = `USW00094823`).

## How to Reproduce

1. `pip install -r code/requirements.txt` (Python ≥ 3.10).
2. `python code/forecast.py`. It downloads `annual_indices` from the Hub, prints the backtests, and rewrites `submission.csv` and `code/backtest.csv` (about 10 seconds; the output is deterministic). Pass `--data DIR` to use a local copy of `annual_indices.parquet`.
3. `python code/check_submission.py` → `OK: submission.csv has all 5880 forecasts and can be scored.`

## Data

- **External data:** none. Forecasts use only the challenge dataset up to 2018-12-31. The policy section uses only figures computed from the same data.

Training data: [`CMU-OSPO/protostar-climate-train-to-2018`](https://huggingface.co/datasets/CMU-OSPO/protostar-climate-train-to-2018), from:

- Lai, Y., & Dzombak, D. A. (2019). Compiled historical daily temperature and precipitation data for selected 210 U.S. cities. Carnegie Mellon University. https://doi.org/10.1184/R1/7890488.v6
- Lai, Y., & Dzombak, D. A. (2019). Historical changes of annual temperature and precipitation indices at selected 210 U.S. cities. Carnegie Mellon University. https://doi.org/10.1184/R1/7961012.v6
- Lai, Y., & Dzombak, D. A. (2019). *Use of historical data to assess regional climate change.* Journal of Climate, 32(14), 4299–4320. https://doi.org/10.1175/JCLI-D-18-0630.1
