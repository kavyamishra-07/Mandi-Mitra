# Devpost submission text (copy and paste)

## Project name
Mandi Mitra

## Tagline
A voice advisor that tells farmers whether to sell their crop now or wait.

## Text description
**Inspiration.** Many small farmers sell on the day they reach the mandi. Prices swing 5-30% within weeks, and perishable crops like tomato
spoil in days. Most farmers cannot read charts or apps, but they can talk to a voice assistant.

**What it does.** Mandi Mitra is a self-hosted MCP server for Alexa+ with five tools: crop list, recent price trend, a 14-day ML price
forecast, a 3-day rain outlook, and a sell-or-wait recommendation. Ask "Should I sell my onions now?" (or in Hindi,
"क्या मैं प्याज रोकूं?") and it answers by voice with a clear action and reason.

**How it works.** A gradient-boosting model learns next-day price moves from lagged prices and seasonality, and forecasts 14 days ahead
recursively. The server tests it on held-out data and reports the error. The advice tool combines the forecast with each crop's shelf life (wait
only if prices should rise 3% or more inside the storage window) and rain risk from Open-Meteo (perishables are sold before heavy rain).
Because we took the simulated-experience path, a web app plays the role of Alexa+ with speech in and out in English and Hindi. It talks
to the server over real MCP calls, and the interface shows every tool call.

**Built with.** Python, MCP Python SDK (Streamable HTTP), scikit-learn, pandas, Open-Meteo, Web Speech API.

**Challenges.** Making advice trustworthy, not just a forecast: we hold-out test the model, respect shelf life, and say plainly when no
rise is expected. The bundled demo data is synthetic so it runs offline; the loader accepts real Agmarknet CSV exports.

**What's next.** Per-mandi real prices, more languages and crops, WhatsApp/SMS alerts, Bedrock for free-form questions.

## Track and mini challenges
Primary track: **Alexa+** (simulated-experience path). Mini challenge: **Open Source** (MIT-licensed public repo, include repo URL,
GitHub username and a short description).

## Product feedback (review and edit so it matches your own experience)
- **MCP Python SDK:** Easy to get a tool server running with `FastMCP` and the decorator style. Pain points: the 2.x release renamed
  `FastMCP` to `MCPServer` and changed client imports, which broke most tutorials, so we pinned `mcp<2`. Tools that return a plain `dict` give
  no `structuredContent`, so clients must fall back to parsing text; clearer docs on return types would help.
- **Open-Meteo:** Free, no key, fast onboarding. Worked well; we added a fallback for offline use.
- **Alexa+ / MCP onboarding:** We took the simulated-experience path. Clearer step-by-step docs for registering a self-hosted
  MCP server with Alexa+ in Preview would help. We would build with it again.

## 3-minute demo video script
1. **0:00-0:20** Problem: "Farmers sell at the wrong time. Mandi Mitra tells them when to sell, by voice." Show the app.
2. **0:20-1:10** Tap the mic, say "Should I sell my onions now?" Show the answer, the chart, and the MCP tool calls panel on the right.
3. **1:10-1:40** Switch voice to Hindi, ask "क्या मैं आलू रोकूं?" Then ask "Should I sell my tomatoes?" to show the shelf-life logic (sell now).
4. **1:40-2:20** Show the code: `server.py` tools, `model.py` forecast, then run `python tests/smoke_test.py` ("ALL OK").
5. **2:20-2:50** Show the GitHub repo with the MIT license, say how it plugs into Alexa+ at `/mcp`, and what is next.
Record with the built-in screen recorder, no copyrighted music, upload as public on YouTube, English narration.

## Before you submit
- [ ] Repo is public with LICENSE (or shared with testing@devpost.com and the Amazon team)
- [ ] Demo video public, under 3 minutes, in English
- [ ] Description, track, mini challenge and product feedback pasted
- [ ] Submit before 23 Oct 2026, 12:00 PM PT (about 12:30 AM IST on 24 Oct), ideally earlier
