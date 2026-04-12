# av-stoikov-mm

[![CI](https://github.com/JKDasondee/av-stoikov-mm/actions/workflows/ci.yml/badge.svg)](https://github.com/JKDasondee/av-stoikov-mm/actions/workflows/ci.yml)
![Python](https://img.shields.io/badge/python-3.11+-blue)

**Avellaneda–Stoikov (2008) market maker reproduced on real Bybit BTCUSDT L2 tick data via hftbacktest.**

## Overview

Full implementation of the AS continuous-time stochastic optimal control market-making model. Runs against live-fetched Bybit BTCUSDT Level-2 orderbook data using hftbacktest's queue-position-aware fill model. Includes walk-forward evaluation, inventory-risk decomposition, and MLE estimation of model parameters (σ, k) from tick data.

## Model

```
Reservation price:   r(s, q, t) = s - q · γ · σ² · (T - t)
Optimal half-spread: δ* = γ · σ² · (T - t) + (2/γ) · ln(1 + γ/k)
Quotes:              bid = r - δ*,  ask = r + δ*
```

- `s` — mid price
- `q` — signed inventory
- `γ` — risk aversion parameter
- `σ` — per-tick mid-price volatility (estimated via log-return std)
- `k` — fill-intensity decay (estimated by fitting λ = A·exp(−k·δ) to historical trades)
- `T − t` — time remaining in session

When `q > 0` (long inventory), reservation price shifts down so quotes skew sell-heavy. Spread widens with volatility and as `T − t` grows.

## Architecture

```
Bybit public v5 L2 feed
  → scripts/fetch_l2.py        (raw tick collection)
  → hftbacktest replay         (queue position, latency, fee simulation)
  → AvellanedaStoikovParams    (γ, k, σ, T — estimated or grid-searched)
  → MMStrategy                 (on_book_update → quote(), on_fill → risk_check())
  → Walk-forward evaluator     (rolling IS/OOS windows)
  → Metrics                    (Sharpe net of fees, inventory σ, fill rate,
                                adverse-selection decomposition, max drawdown)
```

## Setup

```bash
pip install -e .[dev]
python scripts/fetch_l2.py --symbol BTCUSDT --days 7
python scripts/backtest_mm.py --gamma 0.1 --k 1.5 --walk_forward 5
```

## Results

| Metric                 | Target | Actual |
|------------------------|--------|--------|
| Sharpe (OOS, net fees) | ≥ 1.0  | TBD    |
| Max drawdown           | ≤ 10%  | TBD    |
| Fill rate              | ≥ 10%  | TBD    |
| Inventory σ            | < 30%  | TBD    |
| OOS/IS Sharpe ratio    | ≥ 0.5  | TBD    |

Results populated after backtest runs. If the model fails to reproduce cleanly on live Bybit data, the writeup will explain the breakdown.

## References

1. Avellaneda, M., & Stoikov, S. (2008). High-frequency trading in a limit order book. *Quantitative Finance*, 8(3), 217–224.
2. Guéant, O., Lehalle, C.-A., & Fernandez-Tapia, J. (2013). Dealing with the inventory risk. *Mathematics and Financial Economics*, 7(4), 477–507.
3. Cartea, Á., Jaimungal, S., & Penalva, J. (2015). *Algorithmic and High-Frequency Trading*. Cambridge.

## Stack

```
Python 3.10+ · hftbacktest · NumPy · pandas
Bybit public v5 WebSocket API
```

MIT License
