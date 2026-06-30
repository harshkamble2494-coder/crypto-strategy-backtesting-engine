from __future__ import annotations

import argparse
import csv
import json
import time
from datetime import UTC, datetime, timedelta
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import urlopen


BASE_URL = "https://fapi.binance.com/fapi/v1/klines"
INTERVAL_MS = 60 * 60 * 1000


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Download public Binance USD-M futures klines.")
    parser.add_argument("--symbol", default="BTCUSDT")
    parser.add_argument("--interval", default="1h")
    parser.add_argument("--years", type=float, default=2.0)
    parser.add_argument("--output", default="data/raw/BTCUSDT_1h.csv")
    return parser.parse_args()


def request_klines(symbol: str, interval: str, start_ms: int, end_ms: int) -> list[list[object]]:
    params = urlencode(
        {
            "symbol": symbol,
            "interval": interval,
            "startTime": start_ms,
            "endTime": end_ms,
            "limit": 1000,
        }
    )
    with urlopen(f"{BASE_URL}?{params}", timeout=30) as response:
        payload = response.read().decode("utf-8")
    data = json.loads(payload)
    if not isinstance(data, list):
        raise RuntimeError(f"Unexpected Binance response: {data}")
    return data


def download(symbol: str, interval: str, years: float) -> list[dict[str, object]]:
    end = datetime.now(UTC).replace(minute=0, second=0, microsecond=0)
    start = end - timedelta(days=365.25 * years)
    start_ms = int(start.timestamp() * 1000)
    end_ms = int(end.timestamp() * 1000)

    rows: list[dict[str, object]] = []
    cursor = start_ms
    while cursor < end_ms:
        batch = request_klines(symbol, interval, cursor, end_ms)
        if not batch:
            break

        for kline in batch:
            open_time = int(kline[0])
            if open_time > end_ms:
                continue
            rows.append(
                {
                    "timestamp": datetime.fromtimestamp(open_time / 1000, tz=UTC).isoformat(),
                    "open": float(kline[1]),
                    "high": float(kline[2]),
                    "low": float(kline[3]),
                    "close": float(kline[4]),
                    "volume": float(kline[5]),
                }
            )

        next_cursor = int(batch[-1][0]) + INTERVAL_MS
        if next_cursor <= cursor:
            raise RuntimeError("Download cursor did not advance.")
        cursor = next_cursor
        time.sleep(0.15)

    deduped = {row["timestamp"]: row for row in rows}
    return [deduped[key] for key in sorted(deduped)]


def write_csv(rows: list[dict[str, object]], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=["timestamp", "open", "high", "low", "close", "volume"])
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    args = parse_args()
    rows = download(args.symbol, args.interval, args.years)
    if len(rows) < 365 * 24:
        raise RuntimeError(f"Downloaded too few candles for a 2-year backtest: {len(rows)}")
    write_csv(rows, Path(args.output))
    print(f"Wrote {len(rows)} candles to {args.output}")


if __name__ == "__main__":
    main()
