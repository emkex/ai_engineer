"""
Example 1 — Use Wolfram directly as a library (no MCP, no server).

This is the simplest path for "agents from code": just import the client.

Run:
    export WOLFRAM_APP_ID="your-appid"
    python examples/direct_client.py
"""

from wolfram_mcp import WolframClient, WolframError


def main() -> None:
    # Reads WOLFRAM_APP_ID from the environment. You can also pass app_id="...".
    with WolframClient() as wa:
        # 1) Quick single-value check.
        print("short:", wa.short("derivative of x^3"))  # -> 3 x^2

        # 2) Detailed, LLM-ready answer (includes image URLs inline).
        print("\nask:\n", wa.llm("integrate x^2 sin(x) dx", maxchars=800))

        # 3) A natural sentence (good for voice).
        print("\nspoken:", wa.spoken("distance from Earth to the Moon"))

        # 4) A rendered IMAGE (map + table for 'neighbors of Spain'); save to disk.
        img = wa.simple("neighbors of Spain", width=700, timeout=20)
        path = img.save("neighbors_of_spain." + img.image_format)
        print(f"\nvisual: saved {len(img.data)} bytes -> {path} ({img.mime_type})")

        # 5) Structured data for programmatic use / disambiguation.
        qr = wa.full("GDP of Germany 2023")
        print("\nfull (digest):\n", WolframClient.digest_full(qr))

        # Branch on typed errors:
        try:
            wa.short("qwertyuiop asdfgh")  # nonsense -> no short answer
        except WolframError as e:
            print("\nhandled error:", e)
        
        # 6) self-made:
        img = wa.simple("distance from Earth to the Moon", width=700, timeout=20)
        path = img.save("distance_earth_moon." + img.image_format)
        print(f"\nvisual: saved {len(img.data)} bytes -> {path} ({img.mime_type})")


if __name__ == "__main__":
    main()
