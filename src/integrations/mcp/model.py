"""
Pydantic models for the MCP example e-commerce API.

These models define the data structures for product management,
including request payloads and API responses.
"""

from pydantic import BaseModel, Field


class Product(BaseModel):
    """
    Product data model for create/update operations.

    This model represents the core product information without the ID field,
    used for creating new products or updating existing ones.

    Attributes:
        name: Product name/title
        price: Product price in USD (must be positive)
        category: Product category (e.g., Electronics, Furniture)
        description: Optional detailed product description
    """

    name: str = Field(..., min_length=1, description="Product name")
    price: float = Field(..., gt=0, description="Product price in USD")
    category: str = Field(..., min_length=1, description="Product category")
    description: str | None = Field(None, description="Optional product description")


class ProductResponse(BaseModel):
    """
    Product response model including the database ID.

    This model extends the Product model with an ID field, used for
    API responses when returning product data from the database.

    Attributes:
        id: Unique product identifier (auto-generated)
        name: Product name/title
        price: Product price in USD
        category: Product category
        description: Optional detailed product description
    """

    id: int = Field(..., description="Unique product ID")
    name: str = Field(..., description="Product name")
    price: float = Field(..., description="Product price in USD")
    category: str = Field(..., description="Product category")
    description: str | None = Field(None, description="Optional product description")
