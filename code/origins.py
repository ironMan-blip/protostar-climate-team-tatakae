"""Replay forecast.py from every origin 1985-2011 (7-year horizon, data up to the origin only)
and print the mean challenge skill S per metric and the challenge-style score.

Usage:  python code/origins.py [--data DIR]
"""

import argparse

import numpy as np

import forecast as F


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default=None)
    args = ap.parse_args()
    pan, nearest = F.panels(F.load(args.data))
    shapes = F.daily_shapes(F.load(args.data, "daily"))

    S = {m: [] for m in pan}
    for T in range(1985, 2012):
        years = list(range(T + 1, T + 8))
        pred = F.forecast(pan, nearest, T, years, shapes)
        for m, p in pan.items():
            actual = p.reindex(columns=years).values
            base = F.baselines(p, T, years)["30yr_avg"]
            ok = np.isfinite(actual) & np.isfinite(base) & np.isfinite(pred[m])
            S[m].append(1 - np.abs(actual - pred[m])[ok].mean() / np.abs(actual - base)[ok].mean())

    for label, sl in (("all origins 1985-2011", slice(None)), ("origins 2004-2011", slice(-8, None))):
        s = {m: float(np.mean(v[sl])) for m, v in S.items()}
        print(f"{label}: " + ", ".join(f"S_{m} {x:.4f}" for m, x in s.items())
              + f" -> score {100 * max(0, np.mean(list(s.values()))):.2f}")


if __name__ == "__main__":
    main()
