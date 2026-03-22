from abc import ABC, abstractmethod
from app.models.schemas import MarketData, Signal


class BaseStrategy(ABC):
    """
    All trading strategies must inherit from this class and implement `generate_signal`.
    """

    def __init__(self, config: dict):
        self.config = config

    @abstractmethod
    def generate_signal(self, market_data: MarketData) -> Signal:
        """
        Analyse market_data and return a Signal with action buy/sell/hold.
        """
        ...

    @property
    def name(self) -> str:
        return self.__class__.__name__
