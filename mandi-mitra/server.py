"""Mandi Mitra - an Alexa+ style MCP server that helps farmers decide when to sell.

One process serves:
  /mcp        MCP server (Streamable HTTP, tools below) - connect Alexa+ or any MCP client
  /           simulated Alexa+ voice experience (web app)
  /api/chat   simulator backend; it talks to the MCP server over real MCP calls
"""
import json, os, re
from pathlib import Path
import httpx
from mcp.server.fastmcp import FastMCP
from mcp.server.transport_security import TransportSecuritySettings
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client
from starlette.requests import Request
from starlette.responses import HTMLResponse, JSONResponse

from .data import CROPS, load_prices, series
from .model import advise, forecast

PORT = int(os.environ.get("PORT", "8000"))
STATIC = Path(__file__).parent / "static"

mcp = FastMCP("mandi-mitra", host="0.0.0.0", port=PORT, stateless_http=True, json_response=True,
              transport_security=TransportSecuritySettings(enable_dns_rebinding_protection=False))

CITIES = {"kanpur": (26.45, 80.33), "lucknow": (26.85, 80.95), "ludhiana": (30.90, 75.85),
          "indore": (22.72, 75.86), "pune": (18.52, 73.86), "nashik": (20.00, 73.79), "delhi": (28.61, 77.21)}


@mcp.tool()
def list_crops() -> dict:
    """List the crops this server can give prices and advice for."""
    return {"crops": {c: {"shelf_life_days": v["shelf"]} for c, v in CROPS.items()}}


@mcp.tool()
def get_price_trend(crop: str, days: int = 30) -> dict:
    """Recent mandi price trend (Rs per quintal) for a crop over the last N days."""
    crop = crop.lower()
    if crop not in CROPS:
        return {"error": f"unknown crop '{crop}'", "supported": list(CROPS)}
    s = series(load_prices(), crop).tail(max(7, min(days, 120)))
    change = (s.iloc[-1] / s.iloc[0] - 1) * 100
    return {"crop": crop, "today": round(float(s.iloc[-1])), "change_pct": round(float(change), 1),
            "days": len(s), "history": [{"date": d.strftime("%Y-%m-%d"), "price": round(float(p))} for d, p in s.items()]}


@mcp.tool()
def forecast_price(crop: str) -> dict:
    """ML forecast of the next 14 days of mandi prices, with the model's held-out error."""
    crop = crop.lower()
    return forecast(crop) if crop in CROPS else {"error": f"unknown crop '{crop}'", "supported": list(CROPS)}


@mcp.tool()
async def get_weather(city: str) -> dict:
    """3-day rain outlook for a city (Open-Meteo, no API key). Falls back gracefully if offline."""
    key = city.lower()
    if key not in CITIES:
        return {"error": f"unknown city '{city}'", "supported": list(CITIES)}
    lat, lon = CITIES[key]
    try:
        async with httpx.AsyncClient(timeout=6) as c:
            r = await c.get("https://api.open-meteo.com/v1/forecast", params={
                "latitude": lat, "longitude": lon, "daily": "precipitation_sum,temperature_2m_max", "forecast_days": 3})
            d = r.json()["daily"]
        rain = [round(x, 1) for x in d["precipitation_sum"]]
        return {"city": city, "rain_mm": rain, "max_temp_c": d["temperature_2m_max"], "rain_expected": max(rain) >= 10, "source": "open-meteo"}
    except Exception:
        return {"city": city, "rain_expected": False, "source": "unavailable"}


@mcp.tool()
def sell_or_wait_advice(crop: str, rain_expected: bool = False) -> dict:
    """Recommend selling now or waiting, using the price forecast, the crop's shelf life and rain risk."""
    crop = crop.lower()
    return advise(crop, rain_expected) if crop in CROPS else {"error": f"unknown crop '{crop}'", "supported": list(CROPS)}


# ---------------------------------------------------------------- simulator ----
KEYWORDS = {
    "wheat": ["wheat", "gehu", "gehun", "गेहूं", "गेहूँ"], "rice": ["rice", "paddy", "chawal", "dhan", "चावल", "धान"],
    "tomato": ["tomato", "tamatar", "टमाटर"], "potato": ["potato", "aloo", "alu", "आलू"], "onion": ["onion", "pyaz", "pyaaz", "प्याज"],
}
NAMES_HI = {"wheat": "गेहूं", "rice": "धान", "tomato": "टमाटर", "potato": "आलू", "onion": "प्याज"}


def parse(text: str):
    t = text.lower()
    crop = next((c for c, ks in KEYWORDS.items() if any(k in t for k in ks)), None)
    city = next((c for c in CITIES if c in t), "kanpur")
    if any(k in t for k in ["weather", "rain", "mausam", "मौसम", "बारिश", "barish"]):
        intent = "weather"
    elif any(k in t for k in ["trend", "history", "past", "पिछले"]):
        intent = "trend"
    elif any(k in t for k in ["sell", "wait", "bech", "बेच", "रुक", "रोक", "ruk", "roku", "bechu", "when", "kab", "कब", "should", "chahiye"]):
        intent = "advice"
    elif any(k in t for k in ["forecast", "predict", "next", "आगे", "अनुमान"]):
        intent = "forecast"
    elif any(k in t for k in ["price", "rate", "bhav", "bhaav", "भाव", "दाम", "कीमत"]):
        intent = "price"
    else:
        intent = "help"
    return intent, crop, city, bool(re.search("[\u0900-\u097F]", text))


async def call(session, name, args, trace):
    res = await session.call_tool(name, args)
    data = res.structuredContent or json.loads(res.content[0].text)
    trace.append({"tool": name, "args": args})
    return data


def reply_text(intent, crop, hi, data):
    c = NAMES_HI[crop] if hi and crop else crop
    if intent == "price":
        return (f"आज {c} का भाव {data['today']} रुपये प्रति क्विंटल है।" if hi else f"{c.title()} is selling at {data['today']} rupees per quintal today.")
    if intent == "trend":
        d = "बढ़ा" if data["change_pct"] >= 0 else "घटा"
        return (f"पिछले {data['days']} दिनों में {c} का भाव {abs(data['change_pct'])} प्रतिशत {d}।" if hi else
                f"Over the last {data['days']} days, {c} moved {data['change_pct']:+.1f}%, now {data['today']} rupees per quintal.")
    if intent == "forecast":
        last = data["forecast"][-1]
        return (f"मॉडल के अनुसार 14 दिन बाद {c} का भाव करीब {last['price']} रुपये होगा।" if hi else
                f"My model expects {c} near {last['price']} rupees per quintal in 14 days (7-day test error about {data['holdout_7day_error_pct']}%).")
    if intent == "advice":
        if data["action"] == "wait":
            return (f"{c} अभी रोकें। {data['best_date']} तक भाव {data['expected_gain_pct']} प्रतिशत बढ़ने की उम्मीद है।" if hi else
                    f"Wait on your {c}. I expect about {data['expected_gain_pct']}% more by {data['best_date']}.")
        return (f"{c} अभी बेच दें। आगे बड़ी बढ़त की उम्मीद नहीं है।" if hi else f"Sell your {c} now: {data['reason']}.")
    return ""


@mcp.custom_route("/", methods=["GET"])
async def index(_: Request):
    return HTMLResponse((STATIC / "index.html").read_text(encoding="utf-8"))


@mcp.custom_route("/api/chat", methods=["POST"])
async def chat(request: Request):
    text = (await request.json()).get("text", "")
    intent, crop, city, hi = parse(text)
    if intent == "help" or (intent != "weather" and not crop):
        msg = ("आप गेहूं, धान, टमाटर, आलू या प्याज का भाव पूछ सकते हैं, जैसे: 'टमाटर बेचूं या रुकूं?'" if hi else
               "Ask me about wheat, rice, tomato, potato or onion. Try: 'Should I sell my tomatoes now?'")
        return JSONResponse({"reply": msg, "trace": [], "hi": hi})
    trace, series_out, card = [], None, None
    async with streamablehttp_client(f"http://127.0.0.1:{PORT}/mcp") as (r, w, _):
        async with ClientSession(r, w) as session:
            await session.initialize()
            if intent == "weather":
                d = await call(session, "get_weather", {"city": city}, trace)
                rain = d.get("rain_expected")
                msg = (("बारिश की संभावना है, फसल ढककर रखें।" if rain else "अगले तीन दिन बड़ी बारिश नहीं दिख रही।") if hi else
                       (f"Heavy rain is possible near {city.title()} in the next 3 days. Cover your produce." if rain else f"No heavy rain expected near {city.title()} for 3 days."))
                return JSONResponse({"reply": msg, "trace": trace, "hi": hi})
            if intent == "advice":
                w_ = await call(session, "get_weather", {"city": city}, trace)
                data = await call(session, "sell_or_wait_advice", {"crop": crop, "rain_expected": bool(w_.get("rain_expected"))}, trace)
                series_out = data["forecast"]; card = {"action": data["action"], "reason": data["reason"]}
            elif intent == "forecast":
                data = await call(session, "forecast_price", {"crop": crop}, trace); series_out = data["forecast"]
            elif intent == "trend":
                data = await call(session, "get_price_trend", {"crop": crop, "days": 30}, trace); series_out = data["history"]
            else:
                data = await call(session, "get_price_trend", {"crop": crop, "days": 7}, trace)
                series_out = data["history"]
    return JSONResponse({"reply": reply_text(intent, crop, hi, data), "trace": trace, "series": series_out, "card": card, "crop": crop, "hi": hi})


def main():
    print(f"Mandi Mitra running: web demo http://localhost:{PORT}/  |  MCP endpoint http://localhost:{PORT}/mcp")
    mcp.run(transport="streamable-http")


if __name__ == "__main__":
    main()
