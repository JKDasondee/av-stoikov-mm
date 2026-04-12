"""Market-making-specific metrics — PnL, inventory risk, adverse selection."""

from __future__ import annotations

import numpy as np


def sharpe(returns: np.ndarray, periods_per_year: float = 365 * 24 * 3600) -> float:
    """Sharpe ratio annualized. Default: per-second returns."""
    r = returns[~np.isnan(returns)]
    if len(r) < 2 or r.std(ddof=0) == 0:
        return 0.0
    return float(np.sqrt(periods_per_year) * r.mean() / r.std(ddof=0))


def max_drawdown(equity: np.ndarray) -> float:
    peak = np.maximum.accumulate(equity)
    dd = (equity - peak) / peak
    return float(dd.min()) if len(dd) > 0 else 0.0


def inventory_variance(inventory_series: np.ndarray) -> float:
    """Std of inventory over time — lower is better for a market maker."""
    return float(np.std(inventory_series, ddof=0))


def fill_rate(n_fills: int, n_quotes: int) -> float:
    if n_quotes == 0:
        return 0.0
    return n_fills / n_quotes


def adverse_selection(
    fill_prices: np.ndarray,
    mid_after: np.ndarray,
    sides: np.ndarray,
) -> float:
    """Adverse selection = how much mid moves against you after a fill.

    fill_prices: price at which your quote was filled
    mid_after:   mid price N ticks / seconds after the fill
    sides:       +1 for your buy (maker bid lifted), -1 for your sell (maker ask hit)

    Returns average adverse move in bps. Negative = you got picked off on average.
    """
    if len(fill_prices) == 0:
        return 0.0
    # if you bought (side=+1) and mid drops, that's adverse (negative PnL on inventory)
    move = (mid_after - fill_prices) * sides
    return float((move / fill_prices).mean() * 1e4)  # in bps


def summary(
    equity: np.ndarray,
    inventory_series: np.ndarray,
    n_fills: int,
    n_quotes: int,
    adv_sel_bps: float,
    periods_per_year: float = 365 * 24 * 3600,
) -> dict:
    returns = np.diff(equity) / equity[:-1] if len(equity) > 1 else np.array([])
    return {
        "sharpe": round(sharpe(returns, periods_per_year), 3),
        "max_drawdown": round(max_drawdown(equity), 4),
        "inventory_sigma": round(inventory_variance(inventory_series), 4),
        "fill_rate": round(fill_rate(n_fills, n_quotes), 4),
        "n_fills": int(n_fills),
        "n_quotes": int(n_quotes),
        "adverse_selection_bps": round(adv_sel_bps, 3),
        "final_equity": round(float(equity[-1]), 2) if len(equity) > 0 else 0.0,
    }
