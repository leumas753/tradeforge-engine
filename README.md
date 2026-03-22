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
  └── fetch active bot_instances (status = "running")
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

## Notes

- Market data is fully simulated (random walk). Replace `market_data.py` with a real API call when ready.
- Paper trades are written directly to the `trades` table so the React frontend displays them immediately.
- Logs appear in `activity_logs` and are visible on the Logs & Alerts page in the UI.
