from __future__ import annotations

from dataclasses import dataclass

from crypto_futures_bot.strategy.signals import SignalType


@dataclass(frozen=True)
class Order:
    direction: SignalType
    quantity: float
    price: float

