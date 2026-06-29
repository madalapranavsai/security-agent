import asyncio
import os

from mcp.connect import MCPToolLoader


async def main():
    project_dir = os.path.dirname(os.path.abspath(__file__))

    loader = MCPToolLoader(
        command="python3",
        args=[
            os.path.join(project_dir, "hexstrike-ai", "hexstrike_mcp.py"),
            "--server",
            "http://localhost:8888",
        ],
        max_tools=100,
        server_name="hexstrike",
    )

    try:
        client, tools = await loader.connect()

        print("\n" + "=" * 60)
        print("✅ MCP CONNECTED SUCCESSFULLY")
        print("=" * 60)
        print(f"Total tools loaded: {len(tools)}\n")

        for i, tool in enumerate(tools, 1):
            print(f"{i}. {tool.name}")
            if getattr(tool, "description", None):
                print(f"   {tool.description}")

    except Exception as e:
        print("\n❌ Failed to connect to MCP server")
        print(type(e).__name__)
        print(e)

    finally:
        try:
            await loader.aclose()
        except Exception:
            pass


if __name__ == "__main__":
    asyncio.run(main())