"""
wolfram-mcp
===========

A free, self-hosted MCP server + plain Python client for the Wolfram|Alpha
REST APIs (2,000 non-commercial calls/month per AppID).

Two ways to use it:

1. As an MCP server (Claude Code / Desktop / Cursor / remote agents)::

       python -m wolfram_mcp.server

2. As a normal library, from your own code::

       from wolfram_mcp import WolframClient
       wa = WolframClient()                       # reads WOLFRAM_APP_ID
       print(wa.short("derivative of x^3"))       # -> "3 x^2"
"""

from __future__ import annotations

from .core import (
    SimpleImage,
    WolframAuthError,
    WolframClient,
    WolframConfigError,
    WolframError,
    WolframHTTPError,
    WolframInterpretError,
    WolframNetworkError,
)

__version__ = "1.0.0"

__all__ = [
    "WolframClient",
    "SimpleImage",
    "WolframError",
    "WolframAuthError",
    "WolframInterpretError",
    "WolframNetworkError",
    "WolframHTTPError",
    "WolframConfigError",
    "__version__",
]
