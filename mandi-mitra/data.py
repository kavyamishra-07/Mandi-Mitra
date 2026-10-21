"""Price data loader.

Uses data/prices.csv (columns: date,crop,modal_price in Rs/quintal) if present.
Otherwise generates a clearly-labelled SYNTHETIC sample dataset with realistic
seasonality so the project runs offline. Drop a real Agmarknet export in
data/prices.csv to use real prices.
"""
from pathlib import Path
import numpy as np
import pandas as pd

DATA_PATH = Path(__file__).resolve().parent.parent / "data" / "prices.csv"

# base price (Rs/quintal), seasonal amplitude, noise, shelf life (days)
CROPS = {
    "wheat":  dict(base=2400, amp=0.06, peak_doy=120, noise=0.004, shelf=180),
    "rice":   dict(base=2300, amp=0.05, peak_doy=60,  noise=0.004, shelf=180),
    "tomato": dict(base=1800, amp=0.45, peak_doy=190, noise=0.03,  shelf=4),
    "potato": dict(base=1500, amp=0.25, peak_doy=335, noise=0.012, shelf=60),
    "onion":  dict(base=2000, amp=0.35, peak_doy=350, noise=0.015, shelf=45),
}


def _synthetic() -> pd.DataFrame:
    rng = np.random.default_rng(42)
    days = pd.date_range("2023-10-01", "2026-10-20", freq="D")
    rows = []
    for crop, c in CROPS.items():
        doy = days.dayofyear.values
        season = c["amp"] * np.cos(2 * np.pi * (doy - c["peak_doy"]) / 365)
        drift = 0.05 * (np.arange(len(days)) / 365)
        walk = np.cumsum(rng.normal(0, c["noise"], len(days)))
        walk -= np.convolve(walk, np.ones(60) / 60, mode="same")
        price = c["base"] * (1 + season + drift + walk)
        rows.append(pd.DataFrame({"date": days, "crop": crop, "modal_price": price.round(0)}))
    return pd.concat(rows, ignore_index=True)


def load_prices() -> pd.DataFrame:
    if DATA_PATH.exists():
        df = pd.read_csv(DATA_PATH, parse_dates=["date"])
    else:
        df = _synthetic()
        DATA_PATH.parent.mkdir(exist_ok=True)
        df.to_csv(DATA_PATH, index=False)
    return df.sort_values(["crop", "date"]).reset_index(drop=True)


def series(df: pd.DataFrame, crop: str) -> pd.Series:
    return df[df.crop == crop].set_index("date")["modal_price"].asfreq("D").interpolate()
