"""Price forecasting: gradient boosting on lag + seasonal features, recursive 14-day forecast."""
from functools import lru_cache
import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingRegressor
from .data import load_prices, series, CROPS

LAGS = (1, 2, 3, 7, 14, 28)
HORIZON = 14


def _features(hist, date):
    hist = np.asarray(hist)
    f = [hist[-l] for l in LAGS]
    f += [hist[-7:].mean(), hist[-28:].mean(), hist[-7:].std()]
    doy = date.dayofyear
    f += [np.sin(2 * np.pi * doy / 365), np.cos(2 * np.pi * doy / 365)]
    return f


def _dataset(s):
    vals, idx = s.values, s.index
    X, y = [], []
    for t in range(28, len(vals)):
        X.append(_features(vals[:t], idx[t]))
        y.append(vals[t] / vals[t - 1] - 1)  # next-day return
    return np.array(X), np.array(y)


@lru_cache(maxsize=None)
def get_model(crop: str):
    s = series(load_prices(), crop)
    X, y = _dataset(s)
    split = len(X) - 60
    m = GradientBoostingRegressor(n_estimators=150, max_depth=3, learning_rate=0.05, random_state=0)
    m.fit(X[:split], y[:split])
    # honest hold-out check: 7-day-ahead error on the last 60 days
    errs, vals = [], s.values
    for t in range(len(vals) - 60, len(vals) - 7, 3):
        h = list(vals[:t])
        for k in range(7):
            r = m.predict([_features(h, s.index[t] + pd.Timedelta(days=k))])[0]
            h.append(h[-1] * (1 + r))
        errs.append(abs(h[-1] - vals[t + 6]) / vals[t + 6])
    m.fit(X, y)
    return m, float(np.mean(errs) * 100)


def forecast(crop: str, days: int = HORIZON) -> dict:
    s = series(load_prices(), crop)
    m, mape = get_model(crop)
    h, d0, out = list(s.values), s.index[-1], []
    for k in range(1, days + 1):
        date = d0 + pd.Timedelta(days=k)
        r = float(np.clip(m.predict([_features(h, date)])[0], -0.04, 0.04))
        h.append(h[-1] * (1 + r))
        out.append({"date": date.strftime("%Y-%m-%d"), "price": round(h[-1])})
    return {"crop": crop, "today": round(float(s.iloc[-1])), "as_of": d0.strftime("%Y-%m-%d"),
            "forecast": out, "holdout_7day_error_pct": round(mape, 1)}


def advise(crop: str, rain_expected: bool = False) -> dict:
    f = forecast(crop)
    shelf = CROPS[crop]["shelf"]
    window = f["forecast"][: min(shelf, HORIZON)]
    best = max(window, key=lambda p: p["price"])
    gain = (best["price"] / f["today"] - 1) * 100
    if rain_expected and shelf <= 7:
        action, why = "sell_now", "rain expected and this crop spoils quickly"
    elif gain >= 3:
        action, why = "wait", f"price expected to rise {gain:.1f}% by {best['date']}"
    else:
        action, why = "sell_now", "no meaningful rise expected in your storage window"
    return {**f, "action": action, "reason": why, "best_date": best["date"],
            "best_price": best["price"], "expected_gain_pct": round(gain, 1), "shelf_life_days": shelf}
