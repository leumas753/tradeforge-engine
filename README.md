# tradeforge-engine

Python backend for the TradeForge trading bot system.
Reads strategies and bot instances from Supabase, runs trading logic, applies risk rules, simulates paper trades, and writes results back to Supabase.

> **Paper trading only.** No real broker connections. No live orders.

---

## Stack

- Python 3.11+
- FastAPI
- Supabase Python client (service_role)
- Pydantic v2
- python-dotenv

---

## Setup

### 1. Clone and create a virtual environment

```bash
cd tradeforge-engine
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure environment variables

```bash
cp .env.example .env
```

Edit `.env`:

```
SUPABASE_URL=https://slpqdhszbbkzszxmtdtw.supabase.co
SUPABASE_SERVICE_ROLE_KEY=<your service_role key>
```

> Use the **service_role** key here — never the anon key. This key bypasses RLS and is only safe on the backend.

### 3. Run the server

```bash
uvicorn app.main:app --reload
```

Server starts at `http://localhost:8000`

---

## API

| Method | Endpoint    | Description                              |
|--------|-------------|------------------------------------------|
| GET    | `/health`   | Returns engine status                    |
| POST   | `/run-bots` | Triggers one full worker cycle manually  |

### Example

```bash
# Check health
curl http://localhost:8000/health

# Run all active bots
curl -X POST http://localhost:8000/run-bots
```

---

## Project Structure

```
app/
├── main.py                  FastAPI app — /health and /run-bots
├── config.py                Loads env vars via pydantic-settings
├── db/
│   └── supabase_client.py   All Supabase read/write functions
├── models/
│   └── schemas.py           Pydantic models (MarketData, Signal, etc.)
├── services/
│   ├── market_data.py       Mock market data generator
│   ├── strategy_runner.py   Loads and runs strategy classes
│   ├── risk_manager.py      Validates signals against risk rules
│   ├── execution.py         Paper trade execution + Supabase write
│   └── logging_service.py   Writes to activity_logs table
├── strategies/
│   ├── base_strategy.py     Abstract base class for all strategies
│   └── ema_crossover.py     EMA Crossover strategy (short 20 / long 50)
└── workers/
    └── bot_worker.py        Main loop — orchestrates everything
```

---

## How It Works

### Worker cycle (`POST /run-bots`)

```
Supabase
  └── fetch active bot_instances (status = "active")
        └── for each bot:
              1. load strategy from DB config
              2. get mock market data for the symbol
              3. run strategy → signal (buy / sell / hold)
              4. fetch risk rules for user
              5. check risk rules → allowed or blocked
              6. if allowed → execute paper trade → write to trades table
              7. log every step → write to activity_logs table
```

### Strategy execution

Each strategy inherits from `BaseStrategy` and implements `generate_signal(market_data) → Signal`.

The `strategy_runner` maps the `config.type` field from the DB to the correct class:

```python
"ema-crossover" → EMACrossoverStrategy
```

**EMA Crossover logic:**
- Computes EMA-20 and EMA-50 over the last 60 mock candles
- BUY if EMA-20 crosses above EMA-50 (golden cross)
- SELL if EMA-20 crosses below EMA-50 (death cross)
- HOLD otherwise

### Data flow

```
Supabase DB
  ↓  fetch bot_instances + strategies + risk_rules
Engine (bot_worker)
  ↓  market_data → strategy → signal → risk check → execution
Supabase DB
  ↑  insert trades + activity_logs
```

---

## Adding a New Strategy

1. Create `app/strategies/my_strategy.py` inheriting `BaseStrategy`
2. Implement `generate_signal(market_data) -> Signal`
3. Register it in `app/services/strategy_runner.py`:

```python
_STRATEGY_REGISTRY["my-strategy"] = MyStrategy
```

4. Set `config.type = "my-strategy"` on a strategy row in Supabase

---

## Deployment (Railway)

### Environment variables

Set these in the Railway service **Variables** tab:

| Variable | Required | Description |
|---|---|---|
| `SUPABASE_URL` | Yes | Your Supabase project URL |
| `SUPABASE_SERVICE_ROLE_KEY` | Yes | Service role key (bypasses RLS) |
| `CRON_SECRET` | Recommended | Random secret to protect `/run-bots` |

Generate a `CRON_SECRET`:
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

### Start command

Railway picks this up automatically from `Procfile` and `railway.json`:
```
uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

### Scheduled bot execution (Railway Cron)

Railway can trigger `/run-bots` on a schedule using a separate Cron service.

**Recommended frequency:** every 15 minutes (`*/15 * * * *`).
- Runs 96 times per day — enough signal for a paper trading demo
- Avoids hammering Supabase with too many reads/writes
- If no crossover fires on a given cycle, the bot simply holds with no DB writes

**Setup steps:**

1. In your Railway project, click **+ New** → **Empty Service**
2. Go to **Settings** → **Service Type** → select **Cron Job**
3. Set the **Schedule** to `*/15 * * * *`
4. Set the **Command** to:
   ```
   curl -s -X POST https://<your-railway-domain>/run-bots \
     -H "Authorization: Bearer $CRON_SECRET"
   ```
   Replace `<your-railway-domain>` with the public URL of your web service (e.g. `tradeforge-engine-production.up.railway.app`)
5. In the Cron service **Variables** tab, add:
   - `CRON_SECRET` — same value as in the web service

That's it. The cron service calls `/run-bots` every 15 minutes; the web service validates the secret and runs the bot cycle.

### Protecting `/run-bots`

If `CRON_SECRET` is set, `/run-bots` requires:
```
Authorization: Bearer <your-secret>
```

If `CRON_SECRET` is not set, the endpoint is open (fine for local development).

`GET /health` is always public and requires no authentication.

---

## Notes

- Market data is fully simulated (random walk). Replace `market_data.py` with a real API call when ready.
- Paper trades are written directly to the `trades` table so the React frontend displays them immediately.
- Logs appear in `activity_logs` and are visible on the Logs & Alerts page in the UI.
