#!/usr/bin/env python
"""Fetch L2 orderbook snapshots from Bybit public v5 API.

Note: Bybit doesn't expose historical L2 via REST. Two options:
  1. Live capture via websocket: pybit WebsocketClient, save snapshots
  2. Paid data from tardis.dev (has Bybit L2 feed, ~1 USD/day/symbol)

This script does option 1 (live capture). For backtest use, run this script
for N days in a screen/tmux session, or use tardis.dev.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parents[1] / "data" / "raw"


def _stream_via_websocket(symbol: str, depth: int, out_dir: Path, duration_s: int) -> None:
    try:
        from pybit.unified_trading import WebSocket
    except ImportError:
        print("pip install pybit", file=sys.stderr)
        sys.exit(1)

    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / f"{symbol}_l2_depth{depth}_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S')}.ndjson"
    f = out_file.open("w")
    print(f"streaming to {out_file} for {duration_s}s")

    n = [0]
    start = time.time()

    def handler(msg: dict) -> None:
        msg["local_ts_ns"] = time.time_ns()
        f.write(json.dumps(msg) + "\n")
        n[0] += 1
        if n[0] % 100 == 0:
            elapsed = time.time() - start
            print(f"  {n[0]} msgs in {elapsed:.1f}s")

    ws = WebSocket(testnet=False, channel_type="linear")
    ws.orderbook_stream(depth=depth, symbol=symbol, callback=handler)

    try:
        while time.time() - start < duration_s:
            time.sleep(1)
    except KeyboardInterrupt:
        pass
    finally:
        f.close()
        print(f"done: {n[0]} msgs written to {out_file}")


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--symbol", default="BTCUSDT")
    p.add_argument("--depth", type=int, default=50, choices=[1, 50, 200, 500])
    p.add_argument("--duration_s", type=int, default=3600, help="capture duration in seconds")
    args = p.parse_args()

    _stream_via_websocket(args.symbol, args.depth, DATA_DIR, args.duration_s)


if __name__ == "__main__":
    main()
