from pydantic import BaseModel, Field
from typing import Any
from datetime import datetime, timezone


class Candle(BaseModel):
    open: float
    high: float
    low: float
    close: float
    volume: float


class MarketData(BaseModel):
    symbol: str
    price: float
    trend: str          # "up" | "down" | "neutral"
    candles: list[Candle]


_DEFAULT_QUANTITY: dict[str, float] = {
    "BTC/USDT": 0.001,   # ~$87 notional at $87k
    "ETH/USDT": 0.02,    # ~$76 notional at $3800
    "SOL/USDT": 0.5,     # ~$93 notional at $185
    "AVAX/USDT": 2.0,    # ~$84 notional at $42
}


class Signal(BaseModel):
    action: str         # "buy" | "sell" | "hold"
    symbol: str
    price: float
    quantity: float = 0.01
    reason: str = ""


class RiskCheckResult(BaseModel):
    allowed: bool
    reason: str = ""


class TradeRecord(BaseModel):
    user_id: str
    bot_instance_id: str
    symbol: str
    side: str
    entry_price: float
    quantity: float
    pnl: float | None = None
    status: str = "open"
    opened_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class BotRunResult(BaseModel):
    bot_id: str
    status: str         # "traded" | "held" | "blocked" | "error"
    message: str
    trade_id: str | None = None
