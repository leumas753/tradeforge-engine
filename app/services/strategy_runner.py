from app.strategies.base_strategy import BaseStrategy
from app.strategies.ema_crossover import EMACrossoverStrategy
from app.models.schemas import MarketData, Signal

# Registry: map strategy type strings to their classes
_STRATEGY_REGISTRY: dict[str, type[BaseStrategy]] = {
    "ema-crossover": EMACrossoverStrategy,
    "mean-reversion": EMACrossoverStrategy,   # placeholder until implemented
    "momentum":       EMACrossoverStrategy,   # placeholder until implemented
    "grid":           EMACrossoverStrategy,   # placeholder until implemented
    "dca":            EMACrossoverStrategy,   # placeholder until implemented
}


def load_strategy(strategy_row: dict) -> BaseStrategy:
    """
    Instantiate the correct strategy class from a strategies DB row.
    Falls back to EMACrossoverStrategy if the type is unknown.
    """
    config: dict = strategy_row.get("config") or {}
    strategy_type: str = config.get("type", "ema-crossover").lower()
    cls = _STRATEGY_REGISTRY.get(strategy_type, EMACrossoverStrategy)
    return cls(config)


def run_strategy(strategy: BaseStrategy, market_data: MarketData) -> Signal:
    """Execute the strategy and return its signal."""
    return strategy.generate_signal(market_data)
