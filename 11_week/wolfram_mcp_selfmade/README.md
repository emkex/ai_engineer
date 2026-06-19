# Wolfram MCP — free ground-truth computation for agents

A small, production-minded **MCP server *and* Python client** built entirely on
the **free** [Wolfram|Alpha REST APIs](https://products.wolframalpha.com/api).
It gives any agent (Claude Code, Claude Desktop, Cursor, or your own code) a
deterministic, non-hallucinating layer for math, units, dates and curated
real-world data — a cheap alternative to the paid Wolfram MCP, within the free
**2,000 calls/month** tier.

It wraps five Wolfram endpoints behind one consistent interface and lets the
calling LLM choose the right one per task:

| Tool | Wolfram API | Returns | Use it for |
|---|---|---|---|
| `wolfram_short_answer` | Short Answers | one line of text | a single number/phrase, fastest |
| `wolfram_ask` | LLM API | LLM-ready text **+ image URLs** | the default; verify math, full answers |
| `wolfram_verify` | LLM API | claim **+ ground truth** | check a specific claim before asserting it |
| `wolfram_spoken` | Spoken Results | one natural sentence | voice / conversational replies |
| `wolfram_visual` | Simple API (+ Full Results fallback) | a **rendered image** | maps, plots, tables you want to *see* |
| `wolfram_full_results` | Full Results | **structured JSON** (pods + assumptions) | programmatic data, disambiguation |
| `wolfram_usage` | — | quota estimate | check remaining free calls |

> Example of why `wolfram_visual` exists: `neighbors of Spain` returns a map
> **and** a bordering-country table rendered as a single image — the kind of
> output plain text can't carry.
>
> Rich renders (maps, country borders, large tables) exceed the Simple API's
> default 5-second compute budget and come back as a "could not give a response
> in time" 501. `wolfram_visual` defaults that budget to 15s **and** falls back
> to the Full Results API (pulling the per-pod image URLs and showing one
> inline) so these queries return an image instead of an error.

### When to use Wolfram — and when NOT to (the honest scope)

This is a **computational engine + curated/historical reference**, not a search
engine. Used in scope it's deterministic ground truth; used out of scope it
wastes tokens and returns stale or empty answers. The server `instructions`
encode this so the agent routes itself.

| ✅ Use Wolfram | ❌ Use web search instead (Tavily / Brave / Wikipedia) |
|---|---|
| Math: integrals, derivatives, solve, matrices, eigenvalues | **Live** stock / ETF / crypto / commodity **spot** prices |
| Statistics, distributions, **regression**, hypothesis tests | Current market caps, **today's** billionaire net worth |
| Unit / currency / date conversions, exact constants | Breaking news, current events, wars, politics |
| Chemistry / physics / astronomy properties | Company / startup / product info, opinions, sentiment |
| Geography & curated facts (population, area, GDP) | Anything that changed **this week** |
| **Historical** values & **time series** ("X in 2018", prices/inflation/GDP by year) | |

> **History is a strength, "now" is not.** Wolfram returns curated data *as of a
> date*. `Elon Musk net worth 2018` → `$19B` (with its date) is reliable; his
> *current* net worth is stale. Use it for **dynamics / trends / regression on
> history**, not the live number.
>
> **Token discipline:** prefer `wolfram_short_answer` (one value, cheapest);
> `wolfram_full_results` is the heaviest (pods + metadata) — use it sparingly and
> narrow with `include_pod_ids`. Don't call Wolfram "just because there's a
> number" — call it when it adds real value (verifiable math, constants,
> curated/historical data).
>
> **Then compute on the result:** the point isn't just lookup — once the agent
> has a number or series it can chain it into further math (derive, fit, test a
> hypothesis) toward your goal.
>
> **Query etiquette:** qualify ambiguous data with units/currency — `neodymium
> price in USD per kg` → `$450/kg`, whereas a bare `neodymium price` may answer in
> a foreign currency.

### Which tools your model can use (text vs. vision)

Pick the model first; the tool descriptions encode what each one needs so the
model routes itself correctly (and you can deny tools a model can't consume).

| Output | Tools | Model requirement |
|---|---|---|
| **Text** | `wolfram_short_answer`, `wolfram_ask`, `wolfram_spoken`, `wolfram_full_results`, `wolfram_verify` | **Any** LLM. `wolfram_ask` / `wolfram_full_results` even return plots/maps as **image URLs inside the text** — a text-only model still gets the link + data. |
| **Image bytes** | `wolfram_visual` | **Vision-capable (multimodal)** model **and** an image-capable client. A text-only / small model should not call it — use `wolfram_ask` instead. |

> Practical lever: in Claude Code you can allow/deny specific MCP tools per
> project in `.claude/settings.local.json` — e.g. omit `wolfram_visual` when the
> session model can't see images.

**Ground truth is "as of a date", not real-time.** Wolfram returns the last
curated value with its measurement date. For fast-moving figures (net worth,
prices) report them *as of* that date and sanity-check — a value can be
"stale-correct" (right when measured, outdated after a recent event).

---

## Your three questions, answered

**1) Is the free tier really 2,000 calls — or is it secretly paid?**
It's genuinely free. Wolfram's developer portal grants *"immediate free access
for up to 2,000 non-commercial API calls per month"* on a free Wolfram ID — no
payment, no card. A ~100 calls/day soft cap is also commonly reported. The
limit is counted **per AppID**, and the **same AppID works for all five
endpoints** here (LLM, Short, Spoken, Simple, Full Results) — they share that
one 2,000/month pool. So you don't need the paid MCP to get started; this covers
real daily use. (See [Limits & quota](#limits--quota).)

**2) Can the LLM see and adjust the parameters itself?**
Yes. Each tool's parameters (`query`, `maxchars`, `units`, `assumption`,
`layout`, `width`, …) are published in the tool's JSON schema, and every
parameter is documented in the tool's description. The model reads those, picks
a tool, and fills the arguments on its own — including following Wolfram's own
disambiguation flow (re-send the same query with an `assumption` value). The
server also ships routing guidance (in its MCP `instructions`) telling the model
which tool to prefer.

**3) Can it be called both by agents like Claude Code *and* from code?**
Yes — three ways, all documented below:
- **Direct import** (`from wolfram_mcp import WolframClient`) — no MCP at all.
- **MCP over stdio** — spawn the server as a subprocess (same tools an agent sees).
- **MCP over Streamable HTTP** — run it as a shared local/remote service.

The package is deliberately split so the HTTP logic lives in a dependency-light
`core` module with **no MCP requirement**, and the MCP server is a thin wrapper
on top.

---

## 1. Get a free AppID

1. Create a Wolfram ID and sign in at <https://developer.wolframalpha.com/>.
2. **My Apps → Get an AppID**, give it a name/description.
3. Copy the AppID (looks like `XXXXXX-XXXXXXXXXX`).

> Tip: you can create several AppIDs. You don't *need* more than one, but it can
> be handy to separate tracking per project — see [Multiple AppIDs](#multiple-appids).

## 2. Install

```bash
git clone <your-repo>  # or copy this folder
cd wolfram-mcp
pip install -r requirements.txt          # minimal: just run it
# or, to also import it from code / get the `wolfram-mcp` command:
pip install -e .
```

Provide the AppID via environment variable (never hard-code it):

```bash
export WOLFRAM_APP_ID="your-appid"
# or: cp .env.example .env  and fill it in, then load it however you prefer
```

## 3. Quick smoke test (standalone)

```bash
export WOLFRAM_APP_ID="your-appid"
python examples/direct_client.py
```

You should see a derivative, an integral, a spoken sentence, a saved
`neighbors_of_spain.*` image, and a GDP figure.

---

## Use it in Claude Code

**stdio (local subprocess — simplest):**

```bash
claude mcp add wolfram --env WOLFRAM_APP_ID="$WOLFRAM_APP_ID" \
  -- python -m wolfram_mcp.server
```

Run that from inside the `wolfram-mcp` folder (so `python -m wolfram_mcp.server`
resolves), or use the absolute path to the package / the installed console
script:

```bash
claude mcp add wolfram --env WOLFRAM_APP_ID="$WOLFRAM_APP_ID" -- wolfram-mcp
```

Then:

```bash
claude mcp list      # 'wolfram' should show as connected
```

Inside a session, type `/mcp` to see the tools, then just ask, e.g.
*"I think ∫x² dx = x³/3 — verify it with Wolfram"* or *"show me the neighbors of
Spain"* (Claude Code will call `wolfram_visual` and display the image).

**Streamable HTTP (shared service):** start the server, then register the URL.

```bash
# terminal 1
WOLFRAM_APP_ID="$WOLFRAM_APP_ID" python -m wolfram_mcp.server \
  --transport streamable-http --host 127.0.0.1 --port 8000
# terminal 2
claude mcp add --transport http wolfram http://127.0.0.1:8000/mcp
```

> All `claude mcp add` flags (`--transport`, `--env`, `--scope`) go **before**
> the server name; `--` separates them from the command to run.

### Claude Desktop / Cursor / other clients

Add an entry to the client's MCP config (Claude Desktop:
`claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "wolfram": {
      "command": "python",
      "args": ["-m", "wolfram_mcp.server"],
      "env": { "WOLFRAM_APP_ID": "your-appid" }
    }
  }
}
```

---

## Use it from code

### A. Direct import (no MCP)

```python
from wolfram_mcp import WolframClient

wa = WolframClient()                          # reads WOLFRAM_APP_ID
print(wa.short("derivative of x^3"))          # "3 x^2"
print(wa.llm("solve x^2-5x+6=0"))             # detailed answer + image URLs
img = wa.simple("neighbors of Spain")         # rendered image
img.save("spain.png")
qr = wa.full("GDP of Germany 2023")           # structured queryresult dict
print(WolframClient.digest_full(qr))
```

Errors are typed (`WolframInterpretError`, `WolframAuthError`,
`WolframNetworkError`, …), all subclasses of `WolframError`, so you can branch:

```python
from wolfram_mcp import WolframError
try:
    wa.short("...")
except WolframError as e:
    print("handled:", e)
```

Full runnable version: [`examples/direct_client.py`](examples/direct_client.py).

### B. MCP over stdio (same tools an agent sees)

```python
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

server = StdioServerParameters(
    command="python", args=["-m", "wolfram_mcp.server"],
    env={"WOLFRAM_APP_ID": "your-appid"},
)
async with stdio_client(server) as (read, write):
    async with ClientSession(read, write) as session:
        await session.initialize()
        res = await session.call_tool("wolfram_short_answer", {"query": "speed of light"})
        print(res.content[0].text)
```

Full version: [`examples/mcp_stdio_client.py`](examples/mcp_stdio_client.py).

### C. MCP over Streamable HTTP (shared service)

```python
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client

async with streamablehttp_client("http://127.0.0.1:8000/mcp") as (read, write, _):
    async with ClientSession(read, write) as session:
        await session.initialize()
        res = await session.call_tool("wolfram_ask", {"query": "GDP per capita Iceland 2024"})
        print(res.content[0].text)
```

Full version: [`examples/mcp_http_client.py`](examples/mcp_http_client.py).

### D. LangChain / LangGraph and other frameworks

Any framework with MCP support can point at this server. With
`langchain-mcp-adapters`, for example, register it as an `http` server at
`http://127.0.0.1:8000/mcp` (or as a `stdio` command) and its tools load
automatically — the tool schemas described above are what the framework sees.

---

## Tool & parameter reference

All tools take a `query` string (English keywords or math notation work best;
keep it one line). Shared/optional parameters:

- **`units`** — `"metric"` or `"imperial"`.
- **`maxchars`** (`wolfram_ask`) — response length cap, default `6800`.
- **`assumption`** (`wolfram_ask`, `wolfram_full_results`) — string or list.
  When a result is ambiguous, re-send the *same* query with the assumption
  code(s) Wolfram returned, rather than rephrasing.
- **`location`** (`wolfram_ask`) — place name for location-dependent queries
  (weather, "planes overhead", …).
- **`layout` / `width` / `background` / `foreground` / `fontsize`**
  (`wolfram_visual`) — image rendering controls. `layout` is `"divider"`
  (default) or `"labelbar"`; colors accept HTML names, hex (`F5F5F5`), `r,g,b`,
  or `transparent`.
- **`include_pod_ids`** (`wolfram_full_results`) — restrict to specific pods
  (e.g. `"Result"`) to save space; **`raw_json`** to get the raw JSON string.
- **`claim`** (`wolfram_verify`) — the checkable statement to test against
  ground truth (e.g. `"France population is 70 million"`). Returns the claim
  next to Wolfram's computed/looked-up value so the model can confirm or correct
  it — it surfaces evidence rather than inventing a true/false verdict.

**Query etiquette that improves results** (baked into the server's instructions):
prefer keyword form (`France population`, not `how many people live in France`);
use `6*10^14`, never `6e14`; single-letter variables; make separate calls for
separate properties; send English.

---

## Security

- **AppID via environment variable only.** Never hard-coded. `.env` is
  git-ignored (the repo-root `.gitignore` covers `.env`, `.env.*`, keys,
  `*.egg-info/`, `.claude/settings.local.json`, …); `.env.example` shows the
  shape and is the only env file that is committed.
- **AppID kept out of URLs where possible.** The LLM API call sends the AppID as
  a `Bearer` token in the `Authorization` header, not the query string. The
  AppID is never logged.
- **HTTPS** for every endpoint; per-request **timeouts**; query length capped.
- **Read-only & idempotent** — every tool is a safe-to-retry GET with no side
  effects.
- **HTTP transport binds to `127.0.0.1` by default.** The MCP HTTP endpoint has
  **no built-in authentication**, so do **not** expose it to a public interface
  as-is. If you must, put it behind a reverse proxy / auth layer, or keep it on
  loopback / a private network and use stdio where you can.
- **Treat the AppID like a password.** If it leaks, rotate it in the developer
  portal. In any user-facing app, also rate-limit per user and keep the AppID
  server-side.

---

## Limits & quota

- Free non-commercial tier: **2,000 calls/month**, commonly **~100/day**, **per
  AppID**, shared across all endpoints used here.
- `wolfram_usage` (and the `[wolfram-mcp quota]` note appended near the limit)
  give a **local, advisory** estimate — only Wolfram knows the real count.
  Tracking is best-effort and never blocks a query; disable with
  `WOLFRAM_TRACK_USAGE=0`.
- **Optional response cache** to save quota: set `WOLFRAM_CACHE_TTL=<seconds>`
  (default `0` = off). Identical idempotent queries within the window reuse the
  cached result instead of spending a call. Keep the TTL short so time-sensitive
  answers (prices, "today") don't go stale.
- Going commercial or need more volume? That's when the paid plans / official
  paid MCP make sense; this project stays on the free tier by design.

### Multiple AppIDs

One AppID is enough — it works for every endpoint. But if you generate several,
you can route specific endpoints to specific keys (e.g. to keep separate usage
counters per project) via env vars, with automatic fallback to `WOLFRAM_APP_ID`:

```bash
export WOLFRAM_APP_ID="default-key"
export WOLFRAM_APP_ID_SIMPLE="key-for-images"   # only wolfram_visual uses this
export WOLFRAM_APP_ID_FULL="key-for-structured" # only wolfram_full_results
```

Or programmatically: `WolframClient(app_id="default", app_ids={"simple": "..."})`.

> Note: creating many AppIDs purely to multiply free quota would run against
> Wolfram's non-commercial terms — use overrides for organization, not as a
> quota hack.

---

## Troubleshooting

- **"No Wolfram AppID configured"** — set `WOLFRAM_APP_ID` (or pass `--env` to
  `claude mcp add`).
- **Auth error / 403** — AppID wrong or monthly quota exhausted; check
  `wolfram_usage` and the developer portal.
- **501 has two meanings** — the client now distinguishes them: *"could not
  give a response in time"* is a **server-side timeout** (the query is fine; it
  surfaces as a retryable network error, and `wolfram_visual` auto-handles it by
  raising the budget + falling back to Full Results), while *"did not understand
  your input"* is a real **interpretation** failure — rephrase in simpler literal
  terms, split into sub-queries, or use standard math notation.
- **No short answer** — use `wolfram_ask` (LLM API) instead; not every question
  has a one-line result.
- **Server not showing in Claude Code** — `claude mcp list`; for stdio, make
  sure `python -m wolfram_mcp.server` runs from a place where the package is
  importable (or `pip install -e .` and use `wolfram-mcp`); restart the session
  so tools are rediscovered.
- **Images don't render** — the client must support image content; otherwise use
  `wolfram_ask`/`wolfram_full_results`, which return image **URLs** as text.

---

## Project layout

```
wolfram-mcp/
├── wolfram_mcp/
│   ├── __init__.py        # exports WolframClient + exceptions
│   ├── core.py            # pure REST client (no MCP dependency)
│   ├── server.py          # FastMCP server (tools, stdio/http entry point)
│   ├── _usage.py          # best-effort local quota tracker
│   └── __main__.py        # `python -m wolfram_mcp`
├── examples/
│   ├── direct_client.py   # use as a library
│   ├── mcp_stdio_client.py# drive the server over stdio
│   └── mcp_http_client.py # connect over streamable HTTP
├── requirements.txt
├── pyproject.toml
├── .env.example           # copy to .env and fill in WOLFRAM_APP_ID
└── README.md              # (.gitignore lives at the repo root)
```

## License

MIT. Use of the Wolfram|Alpha APIs is subject to the
[API Terms of Use](https://products.wolframalpha.com/api/termsofuse).
