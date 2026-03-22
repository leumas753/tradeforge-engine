from app.models.schemas import Signal, RiskCheckResult


def check_risk(
    signal: Signal,
    risk_rules: dict | None,
    open_trades: list[dict],
    daily_pnl: float,
) -> RiskCheckResult:
    """
    Validate a signal against the user's risk rules.
    Returns RiskCheckResult(allowed=False, reason=...) if any rule is violated.
    """
    if signal.action == "hold":
        return RiskCheckResult(allowed=False, reason="signal is hold")

    # No risk rules configured → allow all trades
    if not risk_rules:
        return RiskCheckResult(allowed=True, reason="no risk rules configured")

    # Kill switch — hard stop on all trading
    if risk_rules.get("kill_switch"):
        return RiskCheckResult(allowed=False, reason="kill switch is active")

    # Max open positions
    max_open: int | None = risk_rules.get("max_open_positions")
    if max_open is not None and len(open_trades) >= max_open:
        return RiskCheckResult(
            allowed=False,
            reason=f"max open positions reached ({len(open_trades)}/{max_open})",
        )

    # Max daily loss — daily_pnl is negative when losing
    max_daily_loss: float | None = risk_rules.get("max_daily_loss")
    if max_daily_loss is not None and daily_pnl <= -abs(max_daily_loss):
        return RiskCheckResult(
            allowed=False,
            reason=f"daily loss limit reached (${daily_pnl:.2f} / -${abs(max_daily_loss):.2f})",
        )

    # Max risk per trade — compared against notional value of the signal
    max_risk: float | None = risk_rules.get("max_risk_per_trade")
    if max_risk is not None:
        notional = signal.price * signal.quantity
        if notional > max_risk:
            return RiskCheckResult(
                allowed=False,
                reason=f"trade notional ${notional:.2f} exceeds max risk per trade ${max_risk:.2f}",
            )

    return RiskCheckResult(allowed=True)
