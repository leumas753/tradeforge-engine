from datetime import datetime, timezone
from supabase import create_client, Client
from app.config import settings

# Lazily initialized — created on first use, not at import time.
# This ensures a missing env var does not crash the app before /health is registered.
_client: Client | None = None


def _get_client() -> Client:
    global _client
    if _client is None:
        _client = create_client(
            settings.supabase_url,
            settings.supabase_service_role_key,
        )
    return _client


def fetch_active_bots() -> list[dict]:
    """Fetch all bot_instances with status 'active', including their strategy."""
    res = (
        _get_client()
        .from_("bot_instances")
        .select("*, strategies(*)")
        .eq("status", "active")
        .execute()
    )
    return res.data


def fetch_risk_rules(user_id: str) -> dict | None:
    """Fetch the first risk_rules row for a user, or None if not configured."""
    res = (
        _get_client()
        .from_("risk_rules")
        .select("*")
        .eq("user_id", user_id)
        .order("created_at", desc=False)
        .limit(1)
        .execute()
    )
    return res.data[0] if res.data else None


def fetch_open_trades(user_id: str) -> list[dict]:
    """Fetch all currently open trades for a user."""
    res = (
        _get_client()
        .from_("trades")
        .select("*")
        .eq("user_id", user_id)
        .eq("status", "open")
        .execute()
    )
    return res.data


def fetch_daily_pnl(user_id: str) -> float:
    """Sum of pnl for all trades closed today (UTC)."""
    today = datetime.now(timezone.utc).date().isoformat()
    res = (
        _get_client()
        .from_("trades")
        .select("pnl")
        .eq("user_id", user_id)
        .eq("status", "closed")
        .gte("closed_at", today)
        .execute()
    )
    return sum(row["pnl"] for row in res.data if row["pnl"] is not None)


def insert_trade(trade: dict) -> dict:
    """Insert a new trade row and return the created record."""
    res = _get_client().from_("trades").insert(trade).execute()
    return res.data[0]


def insert_log(log: dict) -> None:
    """Append a row to activity_logs. Fire-and-forget."""
    _get_client().from_("activity_logs").insert(log).execute()
