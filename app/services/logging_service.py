from datetime import datetime, timezone
from app.db import supabase_client as db


def log(
    user_id: str,
    level: str,
    message: str,
    bot_instance_id: str | None = None,
    metadata: dict | None = None,
) -> None:
    """
    Write a single entry to the activity_logs table.

    level: "info" | "warning" | "error"
    """
    entry = {
        "user_id": user_id,
        "level": level,
        "message": message,
        "bot_instance_id": bot_instance_id,
        "metadata": metadata or {},
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    try:
        db.insert_log(entry)
    except Exception as exc:
        # Never let logging failures crash the worker
        print(f"[logging_service] failed to write log: {exc}")


def info(user_id: str, message: str, **kwargs) -> None:
    log(user_id, "info", message, **kwargs)


def warning(user_id: str, message: str, **kwargs) -> None:
    log(user_id, "warning", message, **kwargs)


def error(user_id: str, message: str, **kwargs) -> None:
    log(user_id, "error", message, **kwargs)
