from datetime import datetime, timezone
from supabase import create_client, Client
from app.config import settings

# Single shared client using the service_role key (backend only)
supabase: Client = create_client(
    settings.supabase_url,
    settings.supabase_service_role_key,
)


def fetch_active_bots() -> list[dict]:
    """Fetch all bot_instances with status 'running', including their strategy."""
    res = (
        supabase
        .from_("bot_instances")
        .select("*, strategies(*)")
        .eq("status", "running")
        .execute()
    )
    return res.data


def fetch_risk_rules(user_id: str) -> dict | None:
    """Fetch the first risk_rules row for a user, or None if not configured."""
    res = (
        supabase
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
        supabase
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
        supabase
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
    res = supabase.from_("trades").insert(trade).execute()
    return res.data[0]


def update_trade(trade_id: str, updates: dict) -> dict:
    """Update an existing trade row."""
    res = supabase.from_("trades").update(updates).eq("id", trade_id).execute()
    return res.data[0]


def insert_log(log: dict) -> None:
    """Append a row to activity_logs. Fire-and-forget."""
    supabase.from_("activity_logs").insert(log).execute()
