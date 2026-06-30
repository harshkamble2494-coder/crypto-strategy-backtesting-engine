from __future__ import annotations

from crypto_futures_bot.config.models import StrategyConfig
from crypto_futures_bot.strategy.base import Strategy
from crypto_futures_bot.strategy.ema_rsi_strategy import EmaRsiStrategy
from crypto_futures_bot.strategy.trend_quality_ema_rsi_strategy import TrendQualityEmaRsiStrategy


def create_strategy(config: StrategyConfig) -> Strategy:
    strategies = {
        "ema_rsi_v1": EmaRsiStrategy,
        "trend_quality_ema_rsi_v2": TrendQualityEmaRsiStrategy,
    }
    try:
        strategy_cls = strategies[config.name]
    except KeyError as exc:
        available = ", ".join(sorted(strategies))
        raise ValueError(f"Unknown strategy '{config.name}'. Available strategies: {available}") from exc
    return strategy_cls(config)
