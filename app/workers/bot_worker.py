from app.db import supabase_client as db
from app.services import market_data as md_service
from app.services import strategy_runner
from app.services import risk_manager
from app.services import execution
from app.services import logging_service as logger
from app.models.schemas import BotRunResult


def run_all_bots() -> list[BotRunResult]:
    """
    Main worker entry point.

    Flow for each active bot:
      1. Fetch all running bot_instances (with strategy joined)
      2. Load the strategy
      3. Get mock market data for the strategy's market
      4. Generate a signal
      5. Check risk rules
      6. Execute paper trade if allowed
      7. Log every step
    """
    results: list[BotRunResult] = []

    bots = db.fetch_active_bots()
    print(f"[worker] found {len(bots)} active bot(s)")

    for bot in bots:
        bot_id: str = bot["id"]
        user_id: str = bot["user_id"]
        strategy_row: dict | None = bot.get("strategies")

        logger.info(user_id, "bot cycle started", bot_instance_id=bot_id)

        # ── Guard: no strategy attached ───────────────────────────────────
        if not strategy_row:
            logger.warning(
                user_id,
                "bot has no strategy attached, skipping",
                bot_instance_id=bot_id,
            )
            results.append(BotRunResult(
                bot_id=bot_id,
                status="error",
                message="no strategy attached",
            ))
            continue

        symbol: str = strategy_row.get("market", "BTC/USDT")

        try:
            # ── Step 1: Load strategy ──────────────────────────────────────
            strategy = strategy_runner.load_strategy(strategy_row)

            # ── Step 2: Get market data ────────────────────────────────────
            market_data = md_service.get_market_data(symbol)

            # ── Step 3: Generate signal ────────────────────────────────────
            signal = strategy_runner.run_strategy(strategy, market_data)
            logger.info(
                user_id,
                f"signal generated: {signal.action.upper()} {symbol} @ {signal.price}",
                bot_instance_id=bot_id,
                metadata={"reason": signal.reason, "action": signal.action},
            )

            if signal.action == "hold":
                results.append(BotRunResult(
                    bot_id=bot_id,
                    status="held",
                    message=signal.reason,
                ))
                continue

            # ── Step 4: Check risk rules ───────────────────────────────────
            risk_rules = db.fetch_risk_rules(user_id)
            open_trades = db.fetch_open_trades(user_id)
            daily_pnl = db.fetch_daily_pnl(user_id)

            risk_result = risk_manager.check_risk(signal, risk_rules, open_trades, daily_pnl)

            if not risk_result.allowed:
                logger.warning(
                    user_id,
                    f"trade blocked by risk manager: {risk_result.reason}",
                    bot_instance_id=bot_id,
                    metadata={"reason": risk_result.reason},
                )
                results.append(BotRunResult(
                    bot_id=bot_id,
                    status="blocked",
                    message=risk_result.reason,
                ))
                continue

            # ── Step 5: Execute paper trade ────────────────────────────────
            trade = execution.execute_paper_trade(signal, user_id, bot_id)
            logger.info(
                user_id,
                f"paper trade executed: {signal.action.upper()} {symbol} "
                f"entry={trade['entry_price']} exit={trade['exit_price']} pnl={trade['pnl']}",
                bot_instance_id=bot_id,
                metadata={
                    "trade_id": trade["id"],
                    "side": signal.action,
                    "pnl": trade["pnl"],
                },
            )

            results.append(BotRunResult(
                bot_id=bot_id,
                status="traded",
                message=f"{signal.action} {symbol} @ {trade['entry_price']} | pnl={trade['pnl']}",
                trade_id=trade["id"],
            ))

        except Exception as exc:
            logger.error(
                user_id,
                f"unhandled error in bot cycle: {exc}",
                bot_instance_id=bot_id,
                metadata={"error": str(exc)},
            )
            results.append(BotRunResult(
                bot_id=bot_id,
                status="error",
                message=str(exc),
            ))

    return results
