"""Estimate sigma and k from market data.

sigma: mid-price volatility — estimate as std of log returns over a rolling window.
k:     exponential decay of fill probability with distance from mid — estimate by
       fitting lambda(delta) = A * exp(-k * delta) to historical trades that lifted
       the book at various distances.
"""

from __future__ import annotations

import numpy as np


def estimate_sigma(mid_prices: np.ndarray, dt_seconds: float = 1.0) -> float:
    """Volatility of log returns, annualized to per-second.

    mid_prices: array of mid prices (equally spaced in time)
    dt_seconds: time between consecutive observations
    """
    if len(mid_prices) < 2:
        return 0.0
    log_ret = np.diff(np.log(mid_prices))
    return float(np.std(log_ret, ddof=1) / np.sqrt(dt_seconds))


def estimate_k(distances: np.ndarray, fill_counts: np.ndarray) -> tuple[float, float]:
    """Fit lambda = A * exp(-k * delta) to fill count vs distance from mid.

    distances:   array of delta values (distance from mid, > 0)
    fill_counts: array of fill counts / intensities at each distance

    Returns (A, k). Fits by linearizing: log(lambda) = log(A) - k * delta.
    """
    mask = (fill_counts > 0) & (distances >= 0)
    if mask.sum() < 2:
        return 1.0, 1.0
    x = distances[mask]
    y = np.log(fill_counts[mask])
    # linear regression y = log(A) - k*x
    x_mean = x.mean()
    y_mean = y.mean()
    slope = ((x - x_mean) * (y - y_mean)).sum() / ((x - x_mean) ** 2).sum()
    intercept = y_mean - slope * x_mean
    k = -slope
    A = np.exp(intercept)
    return float(A), float(max(k, 1e-6))
