"""
MCP-enabled E-commerce API Example.

This module demonstrates how to integrate FastMCP with FastAPI to expose
RESTful API endpoints as tools that LLMs can discover and use. The example
implements a simple product management system with CRUD operations.

Based on the FastMCP integration guide: https://gofastmcp.com/integrations/fastapi

Key Features:
    - Standard FastAPI REST endpoints for products
    - Automatic MCP tool generation from API routes
    - Custom MCP tools defined with @mcp.tool decorator
    - Combined server serving both REST and MCP protocols

Usage:
    Run the server:
        uv run python -m src.integrations.mcp.api

    Access endpoints:
        - REST API: http://localhost:8000/products
        - MCP Protocol: http://localhost:8000/mcp
        - API Docs: http://localhost:8000/docs
"""

import uvicorn
from fastapi import FastAPI, HTTPException
from fastmcp import FastMCP

from src.integrations.mcp.model import Product, ProductResponse

# Create the main FastAPI application
app = FastAPI(
    title="E-commerce API",
    version="1.0.0",
    description="Example e-commerce API with MCP integration for LLM interaction",
)

# In-memory product database for demonstration purposes
# In production, this would be replaced with a real database (PostgreSQL, MongoDB, etc.)
products_db: dict[int, ProductResponse] = {
    1: ProductResponse(id=1, name="Laptop", price=999.99, category="Electronics"),
    2: ProductResponse(id=2, name="Mouse", price=29.99, category="Electronics"),
    3: ProductResponse(id=3, name="Desk Chair", price=299.99, category="Furniture"),
}

# Auto-incrementing ID counter for new products
next_id = 4


@app.get("/products", response_model=list[ProductResponse])
def list_products(
    category: str | None = None,
    max_price: float | None = None,
) -> list[ProductResponse]:
    """
    List all products with optional filtering.

    Args:
        category: Optional filter to return only products in this category
        max_price: Optional filter to return only products at or below this price

    Returns:
        List of products matching the filter criteria

    Example:
        GET /products?category=Electronics&max_price=100
    """
    products = list(products_db.values())

    # Apply category filter if provided
    if category:
        products = [p for p in products if p.category == category]

    # Apply price filter if provided
    if max_price:
        products = [p for p in products if p.price <= max_price]

    return products


@app.get("/products/{product_id}", response_model=ProductResponse)
def get_product(product_id: int) -> ProductResponse:
    """
    Get a specific product by ID.

    Args:
        product_id: The unique identifier of the product

    Returns:
        The product with the specified ID

    Raises:
        HTTPException: 404 if product not found

    Example:
        GET /products/1
    """
    if product_id not in products_db:
        raise HTTPException(status_code=404, detail="Product not found")
    return products_db[product_id]


@app.post("/products", response_model=ProductResponse)
def create_product(product: Product) -> ProductResponse:
    """
    Create a new product.

    Args:
        product: Product data (name, price, category, description)

    Returns:
        The newly created product with auto-generated ID

    Example:
        POST /products
        {
            "name": "Keyboard",
            "price": 79.99,
            "category": "Electronics",
            "description": "Mechanical keyboard"
        }
    """
    global next_id
    product_response = ProductResponse(id=next_id, **product.model_dump())
    products_db[next_id] = product_response
    next_id += 1
    return product_response


@app.put("/products/{product_id}", response_model=ProductResponse)
def update_product(product_id: int, product: Product) -> ProductResponse:
    """
    Update an existing product.

    Args:
        product_id: The unique identifier of the product to update
        product: New product data to replace existing data

    Returns:
        The updated product

    Raises:
        HTTPException: 404 if product not found

    Example:
        PUT /products/1
        {
            "name": "Updated Laptop",
            "price": 899.99,
            "category": "Electronics"
        }
    """
    if product_id not in products_db:
        raise HTTPException(status_code=404, detail="Product not found")
    products_db[product_id] = ProductResponse(
        id=product_id,
        **product.model_dump(),
    )
    return products_db[product_id]


@app.delete("/products/{product_id}")
def delete_product(product_id: int) -> dict[str, str]:
    """
    Delete a product.

    Args:
        product_id: The unique identifier of the product to delete

    Returns:
        Success message

    Raises:
        HTTPException: 404 if product not found

    Example:
        DELETE /products/1
    """
    if product_id not in products_db:
        raise HTTPException(status_code=404, detail="Product not found")
    del products_db[product_id]
    return {"message": "Product deleted"}


# ============================================================================
# MCP (Model Context Protocol) Integration
# ============================================================================
# This section demonstrates how to expose FastAPI endpoints as LLM-accessible
# tools using FastMCP. The MCP allows AI agents to discover and interact with
# your API in a structured, tool-based manner.

# Generate MCP server from the FastAPI app
# This automatically creates MCP tools from all the API endpoints defined above
mcp = FastMCP.from_fastapi(app=app, name="E-commerce MCP")

# Create the MCP HTTP application with a custom path prefix
# The MCP protocol will be accessible at /mcp/*
mcp_app = mcp.http_app(path="/mcp")

# Create a combined FastAPI application that serves both:
# 1. Regular REST API routes (for traditional HTTP clients)
# 2. MCP protocol routes (for LLM tool access)
combined_app = FastAPI(
    title="E-commerce API with MCP",
    routes=[
        *mcp_app.routes,  # MCP protocol routes at /mcp
        *app.routes,  # Original API routes at /products
    ],
    lifespan=mcp_app.lifespan,  # Use MCP's lifespan manager
)


# ============================================================================
# Custom MCP Tools
# ============================================================================
# In addition to automatically generated tools from API routes, you can
# define custom tools using the @mcp.tool decorator. These tools can
# implement additional logic or provide convenience methods for LLMs.


@mcp.tool
def get_product_by_id(product_id: int) -> ProductResponse:
    """
    Get a product by ID (custom MCP tool).

    This is a convenience tool that provides direct access to a product
    by ID without needing to construct the full API path. LLMs can use
    this tool more easily than calling the REST endpoint.

    Args:
        product_id: The unique identifier of the product

    Returns:
        The product with the specified ID
    """
    return products_db[product_id]


@mcp.tool
def debug_tool(message: str) -> str:
    """
    Echo a debug message (example tool).

    This is a simple example tool that demonstrates how to create
    custom MCP tools. In a real application, you might create tools
    for complex operations, aggregations, or business logic.

    Args:
        message: The message to echo back

    Returns:
        The echoed message with a debug prefix
    """
    return f"Debug: {message}"


# ============================================================================
# Server Endpoints Summary
# ============================================================================
# The combined application now serves:
# - Regular REST API: http://localhost:8000/products (GET, POST, PUT, DELETE)
# - MCP Protocol: http://localhost:8000/mcp (LLM tool access)
# - API Documentation: http://localhost:8000/docs (Swagger UI)
# - Alternative Docs: http://localhost:8000/redoc (ReDoc UI)

if __name__ == "__main__":
    # Start the combined server with both REST API and MCP protocol
    # Run with: uv run python -m src.integrations.mcp.api
    uvicorn.run(combined_app, host="0.0.0.0", port=8000)
