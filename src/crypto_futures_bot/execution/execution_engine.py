from __future__ import annotations

import pandas as pd

from crypto_futures_bot.backtesting.trade import Trade
from crypto_futures_bot.config.models import CostConfig, RiskConfig
from crypto_futures_bot.execution.position import Position, PositionSide
from crypto_futures_bot.strategy.signals import SignalType


class ExecutionEngine:
    def __init__(self, risk_config: RiskConfig, cost_config: CostConfig) -> None:
        self.risk_config = risk_config
        self.cost_config = cost_config

    def open_position(
        self,
        signal: SignalType,
        timestamp: pd.Timestamp,
        price: float,
        quantity: float,
        atr: float | None = None,
    ) -> Position:
        if signal not in {SignalType.LONG, SignalType.SHORT}:
            raise ValueError(f"Cannot open position for signal: {signal}")

        side = PositionSide.LONG if signal == SignalType.LONG else PositionSide.SHORT
        entry_price = self._apply_entry_slippage(price, side)
        stop_loss, take_profit = self._risk_prices(entry_price, side, atr)
        entry_fee = self._fee(entry_price, quantity)
        return Position(
            side=side,
            entry_time=timestamp,
            entry_price=entry_price,
            quantity=quantity,
            stop_loss=stop_loss,
            take_profit=take_profit,
            entry_fee=entry_fee,
            entry_atr=atr,
        )

    def check_exit(self, position: Position, candle: pd.Series, opposite_signal: bool) -> tuple[float, str] | None:
        if position.side == PositionSide.LONG:
            if candle["low"] <= position.stop_loss:
                return position.stop_loss, "BREAK_EVEN_STOP" if position.break_even_activated else "STOP_LOSS"
            self._activate_break_even_if_triggered(position, candle)
            if candle["low"] <= position.stop_loss:
                return position.stop_loss, "BREAK_EVEN_STOP"
            if candle["high"] >= position.take_profit:
                return position.take_profit, "TAKE_PROFIT"
        else:
            if candle["high"] >= position.stop_loss:
                return position.stop_loss, "BREAK_EVEN_STOP" if position.break_even_activated else "STOP_LOSS"
            self._activate_break_even_if_triggered(position, candle)
            if candle["high"] >= position.stop_loss:
                return position.stop_loss, "BREAK_EVEN_STOP"
            if candle["low"] <= position.take_profit:
                return position.take_profit, "TAKE_PROFIT"

        if opposite_signal:
            return float(candle["close"]), "OPPOSITE_SIGNAL"
        return None

    def close_position(
        self,
        position: Position,
        exit_time: pd.Timestamp,
        raw_exit_price: float,
        exit_reason: str,
        resulting_balance: float,
    ) -> Trade:
        exit_price = self._apply_exit_slippage(raw_exit_price, position.side)
        gross_pnl = self._gross_pnl(position, exit_price)
        exit_fee = self._fee(exit_price, position.quantity)
        total_fees = position.entry_fee + exit_fee
        net_pnl = gross_pnl - total_fees
        return Trade(
            entry_time=position.entry_time,
            exit_time=exit_time,
            direction=position.side.value,
            entry_price=position.entry_price,
            exit_price=exit_price,
            stop_loss=position.stop_loss,
            take_profit=position.take_profit,
            position_size=position.quantity,
            gross_profit_loss=gross_pnl,
            net_profit_loss=net_pnl,
            account_balance=resulting_balance,
            trade_duration=exit_time - position.entry_time,
            exit_reason=exit_reason,
            fees=total_fees,
        )

    def _risk_prices(self, entry_price: float, side: PositionSide, atr: float | None = None) -> tuple[float, float]:
        if self.risk_config.exit_mode == "atr":
            return self._atr_risk_prices(entry_price, side, atr)
        if self.risk_config.exit_mode != "fixed":
            raise ValueError(f"Unsupported exit mode: {self.risk_config.exit_mode}")
        return self._fixed_risk_prices(entry_price, side)

    def _fixed_risk_prices(self, entry_price: float, side: PositionSide) -> tuple[float, float]:
        if side == PositionSide.LONG:
            return (
                entry_price * (1 - self.risk_config.stop_loss_pct),
                entry_price * (1 + self.risk_config.take_profit_pct),
            )
        return (
            entry_price * (1 + self.risk_config.stop_loss_pct),
            entry_price * (1 - self.risk_config.take_profit_pct),
        )

    def _atr_risk_prices(self, entry_price: float, side: PositionSide, atr: float | None) -> tuple[float, float]:
        if atr is None or pd.isna(atr) or atr <= 0:
            raise ValueError("ATR exit mode requires a positive ATR value at entry.")

        stop_distance = atr * self.risk_config.atr_stop_loss_multiplier
        take_profit_distance = atr * self.risk_config.atr_take_profit_multiplier
        if side == PositionSide.LONG:
            return entry_price - stop_distance, entry_price + take_profit_distance
        return entry_price + stop_distance, entry_price - take_profit_distance

    def _activate_break_even_if_triggered(self, position: Position, candle: pd.Series) -> None:
        if not self.risk_config.break_even_enabled or position.break_even_activated:
            return
        if position.entry_atr is None or pd.isna(position.entry_atr) or position.entry_atr <= 0:
            return

        trigger_distance = position.entry_atr * self.risk_config.break_even_trigger_atr_multiplier
        if position.side == PositionSide.LONG and candle["high"] >= position.entry_price + trigger_distance:
            position.stop_loss = position.entry_price
            position.break_even_activated = True
        elif position.side == PositionSide.SHORT and candle["low"] <= position.entry_price - trigger_distance:
            position.stop_loss = position.entry_price
            position.break_even_activated = True

    def _apply_entry_slippage(self, price: float, side: PositionSide) -> float:
        multiplier = 1 + self.cost_config.slippage_pct if side == PositionSide.LONG else 1 - self.cost_config.slippage_pct
        return price * multiplier

    def _apply_exit_slippage(self, price: float, side: PositionSide) -> float:
        multiplier = 1 - self.cost_config.slippage_pct if side == PositionSide.LONG else 1 + self.cost_config.slippage_pct
        return price * multiplier

    def _fee(self, price: float, quantity: float) -> float:
        return price * quantity * self.cost_config.fee_rate

    @staticmethod
    def _gross_pnl(position: Position, exit_price: float) -> float:
        if position.side == PositionSide.LONG:
            return (exit_price - position.entry_price) * position.quantity
        return (position.entry_price - exit_price) * position.quantity
