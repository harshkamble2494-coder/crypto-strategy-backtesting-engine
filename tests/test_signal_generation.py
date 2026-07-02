import pandas as pd

from crypto_futures_bot.config.models import StrategyConfig
from crypto_futures_bot.strategy.ema_rsi_strategy import EmaRsiStrategy
from crypto_futures_bot.strategy.signals import SignalType


def _config() -> StrategyConfig:
    return StrategyConfig(
        ema_fast=9,
        ema_slow=21,
        ema_trend=200,
        rsi_length=14,
        rsi_long_threshold=55,
        rsi_short_threshold=45,
        cooldown_candles=1,
    )


def test_long_signal_requires_cross_above_trend_and_rsi() -> None:
    previous = pd.Series({"ema_fast": 99, "ema_slow": 100, "ema_trend": 90, "rsi": 56, "close": 101})
    current = pd.Series({"ema_fast": 101, "ema_slow": 100, "ema_trend": 90, "rsi": 60, "close": 110})

    assert EmaRsiStrategy(_config()).generate_signal(previous, current) == SignalType.LONG


def test_short_signal_requires_cross_below_trend_and_rsi() -> None:
    previous = pd.Series({"ema_fast": 101, "ema_slow": 100, "ema_trend": 110, "rsi": 44, "close": 100})
    current = pd.Series({"ema_fast": 99, "ema_slow": 100, "ema_trend": 110, "rsi": 40, "close": 90})

    assert EmaRsiStrategy(_config()).generate_signal(previous, current) == SignalType.SHORT


def test_no_signal_without_crossover() -> None:
    previous = pd.Series({"ema_fast": 101, "ema_slow": 100, "ema_trend": 90, "rsi": 60, "close": 110})
    current = pd.Series({"ema_fast": 102, "ema_slow": 100, "ema_trend": 90, "rsi": 60, "close": 111})

    assert EmaRsiStrategy(_config()).generate_signal(previous, current) == SignalType.NONE


def test_adx_filter_blocks_weak_trend_signal_when_enabled() -> None:
    config = StrategyConfig(
        ema_fast=9,
        ema_slow=21,
        ema_trend=200,
        rsi_length=14,
        rsi_long_threshold=55,
        rsi_short_threshold=45,
        cooldown_candles=1,
        use_adx_filter=True,
        min_adx=20,
    )
    previous = pd.Series({"ema_fast": 99, "ema_slow": 100, "ema_trend": 90, "rsi": 56, "adx": 18, "close": 101})
    current = pd.Series({"ema_fast": 101, "ema_slow": 100, "ema_trend": 90, "rsi": 60, "adx": 18, "close": 110})

    assert EmaRsiStrategy(config).generate_signal(previous, current) == SignalType.NONE


def test_adx_filter_allows_strong_trend_signal_when_enabled() -> None:
    config = StrategyConfig(
        ema_fast=9,
        ema_slow=21,
        ema_trend=200,
        rsi_length=14,
        rsi_long_threshold=55,
        rsi_short_threshold=45,
        cooldown_candles=1,
        use_adx_filter=True,
        min_adx=20,
    )
    previous = pd.Series({"ema_fast": 99, "ema_slow": 100, "ema_trend": 90, "rsi": 56, "adx": 24, "close": 101})
    current = pd.Series({"ema_fast": 101, "ema_slow": 100, "ema_trend": 90, "rsi": 60, "adx": 24, "close": 110})

    assert EmaRsiStrategy(config).generate_signal(previous, current) == SignalType.LONG


def test_trend_slope_filter_blocks_long_against_falling_trend() -> None:
    config = StrategyConfig(
        ema_fast=9,
        ema_slow=21,
        ema_trend=200,
        rsi_length=14,
        rsi_long_threshold=55,
        rsi_short_threshold=45,
        cooldown_candles=1,
        use_trend_slope_filter=True,
    )
    previous = pd.Series(
        {"ema_fast": 99, "ema_slow": 100, "ema_trend": 90, "rsi": 56, "ema_trend_slope": -1, "close": 101}
    )
    current = pd.Series(
        {"ema_fast": 101, "ema_slow": 100, "ema_trend": 90, "rsi": 60, "ema_trend_slope": -1, "close": 110}
    )

    assert EmaRsiStrategy(config).generate_signal(previous, current) == SignalType.NONE


def test_trend_slope_filter_allows_long_with_rising_trend() -> None:
    config = StrategyConfig(
        ema_fast=9,
        ema_slow=21,
        ema_trend=200,
        rsi_length=14,
        rsi_long_threshold=55,
        rsi_short_threshold=45,
        cooldown_candles=1,
        use_trend_slope_filter=True,
    )
    previous = pd.Series(
        {"ema_fast": 99, "ema_slow": 100, "ema_trend": 90, "rsi": 56, "ema_trend_slope": 1, "close": 101}
    )
    current = pd.Series(
        {"ema_fast": 101, "ema_slow": 100, "ema_trend": 90, "rsi": 60, "ema_trend_slope": 1, "close": 110}
    )

    assert EmaRsiStrategy(config).generate_signal(previous, current) == SignalType.LONG
