from fastapi import FastAPI
from app.workers.bot_worker import run_all_bots
from app.models.schemas import BotRunResult

app = FastAPI(
    title="TradeForge Engine",
    description="Paper trading backend for the TradeForge system.",
    version="0.1.0",
)


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "engine": "tradeforge-engine", "version": "0.1.0"}


@app.post("/run-bots", response_model=list[BotRunResult])
def run_bots() -> list[BotRunResult]:
    """
    Manually trigger a single worker cycle.
    Fetches all active bots, runs strategies, applies risk checks,
    executes paper trades, and logs everything to Supabase.
    """
    return run_all_bots()
