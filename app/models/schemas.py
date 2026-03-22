from pydantic import BaseModel, Field
from typing import Any
from datetime import datetime


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


class Signal(BaseModel):
    action: str         # "buy" | "sell" | "hold"
    symbol: str
    price: float
    quantity: float = 1.0
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
    opened_at: datetime = Field(default_factory=datetime.utcnow)


class BotRunResult(BaseModel):
    bot_id: str
    status: str         # "traded" | "held" | "blocked" | "error"
    message: str
    trade_id: str | None = None
