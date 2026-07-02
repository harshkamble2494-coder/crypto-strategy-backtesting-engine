from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class ProjectConfig:
    name: str
    timezone: str


@dataclass(frozen=True)
class DataConfig:
    symbol: str
    timeframe: str
    csv_path: Path
    start_date: str | None
    end_date: str | None
    default_lookback_years: int


@dataclass(frozen=True)
class BacktestConfig:
    initial_capital: float
    results_dir: Path


@dataclass(frozen=True)
class StrategyConfig:
    ema_fast: int
    ema_slow: int
    ema_trend: int
    rsi_length: int
    rsi_long_threshold: float
    rsi_short_threshold: float
    cooldown_candles: int
    name: str = "ema_rsi_v1"
    atr_length: int = 14
    adx_length: int = 14
    use_adx_filter: bool = False
    use_trend_slope_filter: bool = False
    volume_sma_length: int = 20
    trend_slope_lookback: int = 24
    min_adx: float = 20.0
    min_trend_distance_atr: float = 0.25
    min_volume_ratio: float = 1.0


@dataclass(frozen=True)
class RiskConfig:
    leverage: float
    risk_per_trade: float
    stop_loss_pct: float
    take_profit_pct: float
    max_daily_loss_pct: float
    exit_mode: str = "fixed"
    take_profit_enabled: bool = True
    atr_stop_loss_multiplier: float = 1.5
    atr_take_profit_multiplier: float = 3.0
    break_even_enabled: bool = False
    break_even_trigger_atr_multiplier: float = 1.0
    trailing_stop_enabled: bool = False
    trailing_stop_activation_atr_multiplier: float = 1.0
    trailing_stop_atr_multiplier: float = 2.0


@dataclass(frozen=True)
class CircuitBreakerConfig:
    enabled: bool = False
    consecutive_loss_threshold: int = 3
    cooldown_candles: int = 24
    resume_mode: str = "candles"


@dataclass(frozen=True)
class CostConfig:
    fee_rate: float
    slippage_pct: float


@dataclass(frozen=True)
class LoggingConfig:
    level: str
    file_path: Path


@dataclass(frozen=True)
class AppConfig:
    project: ProjectConfig
    data: DataConfig
    backtest: BacktestConfig
    strategy: StrategyConfig
    risk: RiskConfig
    circuit_breaker: CircuitBreakerConfig
    costs: CostConfig
    logging: LoggingConfig

    @classmethod
    def from_dict(cls, raw: dict[str, Any], project_root: Path) -> "AppConfig":
        data = raw["data"]
        backtest = raw["backtest"]
        logging_config = raw["logging"]
        return cls(
            project=ProjectConfig(**raw["project"]),
            data=DataConfig(
                symbol=data["symbol"],
                timeframe=data["timeframe"],
                csv_path=_resolve_path(project_root, data["csv_path"]),
                start_date=data.get("start_date"),
                end_date=data.get("end_date"),
                default_lookback_years=int(data["default_lookback_years"]),
            ),
            backtest=BacktestConfig(
                initial_capital=float(backtest["initial_capital"]),
                results_dir=_resolve_path(project_root, backtest["results_dir"]),
            ),
            strategy=StrategyConfig(**raw["strategy"]),
            risk=RiskConfig(**raw["risk"]),
            circuit_breaker=CircuitBreakerConfig(**raw.get("circuit_breaker", {})),
            costs=CostConfig(**raw["costs"]),
            logging=LoggingConfig(
                level=logging_config["level"],
                file_path=_resolve_path(project_root, logging_config["file_path"]),
            ),
        )


def _resolve_path(project_root: Path, value: str | Path) -> Path:
    path = Path(value)
    return path if path.is_absolute() else project_root / path
