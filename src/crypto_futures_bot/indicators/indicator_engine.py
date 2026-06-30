from __future__ import annotations

import pandas as pd

from crypto_futures_bot.config.models import StrategyConfig


class IndicatorEngine:
    def __init__(self, config: StrategyConfig) -> None:
        self.config = config

    def add_indicators(self, candles: pd.DataFrame) -> pd.DataFrame:
        df = candles.copy()
        df["ema_fast"] = self._ema(df["close"], self.config.ema_fast)
        df["ema_slow"] = self._ema(df["close"], self.config.ema_slow)
        df["ema_trend"] = self._ema(df["close"], self.config.ema_trend)
        df["rsi"] = self._rsi(df["close"], self.config.rsi_length)
        df["atr"] = self._atr(df, self.config.atr_length)
        df["adx"] = self._adx(df, self.config.adx_length)
        df["ema_trend_slope"] = df["ema_trend"] - df["ema_trend"].shift(self.config.trend_slope_lookback)
        df["volume_sma"] = df["volume"].rolling(self.config.volume_sma_length, min_periods=self.config.volume_sma_length).mean()
        df["volume_ratio"] = df["volume"] / df["volume_sma"]
        return df

    @staticmethod
    def _ema(series: pd.Series, length: int) -> pd.Series:
        return series.ewm(span=length, adjust=False, min_periods=length).mean()

    @staticmethod
    def _rsi(series: pd.Series, length: int) -> pd.Series:
        delta = series.diff()
        gain = delta.clip(lower=0)
        loss = -delta.clip(upper=0)
        avg_gain = gain.ewm(alpha=1 / length, adjust=False, min_periods=length).mean()
        avg_loss = loss.ewm(alpha=1 / length, adjust=False, min_periods=length).mean()
        rs = avg_gain / avg_loss.replace(0, pd.NA)
        rsi = 100 - (100 / (1 + rs))
        return rsi.fillna(50.0)

    @staticmethod
    def _atr(df: pd.DataFrame, length: int) -> pd.Series:
        high_low = df["high"] - df["low"]
        high_close = (df["high"] - df["close"].shift()).abs()
        low_close = (df["low"] - df["close"].shift()).abs()
        true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        return true_range.ewm(alpha=1 / length, adjust=False, min_periods=length).mean()

    @staticmethod
    def _adx(df: pd.DataFrame, length: int) -> pd.Series:
        up_move = df["high"].diff()
        down_move = -df["low"].diff()
        plus_dm = up_move.where((up_move > down_move) & (up_move > 0), 0.0)
        minus_dm = down_move.where((down_move > up_move) & (down_move > 0), 0.0)
        atr = IndicatorEngine._atr(df, length)
        plus_di = 100 * plus_dm.ewm(alpha=1 / length, adjust=False, min_periods=length).mean() / atr
        minus_di = 100 * minus_dm.ewm(alpha=1 / length, adjust=False, min_periods=length).mean() / atr
        dx = ((plus_di - minus_di).abs() / (plus_di + minus_di).replace(0, pd.NA)) * 100
        return dx.ewm(alpha=1 / length, adjust=False, min_periods=length).mean()
