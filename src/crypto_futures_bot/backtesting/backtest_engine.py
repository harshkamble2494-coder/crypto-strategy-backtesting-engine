from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from crypto_futures_bot.backtesting.portfolio import Portfolio
from crypto_futures_bot.backtesting.trade import Trade
from crypto_futures_bot.config.models import AppConfig
from crypto_futures_bot.execution.execution_engine import ExecutionEngine
from crypto_futures_bot.indicators.indicator_engine import IndicatorEngine
from crypto_futures_bot.risk_management.position_sizer import PositionSizer
from crypto_futures_bot.risk_management.risk_manager import RiskManager
from crypto_futures_bot.strategy.factory import create_strategy
from crypto_futures_bot.strategy.signals import SignalType


@dataclass(frozen=True)
class BlockedPeriod:
    start_time: pd.Timestamp
    end_time: pd.Timestamp
    resume_mode: str
    consecutive_losses: int
    blocked_signals: int
    duration_candles: int


@dataclass(frozen=True)
class CircuitBreakerStats:
    blocked_trades: int
    cooldown_periods: int
    average_cooldown_duration: float
    consecutive_loss_clusters: int
    blocked_periods: list[BlockedPeriod]


@dataclass(frozen=True)
class BacktestResult:
    trades: list[Trade]
    equity_curve: pd.DataFrame
    candles: pd.DataFrame
    output_dir: Path
    circuit_breaker_stats: CircuitBreakerStats


class BacktestEngine:
    def __init__(self, config: AppConfig, output_dir: Path) -> None:
        self.config = config
        self.output_dir = output_dir
        self.indicators = IndicatorEngine(config.strategy)
        self.strategy = create_strategy(config.strategy)
        self.position_sizer = PositionSizer(config.risk)
        self.risk_manager = RiskManager(config.risk, config.backtest.initial_capital)
        self.execution = ExecutionEngine(config.risk, config.costs)
        self.portfolio = Portfolio(config.backtest.initial_capital)
        self.trades: list[Trade] = []
        self._cooldown_remaining = 0
        self._consecutive_losses = 0
        self._circuit_breaker_active = False
        self._circuit_breaker_candles_remaining = 0
        self._current_blocked_start: pd.Timestamp | None = None
        self._current_blocked_signals = 0
        self._current_blocked_duration = 0
        self._current_blocked_losses = 0
        self._blocked_periods: list[BlockedPeriod] = []

    def run(self, candles: pd.DataFrame) -> BacktestResult:
        data = self.indicators.add_indicators(candles)
        warmup = max(self.config.strategy.ema_trend, self.config.strategy.rsi_length) + 1

        for index in range(1, len(data)):
            current = data.iloc[index]
            previous = data.iloc[index - 1]
            timestamp = current["timestamp"]
            close_price = float(current["close"])

            self.risk_manager.register_day(timestamp, self.portfolio.current_equity(close_price))
            signal = self.strategy.generate_signal(previous, current) if index >= warmup else SignalType.NONE

            closed_for_opposite = self._handle_open_position(current, signal)
            if closed_for_opposite:
                self._try_open(signal, current, bypass_cooldown=True)
            elif self.portfolio.position is None:
                self._tick_cooldown()
                self._try_open(signal, current, bypass_cooldown=False)

            self.portfolio.record_equity(timestamp, close_price)

        return BacktestResult(
            trades=self.trades,
            equity_curve=self.portfolio.equity_dataframe(),
            candles=data,
            output_dir=self.output_dir,
            circuit_breaker_stats=self._circuit_breaker_stats(),
        )

    def _handle_open_position(self, candle: pd.Series, signal: SignalType) -> bool:
        position = self.portfolio.position
        if position is None:
            return False

        opposite_signal = (
            (position.side.value == SignalType.LONG.value and signal == SignalType.SHORT)
            or (position.side.value == SignalType.SHORT.value and signal == SignalType.LONG)
        )
        exit_check = self.execution.check_exit(position, candle, opposite_signal)
        if exit_check is None:
            return False

        raw_exit_price, exit_reason = exit_check
        trade = self.execution.close_position(
            position=position,
            exit_time=candle["timestamp"],
            raw_exit_price=raw_exit_price,
            exit_reason=exit_reason,
            resulting_balance=self.portfolio.balance,
        )
        self.portfolio.balance += trade.net_profit_loss
        trade = self._trade_with_balance(trade, self.portfolio.balance)
        self.portfolio.position = None
        self.trades.append(trade)
        self.risk_manager.record_realized_pnl(candle["timestamp"], trade.net_profit_loss)
        self._record_trade_outcome(candle["timestamp"], trade.net_profit_loss)

        if exit_reason == "OPPOSITE_SIGNAL":
            return True

        self._cooldown_remaining = self.config.strategy.cooldown_candles
        return False

    def _try_open(self, signal: SignalType, candle: pd.Series, bypass_cooldown: bool) -> None:
        if signal == SignalType.NONE or self.portfolio.position is not None:
            self._advance_circuit_breaker(candle, signal)
            return
        timestamp = candle["timestamp"]
        price = float(candle["close"])
        if not bypass_cooldown and self._cooldown_remaining > 0:
            self._advance_circuit_breaker(candle, signal)
            return
        if not self.risk_manager.can_open_new_trade(timestamp):
            self._advance_circuit_breaker(candle, signal)
            return
        if self._circuit_breaker_blocks_trade(candle, signal):
            return

        equity = self.portfolio.current_equity(price)
        quantity = self.position_sizer.calculate_quantity(equity, price)
        if quantity <= 0:
            return

        self.portfolio.position = self.execution.open_position(
            signal=signal,
            timestamp=timestamp,
            price=price,
            quantity=quantity,
            atr=float(candle["atr"]) if "atr" in candle else None,
        )

    def _record_trade_outcome(self, timestamp: pd.Timestamp, net_pnl: float) -> None:
        if net_pnl < 0:
            self._consecutive_losses += 1
            if self._should_activate_circuit_breaker():
                self._activate_circuit_breaker(timestamp)
        else:
            self._consecutive_losses = 0

    def _should_activate_circuit_breaker(self) -> bool:
        config = self.config.circuit_breaker
        return (
            config.enabled
            and not self._circuit_breaker_active
            and self._consecutive_losses >= config.consecutive_loss_threshold
        )

    def _activate_circuit_breaker(self, timestamp: pd.Timestamp) -> None:
        config = self.config.circuit_breaker
        if config.resume_mode not in {"candles", "next_signal"}:
            raise ValueError(f"Unsupported circuit breaker resume mode: {config.resume_mode}")
        self._circuit_breaker_active = True
        self._circuit_breaker_candles_remaining = config.cooldown_candles
        self._current_blocked_start = timestamp
        self._current_blocked_signals = 0
        self._current_blocked_duration = 0
        self._current_blocked_losses = self._consecutive_losses

    def _circuit_breaker_blocks_trade(self, candle: pd.Series, signal: SignalType) -> bool:
        if not self._circuit_breaker_active:
            return False

        self._current_blocked_duration += 1
        self._current_blocked_signals += 1
        if self.config.circuit_breaker.resume_mode == "candles":
            self._circuit_breaker_candles_remaining -= 1
            if self._circuit_breaker_candles_remaining <= 0:
                self._close_blocked_period(candle["timestamp"])
        elif self.config.circuit_breaker.resume_mode == "next_signal" and signal != SignalType.NONE:
            self._close_blocked_period(candle["timestamp"])
        return True

    def _advance_circuit_breaker(self, candle: pd.Series, signal: SignalType) -> None:
        if not self._circuit_breaker_active:
            return

        self._current_blocked_duration += 1
        if self.config.circuit_breaker.resume_mode == "candles":
            self._circuit_breaker_candles_remaining -= 1
            if self._circuit_breaker_candles_remaining <= 0:
                self._close_blocked_period(candle["timestamp"])
        elif self.config.circuit_breaker.resume_mode == "next_signal" and signal != SignalType.NONE:
            self._close_blocked_period(candle["timestamp"])

    def _close_blocked_period(self, end_time: pd.Timestamp) -> None:
        if self._current_blocked_start is None:
            return
        self._blocked_periods.append(
            BlockedPeriod(
                start_time=self._current_blocked_start,
                end_time=end_time,
                resume_mode=self.config.circuit_breaker.resume_mode,
                consecutive_losses=self._current_blocked_losses,
                blocked_signals=self._current_blocked_signals,
                duration_candles=self._current_blocked_duration,
            )
        )
        self._circuit_breaker_active = False
        self._circuit_breaker_candles_remaining = 0
        self._current_blocked_start = None
        self._current_blocked_signals = 0
        self._current_blocked_duration = 0
        self._current_blocked_losses = 0
        self._consecutive_losses = 0

    def _circuit_breaker_stats(self) -> CircuitBreakerStats:
        periods = list(self._blocked_periods)
        if self._circuit_breaker_active and self.portfolio.equity_curve and self._current_blocked_start is not None:
            periods.append(
                BlockedPeriod(
                    start_time=self._current_blocked_start,
                    end_time=self.portfolio.equity_curve[-1].timestamp,
                    resume_mode=self.config.circuit_breaker.resume_mode,
                    consecutive_losses=self._current_blocked_losses,
                    blocked_signals=self._current_blocked_signals,
                    duration_candles=self._current_blocked_duration,
                )
            )
        average_duration = (
            sum(period.duration_candles for period in periods) / len(periods)
            if periods
            else 0.0
        )
        return CircuitBreakerStats(
            blocked_trades=sum(period.blocked_signals for period in periods),
            cooldown_periods=len(periods),
            average_cooldown_duration=average_duration,
            consecutive_loss_clusters=len(periods),
            blocked_periods=periods,
        )

    def _tick_cooldown(self) -> None:
        if self._cooldown_remaining > 0:
            self._cooldown_remaining -= 1

    @staticmethod
    def _trade_with_balance(trade: Trade, balance: float) -> Trade:
        return Trade(
            entry_time=trade.entry_time,
            exit_time=trade.exit_time,
            direction=trade.direction,
            entry_price=trade.entry_price,
            exit_price=trade.exit_price,
            stop_loss=trade.stop_loss,
            take_profit=trade.take_profit,
            position_size=trade.position_size,
            gross_profit_loss=trade.gross_profit_loss,
            net_profit_loss=trade.net_profit_loss,
            account_balance=balance,
            trade_duration=trade.trade_duration,
            exit_reason=trade.exit_reason,
            fees=trade.fees,
        )
