"""Simple exchange-rate helper for USD/KES with caching and rounding helpers."""

import time
from typing import Tuple

import requests

from config import Config

# In-memory cache so we don't hit the free API on every request
_CACHE = {
    "usd_kes_rate": None,
    "usd_kes_fetched_at": 0.0,
}

# Keyless public FX APIs (tried in order)
FX_SOURCES = (
    {
        "url": "https://open.er-api.com/v6/latest/USD",
        "extract": lambda data: (data.get("rates") or {}).get("KES"),
        "params": None,
        "name": "open.er-api.com",
    },
    {
        "url": "https://api.exchangerate.host/latest",
        "extract": lambda data: (data.get("rates") or {}).get("KES"),
        "params": {"base": "USD", "symbols": "KES"},
        "name": "api.exchangerate.host",
    },
)


def get_usd_to_kes_rate(ttl_seconds: int = 3600) -> float:
    """Return the current USD→KES rate.

    Tries multiple keyless APIs before falling back to Config.USD_TO_KES_RATE.
    """
    fallback_rate = getattr(Config, "USD_TO_KES_RATE", 130.0)
    now = time.time()

    # Serve from cache if still fresh
    cached = _CACHE.get("usd_kes_rate")
    fetched_at = _CACHE.get("usd_kes_fetched_at", 0.0)
    if cached and (now - fetched_at) < ttl_seconds:
        return float(cached)

    for source in FX_SOURCES:
        try:
            resp = requests.get(
                source["url"],
                params=source["params"],
                timeout=5,
            )
            resp.raise_for_status()
            data = resp.json() or {}
            rate = source["extract"](data)
            if not rate:
                raise ValueError("Rate missing in response")
            rate = float(rate)
            if rate <= 0:
                raise ValueError("Non-positive rate")

            _CACHE["usd_kes_rate"] = rate
            _CACHE["usd_kes_fetched_at"] = now
            print(f"[fx] ✅ Fetched USD→KES rate from {source['name']}: {rate}")
            return rate
        except Exception as e:
            print(f"[fx] ⚠️ {source['name']} failed: {e}")

    print(f"[fx] ⚠️ Falling back to Config.USD_TO_KES_RATE={fallback_rate}")
    return float(fallback_rate)


def convert_amount_to_kes(amount: float, currency: str) -> float:
    """Convert an amount in the given currency to KES.

    - If currency is USD, uses the live (or cached) USD→KES rate.
    - Otherwise assumes the amount is already in KES.
    """
    try:
        amount_val = float(amount or 0)
    except Exception:
        amount_val = 0.0

    currency_upper = str(currency or "").upper()
    if currency_upper == "USD":
        rate = get_usd_to_kes_rate()
        amount_kes = amount_val * rate
        print(
            f"[fx] 💱 Converted {amount_val:.2f} USD to {amount_kes:.2f} KES "
            f"(rate={rate})"
        )
        return amount_kes

    # Treat everything else as already in KES
    return amount_val


def compute_credit_days_from_kes(
    amount_in_kes: float, daily_rate_kes: float
) -> Tuple[int, float]:
    """Compute credit days and a rounded KES amount.

    Business rule from product:
      - Each day costs KES 5.
      - Rounded amount should end in either 0 or 5 (nearest multiple of 5).

    We:
      1. Round the KES amount to the nearest multiple of 5.
      2. Convert to credit days using the configured DAILY_RATE.
    """
    try:
        daily_rate = float(daily_rate_kes or 5.0)
    except Exception:
        daily_rate = 5.0

    if daily_rate <= 0:
        # Degenerate but safe fallback
        return int(amount_in_kes), float(amount_in_kes)

    # Round to nearest multiple of 5 shillings
    rounded_kes = round(float(amount_in_kes or 0.0) / 5.0) * 5.0

    # At least 1 day if there's any positive payment
    credit_days = max(1, int(round(rounded_kes / daily_rate)))
    return credit_days, rounded_kes


