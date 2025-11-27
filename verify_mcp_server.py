import asyncio
import os
import sys
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def run():
    # Determine python executable
    python_exe = sys.executable
    script_path = os.path.join("src", "memory_mcp", "main.py")
    
    print(f"Connecting to server: {python_exe} {script_path}")
    
    server_params = StdioServerParameters(
        command=python_exe,
        args=[script_path],
        env=os.environ.copy()
    )
    
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            
            # List tools
            print("\n--- Listing Tools ---")
            tools = await session.list_tools()
            for t in tools.tools:
                print(f"- {t.name}: {t.description}")
            
            # Test write_memory
            print("\n--- Testing write_memory ---")
            result = await session.call_tool("write_memory", arguments={
                "memory_name": "protocol-test",
                "content_markdown": "This memory was created via MCP protocol test script.",
                "tags": ["test", "mcp-protocol"]
            })
            print(f"Result: {result.content[0].text}")
            
            # Test read_memory
            print("\n--- Testing read_memory ---")
            result = await session.call_tool("read_memory", arguments={
                "memory_name": "protocol-test"
            })
            print(f"Result: {result.content[0].text}")
            
            # Test search_memories
            print("\n--- Testing search_memories ---")
            result = await session.call_tool("search_memories", arguments={
                "query": "protocol"
            })
            print(f"Result: {result.content[0].text}")

            # Test delete_memory
            print("\n--- Testing delete_memory ---")
            result = await session.call_tool("delete_memory", arguments={
                "memory_name": "protocol-test"
            })
            print(f"Result: {result.content[0].text}")

if __name__ == "__main__":
    asyncio.run(run())
