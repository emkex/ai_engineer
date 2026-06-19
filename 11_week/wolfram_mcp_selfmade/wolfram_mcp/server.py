"""
wolfram_mcp.server
==================

A free, self-hosted MCP server that exposes Wolfram|Alpha as a *ground-truth*
computational layer for any MCP-capable agent (Claude Code, Claude Desktop,
Cursor, your own code, ...).

It mirrors the spirit of Wolfram's own MCP "WolframAlpha" tool but is built
entirely on the **free** Wolfram|Alpha REST APIs (one AppID, 2,000 non-commercial
calls/month). It adds the things a single tool can't do: a one-line answer, a
spoken sentence, a *rendered image* (maps/plots/tables), and structured JSON.

Transports
----------
* ``stdio`` (default) — for Claude Code / Desktop / local agents.
* ``streamable-http`` — for remote agents and code clients.

Select via ``WOLFRAM_MCP_TRANSPORT`` env var or ``--transport`` CLI flag.

Run::

    export WOLFRAM_APP_ID="your-appid"
    python -m wolfram_mcp.server                       # stdio
    python -m wolfram_mcp.server --transport streamable-http --host 127.0.0.1 --port 8000
"""

from __future__ import annotations

import argparse
import os

from mcp.server.fastmcp import FastMCP, Image

from . import _usage
from .core import (
    SimpleImage,
    WolframClient,
    WolframError,
)

# --------------------------------------------------------------------------- #
# Server + shared client
# --------------------------------------------------------------------------- #
INSTRUCTIONS = """\
Wolfram|Alpha — a deterministic computation engine + curated knowledge base.
Use it as a CALCULATOR and a SCIENTIFIC / HISTORICAL REFERENCE, NOT a web search.
It computes (doesn't hallucinate) and returns curated data AS OF A DATE.

USE Wolfram (high value — prefer it over memory or web) for:
- Math: integrals, derivatives, limits, sums, ODEs, solve / factor / simplify.
- Linear algebra & stats: matrices/eigenvalues, distributions, regression, tests.
- Units / currency / date conversions and exact physical & chemical constants.
- Chemistry/physics/astronomy properties (bp, density, dipole, pKa, mass, spectra).
- Geography & curated facts: population, area, coordinates, country data.
- HISTORICAL numeric values & TIME SERIES: "X in 2018", prices / inflation / GDP
  by year or over a range (e.g. "Elon Musk net worth 2018" -> $19B with its date;
  "crude oil price 2005 to 2015"). Excellent for dynamics, trends and regression
  on history — pull the series, then compute on it.

DON'T use Wolfram (use web search / Tavily / Brave / Wikipedia instead) for:
- LIVE / current prices: stocks, ETFs, crypto, commodity spot prices.
- Current market caps, today's billionaire net worth, real-time anything.
- Breaking news, current events, wars, politics, company/startup/product info,
  opinions, sentiment. Wolfram is stale or empty here — don't burn a call.
(Rule of thumb: if the answer changed this week, it's probably NOT Wolfram.)

WORK WITH THE NUMBERS (the point of this server): once you obtain a value or
series, CHAIN it into computation — derive quantities, fit a regression, test a
hypothesis, combine series — proactively toward the user's goal, even if not
explicitly asked. Wolfram gives both the numbers AND the engine to compute on them.
Before building a numerical argument, estimate, forecast, comparison, or economic
reasoning chain, ask whether ONE Wolfram query could replace several guessed
assumptions. Fetch numbers to REDUCE hallucination — not numbers for their own sake.

TOKEN EFFICIENCY (don't waste calls/tokens):
- Prefer wolfram_short_answer for one value (cheapest).
- wolfram_ask for an explained answer + image URLs (text).
- wolfram_full_results is the HEAVIEST (pods + metadata + assumptions) — use ONLY
  when you truly need structure / assumptions / multiple fields; never as default.
- Don't call Wolfram "just because there's a number". Call when it adds real
  value: verifiable math, exact constants, curated/historical data, high-stakes
  facts you'd otherwise guess. One good call beats three reflexive ones.

AS OF A DATE, not real-time: fast-moving figures come back with a measurement
date — report them "as of <date>", don't present them as the live value.

MODEL CAPABILITY: all tools return TEXT except wolfram_visual, which returns
IMAGE BYTES (vision-capable model + image client ONLY; text-only models use
wolfram_ask — it returns plots/maps as image URLs inside the text). Visual hard
triggers: show / plot / graph / chart / map / visualize / draw / diagram /
borders / neighbors.

VISUAL OUTPUT POLICY: wolfram_visual returns the rendered image AND its source
URL(s) as text. Always show the image and display EVERY URL it returns; if it
says "No image URL was available", state that. The URL is part of the result,
not optional metadata — never present a visual without exposing its URL(s).

Routing: short_answer[ANY] one value · ask[ANY] explained + URLs ·
verify[ANY] check a claim · spoken[ANY] one sentence · full_results[ANY]
structured/disambiguation (heavy) · visual[VISION] see an image · usage quota.

Query etiquette: English keywords ("France population"); QUALIFY ambiguous data
with units/currency ("neodymium price in USD per kg" — otherwise it may answer in
a foreign currency); '6*10^14' not '6e14'; single-letter vars; separate calls per
property. A "response in time" / timeout 501 is a server-side compute limit, NOT
a bad query — retry or raise the timeout (wolfram_visual auto-falls back to image
URLs + a summary, so visuals are never silently lost). If a result is ambiguous,
re-send the same query with the 'assumption' value Wolfram offers.
"""

mcp = FastMCP(
    "wolfram",
    instructions=INSTRUCTIONS,
    host=os.environ.get("WOLFRAM_MCP_HOST", "127.0.0.1"),
    port=int(os.environ.get("WOLFRAM_MCP_PORT", "8000")),
)

_client: WolframClient | None = None


def client() -> WolframClient:
    global _client
    if _client is None:
        _client = WolframClient()
    return _client


def _with_quota_note(text: str, endpoint: str) -> str:
    """Record the call and append a quota warning if we're getting close."""
    _usage.record(endpoint)
    warn = _usage.warning()
    return f"{text}\n\n[wolfram-mcp quota] {warn}" if warn else text


# --------------------------------------------------------------------------- #
# Tools
# --------------------------------------------------------------------------- #
@mcp.tool()
def wolfram_ask(
    query: str,
    maxchars: int = 6800,
    units: str | None = None,
    assumption: str | list[str] | None = None,
    location: str | None = None,
) -> str:
    """Ask Wolfram|Alpha and get a detailed, LLM-ready answer (the default tool).

    Model/client: ANY model (TEXT output). No vision needed — any maps/plots/
    tables come back as `image: https://...` URLs *inside the text*, so even a
    text-only model gets the data and the link. This is the tool to use instead
    of wolfram_visual when the running model cannot see images.

    Returns the interpretation, computed result and, where relevant, **image
    URLs** (maps, plots, periodic-table highlights, tables) embedded inline as
    `image: https://...`. Use this to VERIFY math/data or to answer factual and
    computational questions with a trustworthy engine instead of memory.

    Data is ground-truth AS OF A DATE, not real-time: for fast-moving values
    (net worth, prices) report the figure with its measurement date and don't
    treat it as the live number.

    Good queries: "integrate x^2 sin(x) dx", "solve x^2-5x+6=0",
    "standard deviation 2,4,4,4,5,5,7,9", "GDP of Germany 2023",
    "eigenvalues {{2,0},{0,3}}", "distance Earth to Mars today".

    Args:
        query: Plain-English or math-notation question. Keep it a single line;
            prefer keyword form ("France population").
        maxchars: Max characters in the response (default 6800). Lower it for a
            terser answer.
        units: "metric" or "imperial" to force a unit system.
        assumption: If a previous call returned ambiguous results, pass the
            Wolfram-provided assumption code(s) here (string or list) and
            re-send the SAME query to disambiguate.
        location: A place name to resolve location-dependent queries
            (e.g. "weather", "planes overhead") from, e.g. "Paris, France".
    """
    try:
        text = client().llm(
            query,
            maxchars=maxchars,
            units=units,
            assumption=assumption,
            location=location,
        )
    except WolframError as e:
        return str(e)
    return _with_quota_note(text, "llm")


@mcp.tool()
def wolfram_short_answer(query: str, units: str | None = None) -> str:
    """Get a single concise plain-text answer (fastest; one value or phrase).

    Model/client: ANY model (TEXT output, one line). Safest default for small /
    text-only / non-multimodal models — nothing to render or interpret visually.

    Use for quick scalar checks where you only need the result, not the working.
    Example: "derivative of x^3" -> "3 x^2"; "speed of light" -> "299792458 m/s".
    If no sufficiently short result exists, returns a message suggesting
    `wolfram_ask` instead.

    Args:
        query: The question/expression.
        units: "metric" or "imperial".
    """
    try:
        text = client().short(query, units=units)
    except WolframError as e:
        return str(e)
    return _with_quota_note(text, "short")


@mcp.tool()
def wolfram_spoken(query: str, units: str | None = None) -> str:
    """Get a single natural-language sentence answer (good for spoken/voice use).

    Model/client: ANY model (TEXT output, one sentence). No vision needed.

    Example: "How far is the Moon?" -> "The average distance ... is about ...".

    Args:
        query: The question.
        units: "metric" or "imperial".
    """
    try:
        text = client().spoken(query, units=units)
    except WolframError as e:
        return str(e)
    return _with_quota_note(text, "spoken")


@mcp.tool()
def wolfram_visual(
    query: str,
    layout: str = "divider",
    width: int = 700,
    units: str | None = None,
    background: str | None = None,
    foreground: str | None = None,
    fontsize: int = 14,
):
    """Render the full Wolfram|Alpha result as an IMAGE you can actually see.

    ⚠️ Model/client requirement: this returns rendered IMAGE BYTES. It is only
    useful to a VISION-CAPABLE (multimodal) model AND an image-capable client.
    If the running model CANNOT see images (e.g. a small text-only model), do
    NOT call this — call `wolfram_ask` or `wolfram_full_results` instead, which
    return the same plots/maps as image URLs + data *as text*. Only call this on
    explicit visual intent — hard triggers: show, plot, graph, chart, map,
    visualize, draw, diagram, geometry, borders, neighbors, "what does ... look
    like". For a plain number/fact, prefer wolfram_short_answer / wolfram_ask.

    Always returns the image AND its public source URL(s) as text (plus a short
    summary) — the URL is part of the result, so a non-image client never loses
    the link. (Getting the URL costs one extra Full Results call, since the
    Simple API returns only bytes; visual queries are rare, so this is worth it.)

    Never loses visuals: the single-image render has a server-side compute
    budget; if it times out (common for rich maps/tables) this tool automatically
    retries via the Full Results API and returns the recovered image (inline) +
    all image URLs + a short data summary as text — so something useful always
    comes back, even on a non-image client.

    Use this when the value is visual: maps, plots/graphs, geometry, formatted
    tables, the whole result page. Classic example: "neighbors of Spain" returns
    a map plus a bordering-country table in one image.

    Args:
        query: The question/expression to visualize.
        layout: "divider" (default, pods separated by lines) or "labelbar".
        width: Image width in px (default 700).
        units: "metric" or "imperial".
        background: Background color: HTML name, hex ("F5F5F5"), "r,g,b", or
            "transparent".
        foreground: "black" (default) or "white" for text.
        fontsize: Text size in points (default 14).
    """
    try:
        img: SimpleImage = client().simple(
            query,
            layout=layout,
            width=width,
            units=units,
            background=background,
            foreground=foreground,
            fontsize=fontsize,
        )
    except WolframError as e:
        # The Simple API renders the whole result as ONE image and often can't
        # finish rich results (maps, country borders, big tables) within its
        # compute budget -> it returns a timeout. Recover gracefully via the
        # Full Results API, which exposes the same renders as per-pod image URLs.
        return _visual_fallback(query, units, str(e))
    _usage.record("simple")
    # VISUAL OUTPUT CONTRACT: always surface the public image URL(s) as text so
    # the URL is part of the result (never optional metadata the model can drop)
    # and non-image clients still get a usable link. The Simple API returns only
    # bytes — and its own URL embeds the AppID — so we fetch the public per-pod
    # URLs from Full Results. One extra call, but visual queries are rare.
    caption = (
        f"Wolfram|Alpha rendered IMAGE for: {query}\n"
        f"{_image_url_lines(query, units)}\n"
        "(Image bytes below are readable only by a vision-capable client; the "
        "URL(s) above open anywhere. Text-only models: prefer wolfram_ask.)"
    )
    warn = _usage.warning()
    if warn:
        caption += f"\n[wolfram-mcp quota] {warn}"
    return [caption, Image(data=img.data, format=img.image_format)]


def _image_url_lines(query: str, units: str | None) -> str:
    """Fetch public image URL(s) for a visual query via Full Results (robust)."""
    try:
        qr = client().full(query, units=units, formats="image")
        _usage.record("full")
        pairs = WolframClient.image_urls(qr)
    except WolframError:
        pairs = []
    if not pairs:
        return "No image URL was available from Wolfram."
    lines = ["Image URL(s):"]
    lines += [f"- {title}: {src}" for title, src in pairs[:12]]
    return "\n".join(lines)


def _visual_fallback(query: str, units: str | None, simple_error: str):
    """Recover visual output via Full Results when the Simple API can't render."""
    try:
        qr = client().full(query, units=units, formats="plaintext,image")
    except WolframError as e2:
        return (
            f"Could not render '{query}' as an image.\n"
            f"- Simple API: {simple_error}\n- Full Results API: {e2}"
        )
    _usage.record("full")
    pairs = WolframClient.image_urls(qr)
    digest = WolframClient.digest_full(qr)

    lines = [
        f"Wolfram|Alpha result for: {query}",
        "(The single-image render timed out; recovered the visual(s) and data "
        "from the Full Results API.)",
    ]
    if pairs:
        lines.append("")
        lines.append("Image URLs:")
        lines += [f"- {title}: {src}" for title, src in pairs[:12]]
    lines.append("")
    lines.append(digest[:3000])
    note = "\n".join(lines)
    warn = _usage.warning()
    if warn:
        note += f"\n\n[wolfram-mcp quota] {warn}"

    # Prefer a non-"Input interpretation" pod image to show inline (e.g. the map).
    chosen = next(
        (src for title, src in pairs if "input" not in title.lower()),
        pairs[0][1] if pairs else None,
    )
    if chosen:
        try:
            resp = client().http.get(chosen)
            ctype = resp.headers.get("content-type", "")
            if resp.status_code == 200 and ctype.startswith("image"):
                from .core import _format_to_short

                return [note, Image(data=resp.content, format=_format_to_short(ctype))]
        except Exception:
            pass  # fall through to text-only result
    return note


@mcp.tool()
def wolfram_full_results(
    query: str,
    units: str | None = None,
    assumption: str | list[str] | None = None,
    include_pod_ids: str | list[str] | None = None,
    raw_json: bool = False,
) -> str:
    """Query the Full Results API and get STRUCTURED output (pods + assumptions).

    Model/client: ANY model (TEXT/JSON output). Image pods come back as URLs in
    the text — no vision needed; a text-only model can use this to get a visual's
    link + data without wolfram_visual.

    ⚠️ TOKEN COST: this is the HEAVIEST tool — it returns every pod, plaintext,
    image URLs, assumptions and metadata (often thousands of tokens). Do NOT use
    it as a default. For a single value use `wolfram_short_answer`; for an
    explained answer use `wolfram_ask`. Reach for this ONLY when you genuinely
    need structure, multiple fields, or to drive disambiguation; narrow it with
    `include_pod_ids` (e.g. "Result") to keep the payload small.

    Most powerful endpoint. Returns each result pod (title + plaintext + image
    URL) plus any assumptions and "did you mean" suggestions.

    Args:
        query: The question/expression.
        units: "metric" or "imperial".
        assumption: Assumption code(s) to disambiguate (string or list).
        include_pod_ids: Restrict output to specific pod id(s) to save space,
            e.g. "Result" or ["Result", "Plot"].
        raw_json: If true, return the raw JSON string instead of a text digest.
    """
    try:
        qr = client().full(
            query,
            units=units,
            assumption=assumption,
            includepodid=include_pod_ids,
        )
    except WolframError as e:
        return str(e)
    _usage.record("full")
    if raw_json:
        import json

        out = json.dumps(qr, ensure_ascii=False)[:60000]
    else:
        out = WolframClient.digest_full(qr)
    warn = _usage.warning()
    return f"{out}\n\n[wolfram-mcp quota] {warn}" if warn else out


@mcp.tool()
def wolfram_verify(claim: str, units: str | None = None) -> str:
    """Check a specific factual/numeric CLAIM against Wolfram ground truth.

    Model/client: ANY model (TEXT output). This is the workhorse for the most
    common use of this server: verifying slowly-changing facts/values before you
    assert them.

    Use this right before asserting a checkable statement, instead of trusting
    memory. It sends the claim to Wolfram|Alpha (deterministic engine, curated
    data) and returns the ground-truth result next to your claim so you can
    confirm it or correct it.

    AS OF A DATE, not real-time: Wolfram gives the last curated value with its
    measurement date. For fast-moving figures (net worth, prices) a claim can be
    "stale-correct" — e.g. a net worth that was right at Wolfram's measurement
    date but outdated after a recent event. Treat a mismatch on a volatile value
    as "verify the date / may have moved", not necessarily "the claim is false",
    and always report the measurement date Wolfram returns.

    Best for claims that resolve to a value or fact:
      "the derivative of x^3 is 3x^2", "France population is 70 million",
      "speed of light is 3e8 m/s", "GDP of Japan 2023 was $5 trillion".

    Args:
        claim: The statement to check. Phrase the checkable core in keywords
            (a value, quantity, formula, or fact), not a yes/no question.
        units: "metric" or "imperial".

    Returns:
        The claim alongside Wolfram's computed/looked-up ground truth. Compare
        them and state whether the claim holds, giving the corrected value if
        not. (This returns evidence to judge against — it does not invent a
        true/false verdict for you.)
    """
    try:
        truth = client().llm(claim, maxchars=1400, units=units)
    except WolframError as e:
        return f"Could not verify '{claim}' with Wolfram: {e}"
    out = (
        f"CLAIM TO VERIFY:\n{claim}\n\n"
        "WOLFRAM|ALPHA GROUND TRUTH (deterministic, not model memory):\n"
        f"{truth}\n\n"
        "Now compare: state whether the claim holds and give the corrected "
        "value if it does not."
    )
    return _with_quota_note(out, "llm")


@mcp.tool()
def wolfram_usage() -> str:
    """Report the advisory local estimate of your free Wolfram quota usage.

    Shows calls today / this month and how many of the free 2,000/month (and
    ~100/day soft cap) appear to remain. This is a LOCAL estimate, not Wolfram's
    authoritative count.
    """
    import json

    return json.dumps(_usage.stats(), indent=2)


# --------------------------------------------------------------------------- #
# Entry point
# --------------------------------------------------------------------------- #
def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Wolfram|Alpha MCP server")
    parser.add_argument(
        "--transport",
        default=os.environ.get("WOLFRAM_MCP_TRANSPORT", "stdio"),
        choices=["stdio", "streamable-http", "sse"],
        help="MCP transport (default: stdio).",
    )
    parser.add_argument("--host", default=os.environ.get("WOLFRAM_MCP_HOST", "127.0.0.1"))
    parser.add_argument(
        "--port", type=int, default=int(os.environ.get("WOLFRAM_MCP_PORT", "8000"))
    )
    args = parser.parse_args(argv)

    # Apply host/port for network transports.
    mcp.settings.host = args.host
    mcp.settings.port = args.port

    # Fail fast with a clear message if no AppID is configured at all.
    if not (
        os.environ.get("WOLFRAM_APP_ID")
        or any(os.environ.get(v) for v in (
            "WOLFRAM_APP_ID_LLM",
            "WOLFRAM_APP_ID_SHORT",
            "WOLFRAM_APP_ID_SPOKEN",
            "WOLFRAM_APP_ID_SIMPLE",
            "WOLFRAM_APP_ID_FULL",
        ))
    ):
        import sys

        print(
            "WARNING: WOLFRAM_APP_ID is not set. Tools will return a configuration "
            "error until you set it. Get a free AppID at "
            "https://developer.wolframalpha.com/",
            file=sys.stderr,
        )

    mcp.run(transport=args.transport)


if __name__ == "__main__":
    main()
