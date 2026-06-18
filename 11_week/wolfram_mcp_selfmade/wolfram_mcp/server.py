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
Wolfram|Alpha as a deterministic, ground-truth computation and knowledge layer.

Core principle: DO NOT answer math, numbers, units, dates, physical/chemical
constants, or curated real-world data from memory. If a value can be computed
or looked up, verify it here FIRST, then answer. Wolfram computes
deterministically and does not hallucinate — prefer it over a guess every time.

Always route through a tool (not memory) for:
- derivatives, integrals, limits, sums, ODEs/PDEs
- solving equations / systems, factoring, simplification
- matrices (eigenvalues, determinant, inverse), linear algebra
- statistics, distributions, regression, hypothesis tests
- unit / currency / date conversions and exact constants
- curated data: GDP, population, elements, astronomy, geography, finance series

Routing rule (pick the smallest tool that answers the question):
- wolfram_short_answer  -> one number/phrase, fastest. ("derivative of x^3")
- wolfram_ask           -> default; detailed LLM-ready answer WITH image URLs.
- wolfram_verify        -> check a specific CLAIM ("France population is 70M")
                           against ground truth before you assert it.
- wolfram_spoken        -> a single natural sentence (good for voice replies).
- wolfram_visual        -> when the answer is VISUAL: maps, plots/graphs,
                           geometry, geographic borders / country neighbors,
                           formatted tables, the full result page as one image
                           (e.g. "neighbors of Spain", "plot sin(x)/x").
- wolfram_full_results  -> structured data / disambiguation (pods, assumptions).
- wolfram_usage         -> check remaining free quota.

Query tips: send English, keyword-style queries ("France population", not
"how many people live in France"); use '6*10^14' not '6e14'; single-letter
variables; make separate calls for separate properties. If a result is not
relevant and Wolfram offers assumptions, re-send the same query with the
'assumption' value rather than rephrasing. A "timed out / response in time"
message is NOT a bad query — it is a server-side compute limit; retry or raise
the timeout (wolfram_visual already does this and falls back automatically).
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

    Returns the interpretation, computed result and, where relevant, **image
    URLs** (maps, plots, periodic-table highlights, tables) embedded inline as
    `image: https://...`. Use this to VERIFY math/data or to answer factual and
    computational questions with a trustworthy engine instead of memory.

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

    Use this when the value is visual: maps, plots/graphs, geometry, formatted
    tables, the whole result page. Classic example: "neighbors of Spain" returns
    a map plus a bordering-country table in one image. Returns the rendered image
    (plus a short caption); MCP clients that support images will display it.

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
    caption = f"Wolfram|Alpha rendered result for: {query}"
    warn = _usage.warning()
    if warn:
        caption += f"\n[wolfram-mcp quota] {warn}"
    return [caption, Image(data=img.data, format=img.image_format)]


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

    Most powerful endpoint. Returns each result pod (title + plaintext + image
    URL) plus any assumptions and "did you mean" suggestions. Use it for
    structured/programmatic needs or to drive disambiguation when `wolfram_ask`
    is ambiguous.

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

    Use this right before asserting a checkable statement, instead of trusting
    memory. It sends the claim to Wolfram|Alpha (deterministic engine, curated
    data) and returns the ground-truth result next to your claim so you can
    confirm it or correct it.

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
