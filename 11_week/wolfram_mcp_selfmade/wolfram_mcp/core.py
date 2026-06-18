"""
wolfram_mcp.core
================

A small, dependency-light client for the **free** Wolfram|Alpha REST APIs.

This module has **no MCP dependency**. It is the engine that both the MCP
server (`wolfram_mcp.server`) and any plain Python code can call directly.

One Wolfram AppID works across *all* of these endpoints (they share the same
2,000-call/month non-commercial quota). You may optionally supply a different
AppID per endpoint if you want to separate quotas / tracking — see
``WolframClient`` below.

Endpoints wrapped
-----------------
============== ============================================ ==================
Method         Wolfram API                                  Returns
============== ============================================ ==================
``llm``        LLM API (``/api/v1/llm-api``)                LLM-ready text + image URLs
``short``      Short Answers API (``/v1/result``)           single line of text
``spoken``     Spoken Results API (``/v1/spoken``)          one spoken sentence
``simple``     Simple API (``/v1/simple``)                  a rendered PNG/GIF image
``full``       Full Results API (``/v2/query``)             structured JSON (pods)
============== ============================================ ==================

All methods are read-only and idempotent — safe to retry.

Errors are raised as typed exceptions (see ``WolframError`` and subclasses) so
calling code can branch on them. The MCP layer catches these and turns them
into clear, LLM-readable strings.
"""

from __future__ import annotations

import json as _json
import os
import re
import threading
import time as _time
from dataclasses import dataclass, field
from typing import Any, Iterable, Mapping

import httpx

__all__ = [
    "WolframClient",
    "SimpleImage",
    "WolframError",
    "WolframAuthError",
    "WolframInterpretError",
    "WolframNetworkError",
    "WolframHTTPError",
    "WolframConfigError",
]

# --------------------------------------------------------------------------- #
# Endpoints (always HTTPS).
# --------------------------------------------------------------------------- #
LLM_API_URL = "https://www.wolframalpha.com/api/v1/llm-api"
SHORT_API_URL = "https://api.wolframalpha.com/v1/result"
SPOKEN_API_URL = "https://api.wolframalpha.com/v1/spoken"
SIMPLE_API_URL = "https://api.wolframalpha.com/v1/simple"
FULL_API_URL = "https://api.wolframalpha.com/v2/query"

# Logical endpoint names used for per-endpoint AppID overrides.
ENDPOINT_LLM = "llm"
ENDPOINT_SHORT = "short"
ENDPOINT_SPOKEN = "spoken"
ENDPOINT_SIMPLE = "simple"
ENDPOINT_FULL = "full"

# Environment variables for per-endpoint AppID overrides. If unset, the default
# WOLFRAM_APP_ID is used for that endpoint.
_ENV_OVERRIDES = {
    ENDPOINT_LLM: "WOLFRAM_APP_ID_LLM",
    ENDPOINT_SHORT: "WOLFRAM_APP_ID_SHORT",
    ENDPOINT_SPOKEN: "WOLFRAM_APP_ID_SPOKEN",
    ENDPOINT_SIMPLE: "WOLFRAM_APP_ID_SIMPLE",
    ENDPOINT_FULL: "WOLFRAM_APP_ID_FULL",
}

# Hard safety cap on query length to avoid abusive / accidental huge requests.
MAX_QUERY_CHARS = 2000

# The Simple/Short/Spoken/Full APIs accept a *server-side* compute budget via the
# `timeout` query param. Wolfram defaults it to 5s, which is too short for rich
# renders (maps, country borders, big data tables) — those reliably return
# HTTP 501 "could not give a response in time". We default the image (Simple)
# endpoint to a longer budget so visual results like "neighbors of Spain" work.
SIMPLE_DEFAULT_TIMEOUT = 15


# --------------------------------------------------------------------------- #
# Exceptions
# --------------------------------------------------------------------------- #
class WolframError(Exception):
    """Base class for all Wolfram client errors. ``str(err)`` is human/LLM-readable."""


class WolframConfigError(WolframError):
    """Missing/invalid configuration (e.g. no AppID set)."""


class WolframAuthError(WolframError):
    """AppID missing, invalid, or out of quota (HTTP 403 / API error 1 & 2)."""


class WolframInterpretError(WolframError):
    """Wolfram could not interpret the query (HTTP 501). May carry suggestions."""

    def __init__(self, message: str, *, query: str = "", suggestions: str = ""):
        super().__init__(message)
        self.query = query
        self.suggestions = suggestions


class WolframNetworkError(WolframError):
    """The request never completed (DNS / connection / timeout). Safe to retry."""


class WolframHTTPError(WolframError):
    """Any other unexpected HTTP status."""

    def __init__(self, message: str, *, status_code: int = 0, body: str = ""):
        super().__init__(message)
        self.status_code = status_code
        self.body = body


# --------------------------------------------------------------------------- #
# Result container for image responses
# --------------------------------------------------------------------------- #
@dataclass
class SimpleImage:
    """Binary image returned by the Simple API.

    Attributes
    ----------
    data : bytes
        Raw image bytes.
    image_format : str
        Short format name suitable for the MCP ``Image`` helper, e.g.
        ``"png"``, ``"gif"`` or ``"jpeg"``.
    mime_type : str
        Full MIME type from the response, e.g. ``"image/png"``.
    """

    data: bytes
    image_format: str
    mime_type: str

    def save(self, path: str) -> str:
        """Write the image to ``path`` and return the path."""
        with open(path, "wb") as fh:
            fh.write(self.data)
        return path


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #
def _clean_query(query: str) -> str:
    """Validate and lightly normalise a user/agent query string."""
    if query is None:
        raise WolframError("query must not be None.")
    q = str(query).strip()
    if not q:
        raise WolframError("query is empty. Provide a non-empty question or expression.")
    # Collapse newlines: the APIs expect a single-line input string.
    q = re.sub(r"\s+", " ", q)
    if len(q) > MAX_QUERY_CHARS:
        raise WolframError(
            f"query is too long ({len(q)} chars; max {MAX_QUERY_CHARS}). "
            "Split it into smaller sub-queries."
        )
    return q


def _drop_none(d: Mapping[str, Any]) -> dict[str, Any]:
    """Remove keys whose value is None so they are not sent as params."""
    return {k: v for k, v in d.items() if v is not None}


def _format_to_short(mime_type: str) -> str:
    """Map a MIME type like 'image/png' to a short format token like 'png'."""
    mt = (mime_type or "").lower().split(";")[0].strip()
    if "/" in mt:
        sub = mt.split("/", 1)[1]
        # Normalise a couple of common aliases.
        if sub in ("jpg",):
            return "jpeg"
        return sub or "png"
    return "png"


# --------------------------------------------------------------------------- #
# Optional, opt-in TTL response cache
# --------------------------------------------------------------------------- #
# Wolfram calls are read-only and idempotent, so identical queries can be reused.
# Disabled by default (WOLFRAM_CACHE_TTL unset / 0). Keep the TTL short if you
# enable it, so time-sensitive answers (prices, "today") don't go stale.
@dataclass
class _CachedResponse:
    """Minimal stand-in for httpx.Response covering what this module reads."""

    status_code: int
    content: bytes
    headers: dict[str, str]

    @property
    def text(self) -> str:
        return self.content.decode("utf-8", "replace")

    def json(self) -> Any:
        return _json.loads(self.text)


_CACHE: dict[tuple, tuple[float, _CachedResponse]] = {}
_CACHE_LOCK = threading.Lock()


def _cache_ttl() -> float:
    try:
        return float(os.environ.get("WOLFRAM_CACHE_TTL", "0"))
    except ValueError:
        return 0.0


def _cache_key(url: str, params: Mapping[str, Any]) -> tuple:
    # AppID is excluded so rotating keys doesn't fragment the cache.
    items = tuple(
        sorted((k, str(v)) for k, v in params.items() if k != "appid")
    )
    return (url, items)


def _cache_get(key: tuple, ttl: float) -> _CachedResponse | None:
    if ttl <= 0:
        return None
    with _CACHE_LOCK:
        hit = _CACHE.get(key)
        if hit and (_time.monotonic() - hit[0]) < ttl:
            return hit[1]
        if hit:
            _CACHE.pop(key, None)
    return None


def _cache_put(key: tuple, resp: httpx.Response) -> _CachedResponse:
    cached = _CachedResponse(
        status_code=resp.status_code,
        content=resp.content,
        headers=dict(resp.headers),
    )
    with _CACHE_LOCK:
        _CACHE[key] = (_time.monotonic(), cached)
    return cached


# --------------------------------------------------------------------------- #
# Client
# --------------------------------------------------------------------------- #
@dataclass
class WolframClient:
    """Client for the free Wolfram|Alpha REST APIs.

    Parameters
    ----------
    app_id : str, optional
        Default AppID. If omitted, read from the ``WOLFRAM_APP_ID`` env var.
    app_ids : Mapping[str, str], optional
        Optional per-endpoint AppID overrides, keyed by logical endpoint name
        (``"llm"``, ``"short"``, ``"spoken"``, ``"simple"``, ``"full"``).
        Per-endpoint env vars (``WOLFRAM_APP_ID_LLM`` etc.) also work and take
        precedence over this default when present. Use this only if you have
        generated several AppIDs and want to route different task types to
        different keys (e.g. to keep separate monthly quotas or usage tracking).
    timeout : float
        HTTP timeout in seconds (default 20). Wolfram's own ``timeout``/
        ``scantimeout`` query params control server-side compute time separately.
    user_agent : str
        Sent as the ``User-Agent`` header.

    Notes
    -----
    * The AppID is **never** logged and, for the LLM API, is sent as a Bearer
      token in the ``Authorization`` header (keeping it out of the URL/query
      string). The other endpoints require it as a query parameter per Wolfram's
      spec.
    * The same AppID works for every endpoint; they share one 2,000/month quota.
    """

    app_id: str | None = None
    app_ids: Mapping[str, str] = field(default_factory=dict)
    timeout: float = 30.0
    user_agent: str = "wolfram-mcp/1.0 (+https://github.com/)"
    _client: httpx.Client | None = field(default=None, init=False, repr=False)

    def __post_init__(self) -> None:
        if self.app_id is None:
            self.app_id = os.environ.get("WOLFRAM_APP_ID")

    # -- AppID resolution --------------------------------------------------- #
    def _appid_for(self, endpoint: str) -> str:
        """Resolve the AppID to use for a given endpoint, or raise."""
        # 1) explicit per-endpoint env override
        env_name = _ENV_OVERRIDES.get(endpoint)
        if env_name:
            val = os.environ.get(env_name)
            if val:
                return val
        # 2) per-endpoint override passed to the constructor
        if endpoint in self.app_ids and self.app_ids[endpoint]:
            return self.app_ids[endpoint]
        # 3) default
        if self.app_id:
            return self.app_id
        raise WolframConfigError(
            "No Wolfram AppID configured. Get a free one at "
            "https://developer.wolframalpha.com/ (2,000 non-commercial "
            "calls/month) and set the WOLFRAM_APP_ID environment variable."
        )

    # -- HTTP plumbing ------------------------------------------------------ #
    @property
    def http(self) -> httpx.Client:
        if self._client is None:
            self._client = httpx.Client(
                timeout=self.timeout,
                headers={"User-Agent": self.user_agent},
                follow_redirects=True,
            )
        return self._client

    def close(self) -> None:
        if self._client is not None:
            self._client.close()
            self._client = None

    def __enter__(self) -> "WolframClient":
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()

    def _get(
        self,
        url: str,
        params: Mapping[str, Any],
        *,
        endpoint: str,
        bearer: bool = False,
    ) -> "httpx.Response | _CachedResponse":
        """Perform a GET, attaching the AppID either as Bearer header or param.

        Raises typed ``WolframError`` subclasses; never leaks the AppID.
        """
        app_id = self._appid_for(endpoint)
        headers: dict[str, str] = {}
        send_params = dict(params)
        if bearer:
            headers["Authorization"] = f"Bearer {app_id}"
        else:
            send_params["appid"] = app_id

        ttl = _cache_ttl()
        key = _cache_key(url, send_params) if ttl > 0 else None
        if key is not None:
            cached = _cache_get(key, ttl)
            if cached is not None:
                return cached

        try:
            resp = self.http.get(url, params=send_params, headers=headers)
        except httpx.TimeoutException as e:
            raise WolframNetworkError(
                f"Wolfram request timed out after {self.timeout}s. "
                "The query was not run; you may retry."
            ) from e
        except httpx.RequestError as e:
            # Scrub anything that might echo the URL with the appid.
            raise WolframNetworkError(
                f"Could not reach Wolfram|Alpha ({type(e).__name__}). "
                "The query was not run; you may retry."
            ) from e

        # Only cache successful responses; never cache transient failures.
        if key is not None and resp.status_code == 200:
            return _cache_put(key, resp)
        return resp

    @staticmethod
    def _raise_for_common_status(resp: httpx.Response, query: str) -> None:
        """Translate Wolfram's documented error statuses into exceptions."""
        code = resp.status_code
        if code == 200:
            return
        body = (resp.text or "").strip()
        if code == 501:
            # 501 carries two very different meanings; the body disambiguates:
            #   * "could not give a response in time" -> SERVER-SIDE TIMEOUT.
            #     The query is fine; the compute budget was too small. This is
            #     the common failure for rich Simple-API renders (maps, big
            #     tables). Treat as a retryable network/timeout error, never as
            #     "rephrase your query".
            #   * "did not understand" / "No short answer" -> genuine interpret
            #     failure where rephrasing (or another endpoint) actually helps.
            msg = body
            try:
                msg = _json.loads(body).get("message", body) or body
            except Exception:
                pass
            low = msg.lower()
            if ("response in time" in low) or ("timed out" in low) or (
                "timeout" in low
            ):
                raise WolframNetworkError(
                    f"Wolfram timed out computing '{query}' server-side "
                    f"({msg[:160]}). The query is valid — retry, or raise the "
                    "'timeout' parameter; heavy renders (maps, large tables) "
                    "need a bigger budget."
                )
            if "no short answer" in low:
                raise WolframInterpretError(
                    f"No short answer is available for '{query}'. "
                    "Use wolfram_ask (LLM API) for a fuller answer.",
                    query=query,
                    suggestions=msg,
                )
            raise WolframInterpretError(
                f"Wolfram could not interpret the query '{query}'. "
                "Try rephrasing in simpler, more literal terms, split it into "
                "smaller sub-queries, or use standard math notation."
                + (f" Wolfram suggested: {msg[:400]}" if msg else ""),
                query=query,
                suggestions=msg,
            )
        if code == 400:
            raise WolframError(
                "Wolfram returned 400 (no input parameter found). This is an "
                "internal request-formatting error."
            )
        if code in (401, 403):
            raise WolframAuthError(
                "Wolfram rejected the request (auth). The AppID is missing, "
                "invalid, or has exhausted its quota (2,000/month free). "
                "Check WOLFRAM_APP_ID."
            )
        raise WolframHTTPError(
            f"Wolfram returned unexpected HTTP {code}: {body[:300]}",
            status_code=code,
            body=body,
        )

    # ------------------------------------------------------------------ #
    # Public API methods
    # ------------------------------------------------------------------ #
    def llm(
        self,
        query: str,
        *,
        maxchars: int = 6800,
        units: str | None = None,
        assumption: str | Iterable[str] | None = None,
        location: str | None = None,
        latlong: str | None = None,
        ip: str | None = None,
        timezone: str | None = None,
        currency: str | None = None,
        countrycode: str | None = None,
        languagecode: str | None = None,
        extra_params: Mapping[str, Any] | None = None,
    ) -> str:
        """LLM API — the main, detailed, LLM-ready answer.

        Returns plain text containing the interpretation, results and, where
        relevant, **image URLs** (maps, plots, tables) inline as
        ``image: https://...``. Best general-purpose verification/answer tool.

        ``assumption`` may be a single string or a list (for disambiguation:
        re-send the same query plus the assumption value Wolfram offered).
        """
        q = _clean_query(query)
        params: dict[str, Any] = _drop_none(
            {
                "input": q,
                "maxchars": maxchars,
                "units": units,
                "assumption": list(assumption)
                if isinstance(assumption, (list, tuple, set))
                else assumption,
                "location": location,
                "latlong": latlong,
                "ip": ip,
                "timezone": timezone,
                "currency": currency,
                "countrycode": countrycode,
                "languagecode": languagecode,
            }
        )
        if extra_params:
            params.update(_drop_none(extra_params))
        # LLM API supports Bearer auth -> keep AppID out of the query string.
        resp = self._get(LLM_API_URL, params, endpoint=ENDPOINT_LLM, bearer=True)
        self._raise_for_common_status(resp, q)
        return resp.text

    def short(
        self,
        query: str,
        *,
        units: str | None = None,
        timeout: int | None = None,
    ) -> str:
        """Short Answers API — a single concise line of plain text.

        Use for a quick scalar/fact check ("derivative of x^3" -> "3 x^2").
        Raises ``WolframInterpretError`` if no sufficiently short result exists.
        """
        q = _clean_query(query)
        params = _drop_none({"i": q, "units": units, "timeout": timeout})
        resp = self._get(SHORT_API_URL, params, endpoint=ENDPOINT_SHORT)
        self._raise_for_common_status(resp, q)
        return resp.text.strip()

    def spoken(
        self,
        query: str,
        *,
        units: str | None = None,
        timeout: int | None = None,
    ) -> str:
        """Spoken Results API — one natural-language sentence answer.

        Phrased for text-to-speech / conversational replies.
        """
        q = _clean_query(query)
        params = _drop_none({"i": q, "units": units, "timeout": timeout})
        resp = self._get(SPOKEN_API_URL, params, endpoint=ENDPOINT_SPOKEN)
        self._raise_for_common_status(resp, q)
        return resp.text.strip()

    def simple(
        self,
        query: str,
        *,
        layout: str | None = None,
        background: str | None = None,
        foreground: str | None = None,
        fontsize: int | None = None,
        width: int | None = None,
        units: str | None = None,
        timeout: int | None = SIMPLE_DEFAULT_TIMEOUT,
    ) -> SimpleImage:
        """Simple API — a single rendered IMAGE of the full result page.

        This is the way to actually *see* maps, plots, tables and formatted
        layouts (e.g. "neighbors of Spain" returns a map + bordering-country
        table as one image). Returns a :class:`SimpleImage` (bytes + format).

        ``layout`` is ``"divider"`` (default) or ``"labelbar"``. Colors accept
        HTML names, hex (``"F5F5F5"``), ``"r,g,b"`` or ``"transparent"``.
        """
        q = _clean_query(query)
        params = _drop_none(
            {
                "i": q,
                "layout": layout,
                "background": background,
                "foreground": foreground,
                "fontsize": fontsize,
                "width": width,
                "units": units,
                "timeout": timeout,
            }
        )
        resp = self._get(SIMPLE_API_URL, params, endpoint=ENDPOINT_SIMPLE)
        self._raise_for_common_status(resp, q)
        mime = resp.headers.get("content-type", "image/png")
        return SimpleImage(
            data=resp.content,
            image_format=_format_to_short(mime),
            mime_type=mime.split(";")[0].strip(),
        )

    def full(
        self,
        query: str,
        *,
        formats: str = "plaintext,image",
        units: str | None = None,
        assumption: str | Iterable[str] | None = None,
        podstate: str | Iterable[str] | None = None,
        includepodid: str | Iterable[str] | None = None,
        scanner: str | Iterable[str] | None = None,
        podtitle: str | Iterable[str] | None = None,
        location: str | None = None,
        latlong: str | None = None,
        extra_params: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Full Results API — structured JSON (the ``queryresult`` object).

        The most powerful endpoint: returns every result *pod* with both
        plaintext and image URLs, plus ``assumptions``, ``didyoumeans`` and
        warnings. Use it programmatically when you need structured data or to
        drive disambiguation. List-valued params (assumption, podstate, etc.)
        are sent as repeated query parameters.
        """
        q = _clean_query(query)

        def _listify(v: Any) -> Any:
            return list(v) if isinstance(v, (list, tuple, set)) else v

        params: dict[str, Any] = _drop_none(
            {
                "input": q,
                "format": formats,
                "output": "json",
                "units": units,
                "assumption": _listify(assumption),
                "podstate": _listify(podstate),
                "includepodid": _listify(includepodid),
                "scanner": _listify(scanner),
                "podtitle": _listify(podtitle),
                "location": location,
                "latlong": latlong,
            }
        )
        if extra_params:
            params.update(_drop_none(extra_params))
        resp = self._get(FULL_API_URL, params, endpoint=ENDPOINT_FULL)
        # Full Results returns 200 even for "did not understand"; the JSON's
        # success flag tells the real story. Still translate hard auth errors.
        if resp.status_code in (401, 403):
            self._raise_for_common_status(resp, q)
        try:
            data = resp.json()
        except ValueError as e:
            raise WolframHTTPError(
                f"Full Results API returned non-JSON (HTTP {resp.status_code}).",
                status_code=resp.status_code,
                body=(resp.text or "")[:300],
            ) from e
        return data.get("queryresult", data)

    # -- convenience -------------------------------------------------------- #
    @staticmethod
    def digest_full(queryresult: Mapping[str, Any], *, max_pods: int = 40) -> str:
        """Render a Full Results ``queryresult`` into a compact text digest.

        Includes pod titles + plaintext, any image URLs, assumptions and
        did-you-mean suggestions. Useful for feeding back to an LLM.
        """
        if not queryresult.get("success"):
            parts = ["Wolfram did not return a successful result."]
            dym = queryresult.get("didyoumeans")
            if dym:
                items = dym if isinstance(dym, list) else [dym]
                vals = [d.get("val", "") for d in items if isinstance(d, dict)]
                if vals:
                    parts.append("Did you mean: " + "; ".join(v for v in vals if v))
            err = queryresult.get("error")
            if isinstance(err, dict) and err.get("msg"):
                parts.append(f"Error: {err['msg']}")
            return "\n".join(parts)

        lines: list[str] = []
        for pod in (queryresult.get("pods") or [])[:max_pods]:
            title = pod.get("title", "").strip()
            chunks: list[str] = []
            for sub in pod.get("subpods", []) or []:
                txt = (sub.get("plaintext") or "").strip()
                if txt:
                    chunks.append(txt)
                img = sub.get("img") or {}
                src = img.get("src")
                if src and not txt:
                    chunks.append(f"image: {src}")
                elif src:
                    chunks.append(f"(image: {src})")
            body = " | ".join(chunks) if chunks else ""
            lines.append(f"{title}: {body}".rstrip(": ").rstrip())

        assumptions = queryresult.get("assumptions")
        if assumptions:
            a_items = (
                assumptions.get("assumption")
                if isinstance(assumptions, dict)
                else assumptions
            )
            if isinstance(a_items, dict):
                a_items = [a_items]
            for a in a_items or []:
                vals = [v.get("input", "") for v in a.get("values", [])]
                if vals:
                    lines.append(
                        f"Assumption ({a.get('type', '')}): "
                        + " / ".join(v for v in vals if v)
                    )
        return "\n".join(line for line in lines if line) or "(empty result)"

    @staticmethod
    def image_urls(queryresult: Mapping[str, Any]) -> list[tuple[str, str]]:
        """Extract ``(pod_title, image_src)`` pairs from a Full Results result.

        Used to recover visual output (maps, plots, tables) when the Simple API
        cannot render a single image in time — the Full Results API exposes the
        same renders as per-pod image URLs.
        """
        out: list[tuple[str, str]] = []
        if not queryresult.get("success"):
            return out
        for pod in queryresult.get("pods") or []:
            title = (pod.get("title") or "").strip()
            for sub in pod.get("subpods") or []:
                src = (sub.get("img") or {}).get("src")
                if src:
                    out.append((title, src))
        return out
