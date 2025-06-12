from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from enum import Enum


class OrderStatus(str, Enum):
    """Statusy zamówienia"""

    PENDING = "pending"
    CONFIRMED = "confirmed"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"


class OrderCreate(BaseModel):
    """Schemat tworzenia zamówienia"""

    shipping_address: str = Field(..., min_length=10, max_length=500)


class OrderItemResponse(BaseModel):
    """Schemat odpowiedzi dla pozycji zamówienia"""

    id: int
    product_id: int
    product_name: str
    quantity: int
    unit_price: float
    total_price: float

    class Config:
        from_attributes = True


class OrderResponse(BaseModel):
    """Schemat odpowiedzi dla zamówienia"""

    id: int
    user_id: int
    total_amount: float
    status: OrderStatus
    shipping_address: str
    created_at: datetime
    updated_at: datetime
    items: List[OrderItemResponse]

    class Config:
        from_attributes = True


class OrderUpdate(BaseModel):
    """Schemat aktualizacji zamówienia"""

    status: Optional[OrderStatus] = None
    shipping_address: Optional[str] = Field(None, min_length=10, max_length=500)


class OrderListResponse(BaseModel):
    """Schemat odpowiedzi dla listy zamówień"""

    id: int
    total_amount: float
    status: OrderStatus
    created_at: datetime
    items_count: int

    class Config:
        from_attributes = True
