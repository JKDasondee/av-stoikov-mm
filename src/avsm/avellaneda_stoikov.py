"""Avellaneda-Stoikov (2008) market maker — pure math, no side effects.

Paper reference:
    Avellaneda, M., & Stoikov, S. (2008).
    High-frequency trading in a limit order book.
    Quantitative Finance, 8(3), 217-224.

Key formulas:

    reservation_price(s, q, gamma, sigma, T, t)
        r = s - q * gamma * sigma**2 * (T - t)

    optimal_half_spread(gamma, sigma, T, t, k)
        delta = gamma * sigma**2 * (T - t) + (2 / gamma) * log(1 + gamma / k)

    quotes(s, q, gamma, sigma, T, t, k)
        bid = reservation_price - delta
        ask = reservation_price + delta
"""
from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass(frozen=True)
class AvellanedaStoikovParams:
    """Static parameters for the AS model.

    gamma:  risk aversion (> 0). Higher = more skew, wider spread when inventoried.
    k:      exponential decay of fill probability with distance from mid.
            Higher k = fills happen close to mid, tighter spread optimal.
    sigma:  mid-price volatility estimate (per-second or per-tick).
    T:      end-of-session time (seconds from start, or bar count).
    """

    gamma: float
    k: float
    sigma: float
    T: float

    def __post_init__(self) -> None:
        if self.gamma <= 0:
            raise ValueError(f"gamma must be > 0, got {self.gamma}")
        if self.k <= 0:
            raise ValueError(f"k must be > 0, got {self.k}")
        if self.sigma < 0:
            raise ValueError(f"sigma must be >= 0, got {self.sigma}")
        if self.T <= 0:
            raise ValueError(f"T must be > 0, got {self.T}")


def reservation_price(mid: float, inventory: float, params: AvellanedaStoikovParams, t: float) -> float:
    """r(s, q, t) = s - q * gamma * sigma^2 * (T - t)

    When inventory q is long (positive), reservation price shifts down (sell more).
    When q is short (negative), shifts up (buy more).
    """
    if t >= params.T:
        return mid  # end of session — no inventory penalty remaining
    time_remaining = params.T - t
    skew = inventory * params.gamma * params.sigma**2 * time_remaining
    return mid - skew


def optimal_half_spread(params: AvellanedaStoikovParams, t: float) -> float:
    """delta* = gamma * sigma^2 * (T - t) + (2 / gamma) * log(1 + gamma / k)

    First term is the inventory-risk premium, decays to zero at session end.
    Second term is the pure market-making profit component (constant).
    """
    if t >= params.T:
        return (2 / params.gamma) * math.log(1 + params.gamma / params.k)
    time_remaining = params.T - t
    inventory_premium = params.gamma * params.sigma**2 * time_remaining
    mm_profit = (2 / params.gamma) * math.log(1 + params.gamma / params.k)
    return inventory_premium + mm_profit


def quotes(
    mid: float,
    inventory: float,
    params: AvellanedaStoikovParams,
    t: float,
) -> tuple[float, float]:
    """Return (bid, ask) from the full AS model."""
    r = reservation_price(mid, inventory, params, t)
    delta = optimal_half_spread(params, t)
    return r - delta, r + delta


def expected_fill_intensity(distance_from_mid: float, params: AvellanedaStoikovParams) -> float:
    """lambda(delta) = A * exp(-k * delta)

    Only the relative intensity matters for the optimal spread derivation, so we
    return exp(-k * delta) here and let the caller scale by A if they have it.
    """
    return math.exp(-params.k * distance_from_mid)
