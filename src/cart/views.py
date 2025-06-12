from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from src.database.models import get_db, CartItem, Product, User
from src.auth.dependencies import get_current_user
from .schemas import (
    CartItemAdd,
    CartItemUpdate,
    CartItemResponse,
    CartResponse,
    CartClear,
)

cart_router = APIRouter(prefix="/cart", tags=["cart"])


def get_cart_item_response(cart_item: CartItem) -> CartItemResponse:
    """Konwersja CartItem na CartItemResponse"""
    return CartItemResponse(
        id=cart_item.id,
        product_id=cart_item.product_id,
        product_name=cart_item.product.name,
        product_price=cart_item.product.price,
        quantity=cart_item.quantity,
        total_price=cart_item.product.price * cart_item.quantity,
        created_at=cart_item.created_at,
    )


@cart_router.get("/", response_model=CartResponse)
def get_cart(
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    """Pobieranie koszyka obecnego użytkownika"""
    cart_items = (
        db.query(CartItem)
        .filter(CartItem.user_id == current_user.id)
        .join(Product)
        .all()
    )

    items_response = [get_cart_item_response(item) for item in cart_items]
    total_items = sum(item.quantity for item in cart_items)
    total_amount = sum(item.product.price * item.quantity for item in cart_items)

    return CartResponse(
        items=items_response, total_items=total_items, total_amount=total_amount
    )


@cart_router.post("/add", response_model=CartItemResponse)
def add_to_cart(
    item_data: CartItemAdd,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Dodawanie produktu do koszyka"""
    # Sprawdzamy istnienie produktu
    product = (
        db.query(Product)
        .filter(Product.id == item_data.product_id, Product.is_active == True)
        .first()
    )

    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Produkt nie znaleziony lub nieaktywny",
        )

    # Sprawdzamy dostępność w magazynie
    if product.stock_quantity < item_data.quantity:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Niewystarczająca ilość produktu w magazynie. Dostępne: {product.stock_quantity}",
        )

    # Sprawdzamy, czy ten produkt jest już w koszyku
    existing_item = (
        db.query(CartItem)
        .filter(
            CartItem.user_id == current_user.id,
            CartItem.product_id == item_data.product_id,
        )
        .first()
    )

    if existing_item:
        # Aktualizujemy ilość
        new_quantity = existing_item.quantity + item_data.quantity

        if product.stock_quantity < new_quantity:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Niewystarczająca ilość produktu w magazynie. Dostępne: {product.stock_quantity}, w koszyku: {existing_item.quantity}",
            )

        existing_item.quantity = new_quantity
        db.commit()
        db.refresh(existing_item)

        return get_cart_item_response(existing_item)
    else:
        # Tworzymy nową pozycję w koszyku
        cart_item = CartItem(
            user_id=current_user.id,
            product_id=item_data.product_id,
            quantity=item_data.quantity,
        )

        db.add(cart_item)
        db.commit()
        db.refresh(cart_item)

        return get_cart_item_response(cart_item)


@cart_router.put("/items/{item_id}", response_model=CartItemResponse)
def update_cart_item(
    item_id: int,
    item_data: CartItemUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Aktualizacja ilości produktu w koszyku"""
    cart_item = (
        db.query(CartItem)
        .filter(CartItem.id == item_id, CartItem.user_id == current_user.id)
        .first()
    )

    if not cart_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Produkt nie znaleziony w koszyku",
        )

    # Sprawdzamy dostępność w magazynie
    if cart_item.product.stock_quantity < item_data.quantity:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Niewystarczająca ilość produktu w magazynie. Dostępne: {cart_item.product.stock_quantity}",
        )

    cart_item.quantity = item_data.quantity
    db.commit()
    db.refresh(cart_item)

    return get_cart_item_response(cart_item)


@cart_router.delete("/items/{item_id}")
def remove_from_cart(
    item_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Usuwanie produktu z koszyka"""
    cart_item = (
        db.query(CartItem)
        .filter(CartItem.id == item_id, CartItem.user_id == current_user.id)
        .first()
    )

    if not cart_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Produkt nie znaleziony w koszyku",
        )

    db.delete(cart_item)
    db.commit()

    return {"message": "Produkt usunięty z koszyka"}


@cart_router.delete("/clear")
def clear_cart(
    clear_data: CartClear,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Czyszczenie koszyka"""
    if not clear_data.confirm:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Wymagane potwierdzenie do wyczyszczenia koszyka",
        )

    deleted_count = (
        db.query(CartItem).filter(CartItem.user_id == current_user.id).delete()
    )

    db.commit()

    return {"message": f"Koszyk wyczyszczony. Usuniętych produktów: {deleted_count}"}
