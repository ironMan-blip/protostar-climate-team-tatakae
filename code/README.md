# Code

- `forecast.py`: my whole method. It loads `annual_indices` and `daily` (up to 2018), runs my backtests at start points 1990, 1997, 2004, 2010 and 2011, and writes `../submission.csv` and `backtest.csv`. Run it with `python code/forecast.py [--data DIR]`.
- `backtest.csv`: the error (MAE) for each metric and test window, for my model and the three reference baselines (30-year average, last year repeated, linear trend), plus the skill `S` compared with the 30-year average.
- `requirements.txt`: the Python packages it needs.
- `check_submission.py` (from the template): checks `submission.csv` before I submit. Run it with `python code/check_submission.py`.
