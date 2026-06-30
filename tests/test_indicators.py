import pandas as pd

from crypto_futures_bot.config.models import StrategyConfig
from crypto_futures_bot.indicators.indicator_engine import IndicatorEngine


def test_indicator_engine_adds_expected_columns() -> None:
    config = StrategyConfig(
        ema_fast=3,
        ema_slow=5,
        ema_trend=8,
        rsi_length=3,
        rsi_long_threshold=55,
        rsi_short_threshold=45,
        cooldown_candles=1,
    )
    close = [100, 101, 102, 103, 102, 104, 105, 106, 107]
    candles = pd.DataFrame(
        {
            "open": close,
            "high": [value + 1 for value in close],
            "low": [value - 1 for value in close],
            "close": close,
            "volume": [1000 + index * 10 for index in range(len(close))],
        }
    )

    result = IndicatorEngine(config).add_indicators(candles)

    assert {"ema_fast", "ema_slow", "ema_trend", "rsi", "atr", "adx", "volume_ratio"}.issubset(result.columns)
    assert result["ema_fast"].iloc[-1] > result["ema_slow"].iloc[-1]
    assert result["rsi"].between(0, 100).all()
