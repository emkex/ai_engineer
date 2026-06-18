"""
Example 2 — Drive the MCP server over stdio from your own code.

Use this when you want to exercise the *exact same tools* an agent sees
(same names, schemas, behavior), spawning the server as a subprocess.

Run:
    export WOLFRAM_APP_ID="your-appid"
    python examples/mcp_stdio_client.py
"""

import asyncio
import os

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


async def main() -> None:
    server = StdioServerParameters(
        command="python",
        args=["-m", "wolfram_mcp.server"],
        # Pass the AppID through to the child process.
        env={"WOLFRAM_APP_ID": os.environ["WOLFRAM_APP_ID"]},
    )

    async with stdio_client(server) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            tools = await session.list_tools()
            print("Tools:", [t.name for t in tools.tools])

            # Call a tool exactly as an agent would.
            res = await session.call_tool(
                "wolfram_short_answer", {"query": "speed of light"}
            )
            for block in res.content:
                if getattr(block, "type", None) == "text":
                    print("short:", block.text)

            res = await session.call_tool(
                "wolfram_ask",
                {"query": "solve x^2 - 5x + 6 = 0", "maxchars": 600},
            )
            for block in res.content:
                if getattr(block, "type", None) == "text":
                    print("\nask:\n", block.text)

            # wolfram_visual returns an image content block.
            res = await session.call_tool(
                "wolfram_visual", {"query": "neighbors of Spain"}
            )
            for block in res.content:
                if getattr(block, "type", None) == "image":
                    print(f"\nimage: {len(block.data)} base64 chars, {block.mimeType}")


if __name__ == "__main__":
    asyncio.run(main())
