from app.strategies.base_strategy import BaseStrategy
from app.models.schemas import MarketData, Signal, _DEFAULT_QUANTITY


def _ema(prices: list[float], period: int) -> list[float]:
    """Calculate Exponential Moving Average for a list of close prices."""
    k = 2.0 / (period + 1)
    ema_values: list[float] = []
    for i, price in enumerate(prices):
        if i == 0:
            ema_values.append(price)
        else:
            ema_values.append(price * k + ema_values[-1] * (1 - k))
    return ema_values


class EMACrossoverStrategy(BaseStrategy):
    """
    EMA Crossover:
      - BUY  when the short EMA crosses above the long EMA (golden cross)
      - SELL when the short EMA crosses below the long EMA (death cross)
      - HOLD otherwise
    """

    def __init__(self, config: dict):
        super().__init__(config)
        self.short_period: int = int(config.get("ema_short", 20))
        self.long_period: int = int(config.get("ema_long", 50))

    def generate_signal(self, market_data: MarketData) -> Signal:
        closes = [c.close for c in market_data.candles]

        if len(closes) < self.long_period + 1:
            return Signal(
                action="hold",
                symbol=market_data.symbol,
                price=market_data.price,
                reason="not enough candles for EMA calculation",
            )

        short_ema = _ema(closes, self.short_period)
        long_ema = _ema(closes, self.long_period)

        # Compare the last two values to detect a crossover
        prev_short, curr_short = short_ema[-2], short_ema[-1]
        prev_long,  curr_long  = long_ema[-2],  long_ema[-1]

        qty = float(self.config.get("quantity") or _DEFAULT_QUANTITY.get(market_data.symbol, 0.01))

        if prev_short <= prev_long and curr_short > curr_long:
            return Signal(
                action="buy",
                symbol=market_data.symbol,
                price=market_data.price,
                quantity=qty,
                reason=f"EMA{self.short_period} crossed above EMA{self.long_period}",
            )

        if prev_short >= prev_long and curr_short < curr_long:
            return Signal(
                action="sell",
                symbol=market_data.symbol,
                price=market_data.price,
                quantity=qty,
                reason=f"EMA{self.short_period} crossed below EMA{self.long_period}",
            )

        return Signal(
            action="hold",
            symbol=market_data.symbol,
            price=market_data.price,
            reason="no crossover detected",
        )
