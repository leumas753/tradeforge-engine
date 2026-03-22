import random
from app.models.schemas import MarketData, Candle

# Simulated base prices per symbol so data is somewhat consistent per run
_BASE_PRICES: dict[str, float] = {
    "BTC/USDT": 87_000.0,
    "ETH/USDT": 3_800.0,
    "SOL/USDT": 185.0,
    "AVAX/USDT": 42.0,
}
_DEFAULT_PRICE = 100.0


def _generate_candles(base_price: float, count: int = 60) -> list[Candle]:
    """Generate a random-walk OHLCV candle series for strategy computation."""
    candles: list[Candle] = []
    price = base_price
    for _ in range(count):
        change = random.uniform(-0.015, 0.015)
        open_ = price
        close = round(open_ * (1 + change), 4)
        high = round(max(open_, close) * random.uniform(1.0, 1.008), 4)
        low = round(min(open_, close) * random.uniform(0.992, 1.0), 4)
        volume = round(random.uniform(100, 5000), 2)
        candles.append(Candle(open=open_, high=high, low=low, close=close, volume=volume))
        price = close
    return candles


def get_market_data(symbol: str) -> MarketData:
    """
    Return simulated market data for a given symbol.
    No real API calls — mock only.
    """
    base = _BASE_PRICES.get(symbol, _DEFAULT_PRICE)
    candles = _generate_candles(base)
    current_price = candles[-1].close

    # Derive a simple trend from the last 10 candles
    recent = candles[-10:]
    first_close = recent[0].close
    last_close = recent[-1].close
    if last_close > first_close * 1.003:
        trend = "up"
    elif last_close < first_close * 0.997:
        trend = "down"
    else:
        trend = "neutral"

    return MarketData(
        symbol=symbol,
        price=current_price,
        trend=trend,
        candles=candles,
    )
