from __future__ import annotations

from abc import ABC, abstractmethod


class BaseExchange(ABC):
    """Placeholder interface for future exchange adapters."""

    @abstractmethod
    def connect(self) -> None:
        raise NotImplementedError

