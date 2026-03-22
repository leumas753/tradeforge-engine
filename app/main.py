from fastapi import FastAPI, Header, HTTPException, status
from app.workers.bot_worker import run_all_bots
from app.models.schemas import BotRunResult
from app.config import settings

print("[startup] TradeForge Engine starting...")

app = FastAPI(
    title="TradeForge Engine",
    description="Paper trading backend for the TradeForge system.",
    version="0.1.0",
)


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "engine": "tradeforge-engine", "version": "0.1.0"}


@app.post("/run-bots", response_model=list[BotRunResult])
def run_bots(authorization: str | None = Header(default=None)) -> list[BotRunResult]:
    """
    Trigger a single worker cycle.
    If CRON_SECRET is configured, requires: Authorization: Bearer <secret>
    """
    if settings.cron_secret:
        if authorization != f"Bearer {settings.cron_secret}":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or missing Authorization header",
            )
    return run_all_bots()
