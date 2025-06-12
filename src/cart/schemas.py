from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime


class CartItemAdd(BaseModel):
    """Schemat dodawania produktu do koszyka"""
    product_id: int = Field(..., gt=0)
    quantity: int = Field(..., gt=0)


class CartItemUpdate(BaseModel):
    """Schemat aktualizacji ilości produktu w koszyku"""
    quantity: int = Field(..., gt=0)


class CartItemResponse(BaseModel):
    """Schemat odpowiedzi dla produktu w koszyku"""
    id: int
    product_id: int
    product_name: str
    product_price: float
    quantity: int
    total_price: float
    created_at: datetime

    class Config:
        from_attributes = True


class CartResponse(BaseModel):
    """Schemat odpowiedzi dla koszyka użytkownika"""
    items: List[CartItemResponse]
    total_items: int
    total_amount: float


class CartClear(BaseModel):
    """Schemat czyszczenia koszyka"""
    confirm: bool = Field(True) 