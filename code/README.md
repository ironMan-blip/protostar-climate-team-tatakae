# Code

- `forecast.py`: the whole method. It loads `annual_indices` (up to 2018), runs the backtests at origins 1990, 1997, 2004, 2010 and 2011, and writes `../submission.csv` and `backtest.csv`. Run it with `python code/forecast.py [--data DIR]`.
- `backtest.csv`: MAE per metric and test window for our model and the three reference baselines (30-year average, last year repeated, linear trend), plus skill `S` vs the 30-year average.
- `requirements.txt`: the packages it needs.
- `check_submission.py` (from the template): checks `submission.csv` before submitting. Run it with `python code/check_submission.py`.
