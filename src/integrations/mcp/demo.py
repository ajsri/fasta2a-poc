"""
MCP Client Demo.

This module demonstrates how to interact with the MCP-enabled e-commerce API
using the FastMCP client. It shows how LLMs and other clients can discover
and use the exposed tools.

Usage:
    Run the demo:
        uv run python -m src.integrations.mcp.demo

    Note: Make sure the API server is NOT running before executing this demo,
    as the client connects to the MCP instance directly (not via HTTP).
"""

import asyncio

from fastmcp import Client

from src.integrations.mcp.api import mcp


async def demo() -> None:
    """
    Demonstrate MCP tool interactions.

    This function shows how to:
    1. Discover available tools from the MCP server
    2. Call auto-generated tools from API endpoints
    3. Call custom tools defined with @mcp.tool decorator

    The demo performs the following operations:
    - Lists all available MCP tools
    - Creates a new product using the auto-generated tool
    - Lists products with filtering
    - Fetches a product using a custom tool
    - Tests the debug tool
    """
    # Connect to the MCP server using a context manager
    # This ensures proper cleanup of resources
    async with Client(mcp) as client:
        # ====================================================================
        # Step 1: Discover available tools
        # ====================================================================
        tools = await client.list_tools()
        print(f"Available tools: {[t.name for t in tools]}")
        print()

        # ====================================================================
        # Step 2: Create a product using auto-generated API tool
        # ====================================================================
        # Tool name format: {function_name}_{endpoint_path}_{method}
        result = await client.call_tool(
            "create_product_products_post",
            {
                "name": "Wireless Keyboard",
                "price": 79.99,
                "category": "Electronics",
                "description": "Bluetooth mechanical keyboard",
            },
        )
        print(f"Created product: {result.data}")
        print()

        # ====================================================================
        # Step 3: List products with filters using auto-generated tool
        # ====================================================================
        result = await client.call_tool(
            "list_products_products_get",
            {"category": "Electronics", "max_price": 100},
        )
        print(f"Affordable electronics: {result.data}")
        print()

        # ====================================================================
        # Step 4: Get a product by ID using custom MCP tool
        # ====================================================================
        # This uses the custom tool defined with @mcp.tool decorator
        result = await client.call_tool("get_product_by_id", {"product_id": 2})
        print(f"Fetched single product by custom tool: {result.data}")
        print()

        # ====================================================================
        # Step 5: Test the debug tool (another custom tool)
        # ====================================================================
        result = await client.call_tool("debug_tool", {"message": "Hello world!"})
        print(f"Debug tool response: {result.data}")


if __name__ == "__main__":
    # Run the async demo function
    # This demonstrates how to use MCP tools programmatically
    asyncio.run(demo())
