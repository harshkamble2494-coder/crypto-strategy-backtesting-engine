from __future__ import annotations

from abc import ABC, abstractmethod

import pandas as pd

from crypto_futures_bot.strategy.signals import SignalType


class Strategy(ABC):
    @abstractmethod
    def generate_signal(self, previous: pd.Series, current: pd.Series) -> SignalType:
        """Return the signal confirmed by the current closed candle."""

