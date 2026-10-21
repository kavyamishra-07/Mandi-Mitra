# Mandi Mitra: a voice advisor that tells farmers when to sell

**Track:** Alexa+ (self-hosted MCP server, simulated-experience path) · **License:** MIT

Small farmers often sell the day they reach the mandi, even when prices are about to rise, or hold perishable
produce too long and lose it. Mandi Mitra is an **MCP server** (Streamable HTTP) that Alexa+ can call to answer
"should I sell my onions now?" in English or Hindi, using an ML price forecast, the crop's shelf life and the rain outlook.

## What is inside

| Part | File | What it does |
|---|---|---|
| MCP server | `mandi_mitra/server.py` | 5 tools at `/mcp`: `list_crops`, `get_price_trend`, `forecast_price`, `get_weather`, `sell_or_wait_advice` |
| ML model | `mandi_mitra/model.py` | Gradient boosting on lag and seasonal features, recursive 14-day forecast, honest 7-day hold-out error |
| Data | `mandi_mitra/data.py` | Loads `data/prices.csv`; generates a **synthetic** sample dataset if none exists |
| Alexa+ simulator | `mandi_mitra/static/index.html` | Voice-first web app (speech in and out, English/Hindi). It calls the MCP server over real MCP, and shows every tool call |
| Test | `tests/smoke_test.py` | Connects as an MCP client and checks every tool |

The advice logic: forecast the next 14 days, look only inside the crop's storage window (tomato 4 days, onion 45, wheat 180),
recommend **wait** if the best day beats today by 3% or more, otherwise **sell now**; and force **sell now** for perishable crops if heavy rain is coming.

## Run it (Python 3.10+)

Easiest: on Windows double-click `run.bat`; on Mac/Linux run `./run.sh`. Manual steps:

```bash
python -m venv venv && source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt
python -m mandi_mitra.server
```

Open http://localhost:8000 (use Chrome or Edge for the microphone). The MCP endpoint is http://localhost:8000/mcp.
Check it with `python tests/smoke_test.py`, or the MCP Inspector: `npx @modelcontextprotocol/inspector`.

Connect to Alexa+: expose the server over HTTPS (for example `ngrok http 8000`) and register `https://<your-host>/mcp`
as an MCP server in your Alexa+ developer setup.

## Data note (please read)

The bundled prices are **synthetic sample data** with realistic seasonality, so the demo runs offline. To use real prices,
put a CSV with columns `date,crop,modal_price` (Rs per quintal, for example an Agmarknet export) in `data/prices.csv`
and delete nothing else; the model retrains on start. Forecasts are guidance, not financial advice.

## Ideas for next steps

Per-mandi prices, more crops and languages, SMS/WhatsApp alerts, Amazon Bedrock for free-form questions.
