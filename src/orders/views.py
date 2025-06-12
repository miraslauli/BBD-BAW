from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from src.database.models import get_db, Order, OrderItem, CartItem, Product, User
from src.auth.dependencies import get_current_user, get_current_admin_user
from .schemas import (
    OrderCreate,
    OrderResponse,
    OrderUpdate,
    OrderListResponse,
    OrderItemResponse,
    OrderStatus,
)

orders_router = APIRouter(prefix="/orders", tags=["orders"])


def get_order_item_response(order_item: OrderItem) -> OrderItemResponse:
    """Konwersja OrderItem na OrderItemResponse"""
    return OrderItemResponse(
        id=order_item.id,
        product_id=order_item.product_id,
        product_name=order_item.product.name,
        quantity=order_item.quantity,
        unit_price=order_item.unit_price,
        total_price=order_item.total_price,
    )


def get_order_response(order: Order) -> OrderResponse:
    """Konwersja Order na OrderResponse"""
    items_response = [get_order_item_response(item) for item in order.order_items]

    return OrderResponse(
        id=order.id,
        user_id=order.user_id,
        total_amount=order.total_amount,
        status=OrderStatus(order.status),
        shipping_address=order.shipping_address,
        created_at=order.created_at,
        updated_at=order.updated_at,
        items=items_response,
    )


@orders_router.post("/create", response_model=OrderResponse)
def create_order(
    order_data: OrderCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Tworzenie zamówienia z koszyka"""
    # Pobieramy produkty z koszyka
    cart_items = (
        db.query(CartItem)
        .filter(CartItem.user_id == current_user.id)
        .join(Product)
        .all()
    )

    if not cart_items:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Koszyk jest pusty"
        )

    # Sprawdzamy dostępność produktów w magazynie
    for cart_item in cart_items:
        if not cart_item.product.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Produkt '{cart_item.product.name}' nie jest już dostępny",
            )

        if cart_item.product.stock_quantity < cart_item.quantity:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Niewystarczająca ilość produktu '{cart_item.product.name}' w magazynie. Dostępne: {cart_item.product.stock_quantity}",
            )

    # Obliczamy łączną kwotę zamówienia
    total_amount = sum(
        cart_item.product.price * cart_item.quantity for cart_item in cart_items
    )

    # Tworzymy zamówienie
    order = Order(
        user_id=current_user.id,
        total_amount=total_amount,
        status=OrderStatus.PENDING.value,
        shipping_address=order_data.shipping_address,
    )

    db.add(order)
    db.flush()  # Otrzymujemy ID zamówienia

    # Tworzymy pozycje zamówienia i aktualizujemy stan magazynowy
    for cart_item in cart_items:
        order_item = OrderItem(
            order_id=order.id,
            product_id=cart_item.product_id,
            quantity=cart_item.quantity,
            unit_price=cart_item.product.price,
            total_price=cart_item.product.price * cart_item.quantity,
        )
        db.add(order_item)

        # Zmniejszamy ilość produktu w magazynie
        cart_item.product.stock_quantity -= cart_item.quantity

    # Czyścimy koszyk
    db.query(CartItem).filter(CartItem.user_id == current_user.id).delete()

    db.commit()
    db.refresh(order)

    return get_order_response(order)


@orders_router.get("/", response_model=List[OrderListResponse])
def get_my_orders(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
):
    """Pobieranie zamówień obecnego użytkownika"""
    orders = (
        db.query(Order)
        .filter(Order.user_id == current_user.id)
        .order_by(Order.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )

    return [
        OrderListResponse(
            id=order.id,
            total_amount=order.total_amount,
            status=OrderStatus(order.status),
            created_at=order.created_at,
            items_count=len(order.order_items),
        )
        for order in orders
    ]


@orders_router.get("/{order_id}", response_model=OrderResponse)
def get_order(
    order_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Pobieranie szczegółów zamówienia"""
    order = (
        db.query(Order)
        .filter(Order.id == order_id, Order.user_id == current_user.id)
        .first()
    )

    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Zamówienie nie znalezione"
        )

    return get_order_response(order)


@orders_router.put("/{order_id}/cancel")
def cancel_order(
    order_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Anulowanie zamówienia przez użytkownika"""
    order = (
        db.query(Order)
        .filter(Order.id == order_id, Order.user_id == current_user.id)
        .first()
    )

    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Zamówienie nie znalezione"
        )

    if order.status not in [OrderStatus.PENDING.value, OrderStatus.CONFIRMED.value]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Zamówienie nie może być anulowane w obecnym statusie",
        )

    # Przywracamy produkty do magazynu
    for order_item in order.order_items:
        order_item.product.stock_quantity += order_item.quantity

    order.status = OrderStatus.CANCELLED.value
    order.updated_at = datetime.utcnow()

    db.commit()

    return {"message": "Zamówienie zostało anulowane"}


# Endpointy administracyjne
@orders_router.get("/admin/all", response_model=List[OrderListResponse])
def get_all_orders_admin(
    current_admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db),
    status_filter: Optional[OrderStatus] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
):
    """Pobieranie wszystkich zamówień (dla administratora)"""
    query = db.query(Order)

    if status_filter:
        query = query.filter(Order.status == status_filter.value)

    orders = query.order_by(Order.created_at.desc()).offset(skip).limit(limit).all()

    return [
        OrderListResponse(
            id=order.id,
            total_amount=order.total_amount,
            status=OrderStatus(order.status),
            created_at=order.created_at,
            items_count=len(order.order_items),
        )
        for order in orders
    ]


@orders_router.put("/admin/{order_id}", response_model=OrderResponse)
def update_order_admin(
    order_id: int,
    order_data: OrderUpdate,
    current_admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db),
):
    """Aktualizacja zamówienia (dla administratora)"""
    order = db.query(Order).filter(Order.id == order_id).first()

    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Zamówienie nie znalezione"
        )

    if order_data.status:
        order.status = order_data.status.value

    if order_data.shipping_address:
        order.shipping_address = order_data.shipping_address

    order.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(order)

    return get_order_response(order)
