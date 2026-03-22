import random
from datetime import datetime, timezone
from app.models.schemas import Signal, TradeRecord
from app.db import supabase_client as db


def execute_paper_trade(
    signal: Signal,
    user_id: str,
    bot_instance_id: str,
) -> dict:
    """
    Simulate a paper trade:
      - Open the trade at the signal price
      - Immediately simulate a close with a small random PnL
      - Persist both states in Supabase and return the final trade record
    """
    now = datetime.now(timezone.utc).isoformat()

    # Simulate a realistic exit: price moves ±0.5% to ±2% randomly (win or lose)
    move = random.uniform(-0.02, 0.02)
    exit_price = round(signal.price * (1 + move), 4)

    if signal.action == "buy":
        pnl = round((exit_price - signal.price) * signal.quantity, 4)
    else:
        pnl = round((signal.price - exit_price) * signal.quantity, 4)

    trade_payload = {
        "user_id": user_id,
        "bot_instance_id": bot_instance_id,
        "symbol": signal.symbol,
        "side": signal.action,
        "entry_price": signal.price,
        "exit_price": exit_price,
        "quantity": signal.quantity,
        "pnl": pnl,
        "status": "closed",
        "opened_at": now,
        "closed_at": now,
    }

    created = db.insert_trade(trade_payload)
    return created
