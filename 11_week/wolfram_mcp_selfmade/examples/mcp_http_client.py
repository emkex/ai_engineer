"""
Example 3 — Connect to the server over Streamable HTTP from code.

Use this when the server runs as a (local or remote) network service that
several agents/processes share.

First, start the server in one terminal:
    export WOLFRAM_APP_ID="your-appid"
    python -m wolfram_mcp.server --transport streamable-http --host 127.0.0.1 --port 8000

Then run this client in another terminal:
    python examples/mcp_http_client.py

The MCP endpoint path is "/mcp".
"""

import asyncio

from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client

URL = "http://127.0.0.1:8000/mcp"


async def main() -> None:
    async with streamablehttp_client(URL) as (read, write, _):
        async with ClientSession(read, write) as session:
            await session.initialize()

            tools = await session.list_tools()
            print("Tools:", [t.name for t in tools.tools])

            res = await session.call_tool(
                "wolfram_full_results",
                {"query": "population of France", "include_pod_ids": "Result"},
            )
            for block in res.content:
                if getattr(block, "type", None) == "text":
                    print("\nfull (digest):\n", block.text)


if __name__ == "__main__":
    asyncio.run(main())
