from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class ProductResponse(BaseModel):
    """Schemat odpowiedzi dla produktu"""
    id: int
    name: str
    description: Optional[str]
    price: float
    stock_quantity: int
    category_id: int
    category_name: str
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class CategoryResponse(BaseModel):
    """Schemat odpowiedzi dla kategorii"""
    id: int
    name: str
    description: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


# Schematy administracyjne dla zarządzania produktami
class ProductCreate(BaseModel):
    """Schemat tworzenia produktu"""
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    price: float = Field(..., gt=0)
    stock_quantity: int = Field(..., ge=0)
    category_id: int = Field(..., gt=0)
    is_active: bool = Field(True)


class ProductUpdate(BaseModel):
    """Schemat aktualizacji produktu"""
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    price: Optional[float] = Field(None, gt=0)
    stock_quantity: Optional[int] = Field(None, ge=0)
    category_id: Optional[int] = Field(None, gt=0)
    is_active: Optional[bool] = None


class CategoryCreate(BaseModel):
    """Schemat tworzenia kategorii"""
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)


class CategoryUpdate(BaseModel):
    """Schemat aktualizacji kategorii"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500) 