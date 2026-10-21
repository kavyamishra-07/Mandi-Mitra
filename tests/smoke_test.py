"""Starts nothing: connects to a running server and checks every MCP tool. Run: python tests/smoke_test.py"""
import asyncio, json, sys
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client

URL = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8000/mcp"


def data(res):
    return res.structuredContent or json.loads(res.content[0].text)


async def main():
    async with streamablehttp_client(URL) as (r, w, _):
        async with ClientSession(r, w) as s:
            await s.initialize()
            tools = [t.name for t in (await s.list_tools()).tools]
            print("tools:", tools)
            assert {"list_crops", "get_price_trend", "forecast_price", "get_weather", "sell_or_wait_advice"} <= set(tools)
            res = await s.call_tool("sell_or_wait_advice", {"crop": "onion"})
            d = data(res)
            assert d["action"] in ("wait", "sell_now") and len(d["forecast"]) == 14
            print("onion advice:", d["action"], "-", d["reason"])
            bad = await s.call_tool("forecast_price", {"crop": "banana"})
            assert "error" in data(bad)
    print("ALL OK")

asyncio.run(main())
