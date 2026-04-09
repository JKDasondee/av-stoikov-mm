# av-stoikov-mm

Reproduction of **Avellaneda & Stoikov (2008)** "High-frequency trading in a limit order book" on real Bybit BTCUSDT Level-2 orderbook data using [hftbacktest](https://github.com/nkaz001/hftbacktest).

Full walk-forward backtest with inventory risk analysis, adverse selection decomposition, and queue-position-aware fill modeling.

## Paper in 3 equations

**Reservation price** (fair price adjusted for current inventory):

```
r(s, q, t) = s − q · γ · σ² · (T − t)
```

- `s` = mid price
- `q` = current inventory (signed)
- `γ` = risk aversion parameter
- `σ` = volatility estimate
- `T − t` = time remaining in trading session

**Optimal half-spread** (around reservation price):

```
δ* = γ · σ² · (T − t) + (2/γ) · ln(1 + γ/k)
```

- `k` = exponential decay of fill probability with distance from mid

**Quotes**:

```
bid = r − δ*
ask = r + δ*
```

When inventory is long (`q > 0`), the reservation price shifts down so quotes lean sell-heavy. When short, opposite. The spread widens with volatility and as time runs out.

## Architecture

```
Bybit public v5 L2 feed  ──▶  hftbacktest replay (queue position, latency)
                                       │
                                       ▼
                       ┌────────────────────────────┐
                       │   AvellanedaStoikovQuoter  │
                       │    - reservation_price()   │
                       │    - optimal_spread()      │
                       │    - estimate_sigma()      │
                       │    - estimate_k()          │
                       │    - quote()               │
                       └──────────────┬─────────────┘
                                      │
                                      ▼
                       ┌────────────────────────────┐
                       │    MMStrategy (hftbacktest)│
                       │    - on_book_update()      │
                       │    - on_fill()             │
                       │    - risk_check()          │
                       └──────────────┬─────────────┘
                                      │
                                      ▼
                       ┌────────────────────────────┐
                       │    Metrics + Reports       │
                       │    - Sharpe (net of fees)  │
                       │    - Inventory σ           │
                       │    - Fill rate             │
                       │    - Adverse selection     │
                       │    - Max drawdown          │
                       └────────────────────────────┘
```

## Setup

```bash
pip install -e .[dev]
python scripts/fetch_l2.py --symbol BTCUSDT --days 7
python scripts/backtest_mm.py --gamma 0.1 --k 1.5 --walk_forward 5
```

## Results

*(populated after backtest runs — deliberately blank for now)*

| Metric                 | Target | Actual |
|------------------------|--------|--------|
| Sharpe (OOS, net fees) | ≥ 1.0  | TBD    |
| Max drawdown           | ≤ 10%  | TBD    |
| Fill rate              | ≥ 10%  | TBD    |
| Inventory σ            | < 30%  | TBD    |
| OOS/IS Sharpe ratio    | ≥ 0.5  | TBD    |

Honest results only. If the paper doesn't reproduce cleanly on real Bybit data, the writeup will explain why.

## References

1. Avellaneda, M., & Stoikov, S. (2008). High-frequency trading in a limit order book. *Quantitative Finance*, 8(3), 217–224.
2. Guéant, O., Lehalle, C.-A., & Fernandez-Tapia, J. (2013). Dealing with the inventory risk: a solution to the market making problem. *Mathematics and Financial Economics*, 7(4), 477–507.
3. [nkaz001/hftbacktest](https://github.com/nkaz001/hftbacktest) — the backtest framework.
4. Cartea, Á., Jaimungal, S., & Penalva, J. (2015). *Algorithmic and High-Frequency Trading*. Cambridge.

## License

MIT
