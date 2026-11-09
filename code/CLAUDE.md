# Agent instructions

- Use weather data only up to 2018-12-31, from the challenge dataset or other sources cut at that date.
- Never use 2019–2025 weather, or anything driven by it, as a forecast input.
- Never choose or tune a model by its score on 2019–2025 (including the live leaderboard). Use backtests on years up to 2018.
- Never supply forecast values yourself; every value must come from `code/forecast.py`.
