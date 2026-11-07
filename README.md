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

**Hugging Face dataset (official submission):** [ironMan334/protostar-climate-team-tatakae](https://huggingface.co/datasets/ironMan334/protostar-climate-team-tatakae)

I forecast the yearly weather of 210 U.S. cities for 2019–2025. I only used data up to the end of 2018, so nothing in my inputs shows how 2019–2025 turned out. This is my entry for the [Protostar Challenge: Climate Risk Intelligence](https://huggingface.co/spaces/CMU-OSPO/protostar-challenge-climate-risk-intelligence).

## Team

I worked on this alone.

| Name | Hugging Face username | Program |
|---|---|---|
| Mashrafi Mahmud Rafi | [@ironMan334](https://huggingface.co/ironMan334) | CSE |

## Architecture

```mermaid
flowchart TD
    A["HF dataset: CMU-OSPO/protostar-climate-train-to-2018<br/>annual_indices, 210 cities, up to 2018"] --> B["code/forecast.py: load + clean<br/>keep years with ≤ 10 missing days"]
    B --> C["Neighbours: 32 nearest cities by lat/lon"]
    C --> D["Regional warming rate<br/>mean 1979–2018 temp trend of neighbours"]
    B --> E["Recent normal<br/>city 2009–2018 mean"]
    B --> F["30-year normal<br/>city 1989–2018 mean"]
    B --> G["CDD sensitivity<br/>extra CDD per +1 °F, fit 1989–2018"]
    D --> T["annual_avg_temp = recent mean + rate × (year − 2013.5)"]
    E --> T
    D --> K["cdd = recent CDD + sensitivity × regional warming"]
    E --> K
    G --> K
    F --> P["total_precip_in, hottest_day_temp = 30-year mean"]
    T --> S["submission.csv<br/>210 cities × 2019–2025 × 4 metrics = 5,880 rows"]
    K --> S
    P --> S
    B --> DS["Daily-shape CDD<br/>last 10 years of daily temps, shifted to the temp forecast"]
    T --> DS
    DS --> K
    B --> BT["Backtests at origins 1990, 1997, 2004, 2010, 2011<br/>vs 30-yr avg, last year, linear trend"]
    BT --> BC["code/backtest.csv"]
    S --> CH["code/check_submission.py: format check"]
    CH --> HF["HF dataset repo → Space Submission tab → scored"]
```

## Method

I call it **"recent normal + regional warming"**. It is a simple statistical forecast that anyone can follow. I picked it because it beat every bigger model I tried in my tests (below).

- **The model:**
  - **Average temperature:** I take the city's 2009–2018 average. Then I add the *regional* warming rate times the number of years since 2013.5 (the middle of that 10-year window). The regional warming rate is the average 1979–2018 temperature trend of the city's 32 closest cities. The middle value is +0.52 °F per decade (range +0.33 to +0.63).
  - **Cooling degree days (CDD):** I take the city's 2009–2018 average CDD. Then I add the city's *CDD sensitivity* times the same regional warming. CDD sensitivity means "how many extra CDD the city gets for each +1 °F of yearly temperature", fitted on 1989–2018. This makes sense because CDD comes from temperature, and the shared regional temperature trend is much less noisy than one city's own CDD trend.
  - **Second view, "region + departure" (75 % weight for temperature and CDD):** each year, a city's value = its region's anomaly (mean of its 32 nearest cities, each measured against its own 1989–2018 mean) + the city's *departure* from that region. The departure is much less noisy than the raw value, because weather shared across the region cancels out, so its last 5 years are enough to pin it down (this also follows station moves quickly). The region's anomaly is carried forward with a 1989–2018 trend line; CDD uses the same regional anomaly times the city's CDD sensitivity. The final forecast is 75 % this view + 25 % the first one. I chose this by replaying it from every start year 1985–2011 (data before that year only): on average it adds about +0.02 to temperature skill and +0.01 to CDD skill. It is not better in every window (see the table: 1997 got worse, 2004 better).
  - **Third view for CDD, "daily shape" (50 % weight):** CDD is not a straight line in temperature: only days above 65 °F count, so a warmer year adds more CDD in a hot city than in a cool one. For each of the city's last 10 valid years, I take that year's real daily temperatures, shift them so the year's average equals my temperature forecast, and recount CDD. The mean of those 10 counts is the third view; the final CDD is 50 % this + 50 % the first two. Replayed from every start year 1985–2011, it raised CDD skill from 0.0766 to 0.0811 and won in 70 % of start years.
  - **Rain and the hottest day:** the city's 1989–2018 average.
- **Inputs:** only `annual_indices` and `daily` up to 2018, plus each station's latitude and longitude to find its neighbours. I only count a year if 10 or fewer days are missing. This is the same rule the challenge uses for scoring. I used no outside data.
- **How I tested it:** I ran the exact same method at five points in the past. Each time it could only see the years before that point. The score uses the challenge formula (compared with the 30-year average):

| Test years (start point) | Temp S | Precip S | Hot day S | CDD S | **Score: mine** | Score: linear trend |
|---|---:|---:|---:|---:|---:|---:|
| 1991–1997 (1990) | 0.046 | 0 | 0 | 0.037 | **2.1** | 0.0 |
| 1998–2004 (1997) | 0.144 | 0 | 0 | 0.021 | **4.1** | 0.0 |
| 2005–2011 (2004) | 0.190 | 0 | 0 | 0.147 | **8.4** | 0.0 |
| 2011–2018 (2010, organisers' practice run) | 0.162 | 0 | 0 | 0.227 | **9.7** | 4.8 |
| 2012–2018 (2011) | 0.151 | 0 | 0 | 0.226 | **9.4** | 2.2 |

The errors (MAE) for each metric and all four forecasts (mine, 30-year average, last year repeated, linear trend) are in `code/backtest.csv`. My model does better in later test windows, because warming speeds up over time. It beats the linear-trend baseline in every window.

  In the organisers' practice run (data up to 2010, forecast 2011–2018), I get the exact same reference numbers they give: the 30-year average has a CDD error of **212.6 °F-days** and the trend line **176.9**. My model gets **164.4**. That beats the trend line by more than the 10 °F-day tie margin (level 2). For temperature, my error is 1.39 °F, against 1.66 for the 30-year average and 1.43 for the trend line.

**What I learned (and why the model is so simple).** I tested more than 100 versions: recent 5/10/15/20-year averages, 30/40/50-year trends, medians (MAE rewards medians), one city alone vs. 4/8/16/32/210 neighbours, and a pooled Huber regression with all of these.
1. **Averaging over neighbours wins.** One city's trend is mostly noise from its station. The more cities I averaged, the better the forecast, up to about 32.
2. **The last 10 years beat the 30-year average for temperature and CDD**, because the climate has already moved away from the 1989–2018 average.
3. **Rain and the hottest day are mostly noise.** No version beat the 30-year average in every window. Some won one window and lost the next. So I kept the simple baseline there on purpose, instead of overfitting.

**Why it is useful in real life.** The method only needs a station's own yearly record and its neighbours. It runs in seconds and has no hidden black box. It gives planners a clear "near-term normal" that anyone can rebuild for any GHCN station. In my tests it is a better planning number than the 30-year normals that power companies and building codes still use.

## Policy Idea

1. **What risk did I notice?** The need for air conditioning is growing fastest (in percent) in cities that were not built for heat. Across the 210 cities, CDD in 2009–2018 was already a median **16.6 % higher** than in 1959–1988. My forecast puts 2025 another **+12.8 %** above the 1989–2018 normal, with CDD going up in 98 % of cities. The biggest *percent* jumps are in the cool Northwest and the North: Seattle (+45 %), Salem (+37 %), Vancouver WA (+35 %), Reno (+31 %), Sault Ste. Marie (+39 %). Many homes there have no cooling, so a heat wave can become a health emergency (like the 2021 Pacific Northwest heat dome). Also, 13 cities have gone above 1,000 CDD a year since 1959–1988, including Columbus OH, Dayton, Boise, Asheville and Reno.
2. **What would I do, and who would do it?** A **"Cooling-Ready Cities" heat-pump program**, run by state energy offices together with power companies. Every year, a forecast like mine marks the cities where near-term CDD is expected to rise more than **+25 %** above the official 30-year normal, or to pass 1,000 CDD. In those cities, rebates would help low-income and elderly households swap old furnaces and window AC units for **cold-climate heat pumps**. The program would also add cool roofs and plant street trees on the hottest blocks. Power companies would use the forecast CDD, instead of old 30-year normals, to plan for summer peak demand.
3. **Why does it last?** A heat pump is both an efficient air conditioner and an efficient heater. It cuts winter heating emissions from gas and oil while adding cooling, so getting ready for heat lowers emissions instead of raising them. Cool roofs and trees lower cooling needs and cost nothing to run. A cheap, open forecast puts the money where the risk is really rising, before the emergency happens.

## Feedback to the Ecosystem

- **What got in my way:**
  - **Tools that are not browsers cannot see the challenge text.** The Space shows its rules with JavaScript, so a plain HTTP fetch (or an AI agent) only sees "Fetching metadata…". I had to read `content/about.md` and `content/data.md` from the Space's git repo to find the rules.
  - **The "valid year" rule is not clear enough for code.** "Years where the station missed more than 10 days" does not say which `Miss *` column goes with which metric (for example: Tmax and Tmin for average temperature and CDD, or only Tmax for the hottest day?). I had to guess. I only knew my guess was right because my 30-year-average and trend errors matched the organisers' numbers (213 and 177 °F-days).
  - **The 30-year-average baseline is not fully defined:** are invalid years included in the 1989–2018 average? Four cities (Huntsville, Grand Island, Elko, Hayward) have whole 30-year windows with no valid years at earlier start points.
  - **No station-change flags in `annual_indices`.** Each city's record joins several stations (listed in `city_info`), but no column shows the year a station moved. These moves cause sudden jumps that look like climate trends.
  - **Number precision changes in 2018** (one decimal from converted GHCN-D data, whole °F before). The data card mentions it, but the rows do not flag it.
- **What would fix it:**
  - Publish the rules as a plain Markdown file in the dataset or template repo, with a link from the Space.
  - Share the scorer (`score.py`) next to `check_submission.py`, with clear validity columns for each metric, for example a true/false `valid_<metric>` column in `annual_indices`.
  - Add a `station_id_in_use` column for each year, so people can find or fix station jumps.
  - Share the organisers' practice-run baseline numbers for every metric (not just CDD), so teams can check their whole pipeline.

## Files

| File | What it has |
|---|---|
| `submission.csv` | My forecasts: `city_id,year,metric,predicted_value` |
| `code/forecast.py` | The whole method: loads the data, runs the five backtests, writes `submission.csv` and `code/backtest.csv` |
| `code/backtest.csv` | Errors (MAE) of my model and the three reference baselines, for each metric and test window |
| `code/requirements.txt` | Python packages |
| `code/check_submission.py` | The template's format checker |

**Metric codes:** `annual_avg_temp` (°F), `total_precip_in` (inches), `hottest_day_temp` (°F), `cdd` (°F-days).
**City IDs:** the station `ID` from the `city_info` table of the training dataset (for example, Pittsburgh = `USW00094823`).

## How to Run It Yourself

1. `pip install -r code/requirements.txt` (Python 3.10 or newer).
2. `python code/forecast.py`. It downloads `annual_indices` and `daily` from the Hub, prints the backtests, and rewrites `submission.csv` and `code/backtest.csv`. It takes under a minute and gives the same output every time. Add `--data DIR` to use local copies of `annual_indices.parquet` and `daily.parquet` (e.g. `--data data`).
3. `python code/check_submission.py` → `OK: submission.csv has all 5880 forecasts and can be scored.`

## Data

- **Outside data:** none. The forecasts use only the challenge dataset up to 2018-12-31. The policy section only uses numbers I computed from the same data.

Training data: [`CMU-OSPO/protostar-climate-train-to-2018`](https://huggingface.co/datasets/CMU-OSPO/protostar-climate-train-to-2018), from:

- Lai, Y., & Dzombak, D. A. (2019). Compiled historical daily temperature and precipitation data for selected 210 U.S. cities. Carnegie Mellon University. https://doi.org/10.1184/R1/7890488.v6
- Lai, Y., & Dzombak, D. A. (2019). Historical changes of annual temperature and precipitation indices at selected 210 U.S. cities. Carnegie Mellon University. https://doi.org/10.1184/R1/7961012.v6
- Lai, Y., & Dzombak, D. A. (2019). *Use of historical data to assess regional climate change.* Journal of Climate, 32(14), 4299–4320. https://doi.org/10.1175/JCLI-D-18-0630.1
