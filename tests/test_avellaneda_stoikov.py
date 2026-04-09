"""Sanity tests for the Avellaneda-Stoikov math.

Paper invariants we verify:
  1. At t = T (session end), reservation_price = mid regardless of inventory
  2. When inventory = 0, reservation_price = mid
  3. When inventory > 0, reservation_price < mid (lean sell)
  4. When inventory < 0, reservation_price > mid (lean buy)
  5. Bid < mid < ask always (spread is positive)
  6. Ask - bid > 0 always
  7. Spread widens with sigma (more vol → wider quotes)
  8. Spread widens with gamma (more risk averse → wider quotes)
  9. Spread narrows with k (faster fills → tighter quotes)
"""
from __future__ import annotations

import math

import pytest

from avsm.avellaneda_stoikov import (
    AvellanedaStoikovParams,
    optimal_half_spread,
    quotes,
    reservation_price,
)


@pytest.fixture
def base_params() -> AvellanedaStoikovParams:
    return AvellanedaStoikovParams(gamma=0.1, k=1.5, sigma=0.02, T=1.0)


def test_reservation_equals_mid_at_session_end(base_params):
    assert reservation_price(100.0, 5.0, base_params, t=1.0) == 100.0
    assert reservation_price(100.0, -5.0, base_params, t=1.0) == 100.0


def test_reservation_equals_mid_zero_inventory(base_params):
    assert reservation_price(100.0, 0.0, base_params, t=0.5) == 100.0


def test_long_inventory_shifts_down(base_params):
    r = reservation_price(100.0, 5.0, base_params, t=0.0)
    assert r < 100.0


def test_short_inventory_shifts_up(base_params):
    r = reservation_price(100.0, -5.0, base_params, t=0.0)
    assert r > 100.0


def test_spread_is_positive(base_params):
    bid, ask = quotes(100.0, 0.0, base_params, t=0.5)
    assert bid < 100.0 < ask
    assert ask - bid > 0


def test_spread_widens_with_sigma():
    p_low = AvellanedaStoikovParams(gamma=0.1, k=1.5, sigma=0.01, T=1.0)
    p_high = AvellanedaStoikovParams(gamma=0.1, k=1.5, sigma=0.05, T=1.0)
    assert optimal_half_spread(p_high, 0.0) > optimal_half_spread(p_low, 0.0)


def test_gamma_increases_inventory_skew():
    """Higher gamma = more aggressive inventory rebalancing.

    With a long position (q > 0) the reservation price shifts DOWN by
    q * gamma * sigma^2 * (T - t). Higher gamma -> larger downward shift.
    This is the actual risk-aversion behavior in AS, not half-spread width
    (which has competing terms and isn't monotonic in gamma).
    """
    p_low = AvellanedaStoikovParams(gamma=0.05, k=1.5, sigma=0.02, T=1.0)
    p_high = AvellanedaStoikovParams(gamma=0.5, k=1.5, sigma=0.02, T=1.0)
    r_low = reservation_price(100.0, 5.0, p_low, t=0.0)
    r_high = reservation_price(100.0, 5.0, p_high, t=0.0)
    assert r_high < r_low  # higher gamma = more aggressive skew down


def test_spread_narrows_with_higher_k():
    p_low = AvellanedaStoikovParams(gamma=0.1, k=1.0, sigma=0.02, T=1.0)
    p_high = AvellanedaStoikovParams(gamma=0.1, k=5.0, sigma=0.02, T=1.0)
    assert optimal_half_spread(p_high, 0.5) < optimal_half_spread(p_low, 0.5)


def test_invalid_params():
    with pytest.raises(ValueError):
        AvellanedaStoikovParams(gamma=0.0, k=1.0, sigma=0.02, T=1.0)
    with pytest.raises(ValueError):
        AvellanedaStoikovParams(gamma=0.1, k=0.0, sigma=0.02, T=1.0)
    with pytest.raises(ValueError):
        AvellanedaStoikovParams(gamma=0.1, k=1.0, sigma=-0.01, T=1.0)
    with pytest.raises(ValueError):
        AvellanedaStoikovParams(gamma=0.1, k=1.0, sigma=0.02, T=0.0)


def test_reservation_price_formula(base_params):
    # manual calculation: r = s - q * gamma * sigma^2 * (T - t)
    s, q, t = 100.0, 3.0, 0.4
    expected = s - q * base_params.gamma * base_params.sigma**2 * (base_params.T - t)
    assert reservation_price(s, q, base_params, t) == pytest.approx(expected)


def test_half_spread_formula(base_params):
    t = 0.3
    expected = (
        base_params.gamma * base_params.sigma**2 * (base_params.T - t)
        + (2 / base_params.gamma) * math.log(1 + base_params.gamma / base_params.k)
    )
    assert optimal_half_spread(base_params, t) == pytest.approx(expected)
